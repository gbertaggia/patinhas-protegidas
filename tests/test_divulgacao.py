"""
Testes do formulário do animal: divulgação na página pública e informações de saúde.

Cada teste usa a pessoa de teste (e-mail iniciado em pytest_) criada pelas fixtures
do conftest.py, que apagam a pessoa e os animais dela no fim.
"""
import re
import uuid

import pytest

from database.connection import conectar_banco


# ---------- ajudas ----------

def _consultar(sql, parametros=()):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    finally:
        conexao.close()


def _executar(sql, parametros=()):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)
        conexao.commit()
    finally:
        conexao.close()


def _definir_localizacao(id_usuario, cidade='Campinas', uf='SP'):
    _executar("UPDATE usuarios SET cidade = %s, uf = %s WHERE id = %s", (cidade, uf, id_usuario))


def _animais_do_usuario(id_usuario):
    return _consultar(
        "SELECT id, nome, visivel_publico, info_saude FROM animais WHERE usuario_id = %s",
        (id_usuario,),
    )


def _estado_do_animal(id_animal):
    return _consultar(
        "SELECT visivel_publico, info_saude FROM animais WHERE id = %s", (id_animal,)
    )[0]


def _tag_divulgar(html):
    """Devolve a tag <input> da opção de divulgar, para conferir se está habilitada ou marcada."""
    achado = re.search(r'<input[^>]*name="divulgar"[^>]*>', html)
    assert achado, 'a opção de divulgar não está na página'
    return achado.group(0)


def _dados_do_novo_animal(**extras):
    dados = {'nome': 'Pet de teste', 'especie': 'Gato', 'idade': '2 anos', 'castrado': '1'}
    dados.update(extras)
    return dados


# ---------- telas ----------

def test_tela_de_cadastro_libera_a_divulgacao_com_cidade_e_estado(client_logado, usuario):
    _definir_localizacao(usuario)

    resposta = client_logado.get('/cadastro_animal')

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'disabled' not in _tag_divulgar(html)
    assert 'name="info_saude"' in html


def test_tela_de_cadastro_bloqueia_a_divulgacao_sem_cidade_e_estado(client_logado):
    resposta = client_logado.get('/cadastro_animal')

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'disabled' in _tag_divulgar(html)
    assert '/editar_usuario' in html


def test_tela_de_edicao_mostra_o_que_esta_salvo(client_logado, usuario, animal):
    _definir_localizacao(usuario)
    _executar(
        "UPDATE animais SET visivel_publico = 1, info_saude = %s WHERE id = %s",
        ('vermifugado e castrado', animal),
    )

    resposta = client_logado.get(f'/editar_animal/{animal}')

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'vermifugado e castrado' in html
    tag = _tag_divulgar(html)
    assert 'checked' in tag
    assert 'disabled' not in tag


# ---------- cadastro de animal ----------

def test_cadastrar_animal_com_divulgacao(client_logado, usuario):
    _definir_localizacao(usuario)

    resposta = client_logado.post('/cadastrar_animal', data=_dados_do_novo_animal(
        divulgar='1', info_saude='  vermifugado, FIV/FELV negativo  '))

    assert resposta.status_code == 302
    (animal,) = _animais_do_usuario(usuario)
    assert animal['visivel_publico'] == 1
    assert animal['info_saude'] == 'vermifugado, FIV/FELV negativo'


def test_cadastrar_animal_sem_marcar_nao_divulga(client_logado, usuario):
    _definir_localizacao(usuario)

    resposta = client_logado.post('/cadastrar_animal', data=_dados_do_novo_animal())

    assert resposta.status_code == 302
    (animal,) = _animais_do_usuario(usuario)
    assert animal['visivel_publico'] == 0
    assert animal['info_saude'] is None


def test_divulgar_sem_cidade_e_estado_e_recusado(client_logado, usuario):
    resposta = client_logado.post('/cadastrar_animal', data=_dados_do_novo_animal(divulgar='1'))

    assert resposta.status_code == 400
    assert '/editar_usuario' in resposta.get_data(as_text=True)
    assert len(_animais_do_usuario(usuario)) == 0


def test_cadastrar_sem_divulgar_funciona_mesmo_sem_cidade_e_estado(client_logado, usuario):
    resposta = client_logado.post('/cadastrar_animal', data=_dados_do_novo_animal())

    assert resposta.status_code == 302
    assert len(_animais_do_usuario(usuario)) == 1


@pytest.mark.parametrize('tamanho, esperado', [(500, 302), (501, 400)])
def test_limite_do_texto_de_saude(client_logado, usuario, tamanho, esperado):
    _definir_localizacao(usuario)

    resposta = client_logado.post('/cadastrar_animal', data=_dados_do_novo_animal(
        info_saude='a' * tamanho))

    assert resposta.status_code == esperado
    assert len(_animais_do_usuario(usuario)) == (1 if esperado == 302 else 0)


# ---------- edição de animal ----------

def _dados_da_edicao(**extras):
    dados = {'nome': 'Animal de teste', 'especie': 'gato', 'raca': 'SRD', 'idade': '3 anos'}
    dados.update(extras)
    return dados


def test_editar_animal_liga_e_desliga_a_divulgacao(client_logado, usuario, animal):
    _definir_localizacao(usuario)

    resposta = client_logado.post(f'/salvar_edicao/{animal}', data=_dados_da_edicao(
        divulgar='1', info_saude='vermifugado'))
    assert resposta.status_code == 302
    estado = _estado_do_animal(animal)
    assert estado['visivel_publico'] == 1
    assert estado['info_saude'] == 'vermifugado'

    # Salvar sem marcar a opção tira o animal da página pública
    resposta = client_logado.post(f'/salvar_edicao/{animal}', data=_dados_da_edicao(
        info_saude='vermifugado'))
    assert resposta.status_code == 302
    assert _estado_do_animal(animal)['visivel_publico'] == 0


def test_editar_para_divulgar_sem_cidade_e_estado_e_recusado(client_logado, animal):
    resposta = client_logado.post(f'/salvar_edicao/{animal}', data=_dados_da_edicao(divulgar='1'))

    assert resposta.status_code == 400
    assert _estado_do_animal(animal)['visivel_publico'] == 0


def test_nao_divulga_animal_de_outra_conta(outro_client, outro_usuario, usuario, animal):
    # A outra pessoa tem cidade e estado, mas o animal não é dela
    _definir_localizacao(outro_usuario)

    outro_client.post(f'/salvar_edicao/{animal}', data=_dados_da_edicao(
        divulgar='1', info_saude='texto de outra pessoa'))

    estado = _estado_do_animal(animal)
    assert estado['visivel_publico'] == 0
    assert estado['info_saude'] is None


# ---------- de ponta a ponta ----------

def test_animal_divulgado_pelo_formulario_aparece_na_api_publica(client_logado, client, usuario):
    _definir_localizacao(usuario, cidade='Campinas', uf='SP')
    nome = f'Pet {uuid.uuid4().hex[:10]}'
    chip = str(uuid.uuid4().int)[:15]

    client_logado.post('/cadastrar_animal', data=_dados_do_novo_animal(
        nome=nome, chip=chip, divulgar='1', info_saude='vermifugado'))

    resposta = client.get('/api/publico/dados')  # sem login

    assert resposta.status_code == 200
    animais = [a for cartao in resposta.get_json()['ongs'] for a in cartao['animais']]
    meu = next((a for a in animais if a['nome'] == nome), None)
    assert meu is not None, 'o animal divulgado não apareceu na API pública'
    assert meu['infoSaude'] == 'vermifugado'
    assert meu['cidade'] == 'Campinas'
    assert meu['estado'] == 'SP'
    assert meu['temChip'] is True
    assert chip not in resposta.get_data(as_text=True)

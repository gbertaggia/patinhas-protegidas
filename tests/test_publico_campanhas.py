"""
Testes da API pública: campanhas, formulário de adoção dos cartões e aviso de doação.

Cada teste usa a pessoa de teste (e-mail iniciado em pytest_) criada pelas fixtures
do conftest.py. As campanhas criadas aqui são apagadas antes da pessoa, porque a
chave estrangeira de campanhas é RESTRICT.
"""
import uuid
from decimal import Decimal

import pytest

from database.connection import conectar_banco
from routes.publico import LIMITE_PENDENTES_POR_CAMPANHA, LINK_FORMULARIO


CAMPOS_DA_CAMPANHA = {
    'id', 'titulo', 'descricao', 'meta', 'arrecadado', 'foto',
    'animalId', 'chavePix', 'recebedor', 'cidade',
}


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


def _configurar_conta(id_usuario, tipo, nome, **extras):
    campos = {'tipo': tipo, 'nome': nome, 'cidade': 'Campinas', 'uf': 'SP', **extras}
    atribuicoes = ', '.join(f'{coluna} = %s' for coluna in campos)
    _executar(
        f"UPDATE usuarios SET {atribuicoes} WHERE id = %s",
        (*campos.values(), id_usuario),
    )


def _divulgar(id_animal):
    _executar("UPDATE animais SET visivel_publico = 1 WHERE id = %s", (id_animal,))


def _nome_unico(prefixo):
    return f'{prefixo} {uuid.uuid4().hex[:8]}'


def _criar_campanha(id_usuario, status):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO campanhas (usuario_id, titulo, descricao, meta, status) "
                "VALUES (%s, %s, %s, %s, %s)",
                (id_usuario, 'Campanha de teste', 'Descrição de teste', Decimal('100.00'), status),
            )
            id_campanha = cursor.lastrowid
        conexao.commit()
    finally:
        conexao.close()
    return id_campanha


@pytest.fixture
def campanhas(usuario):
    """
    Devolve uma função que cria campanhas da pessoa de teste. Depende de `usuario`
    para ser desmontada antes dele: avisos e campanhas saem antes da pessoa.
    """
    criadas = []

    def criar(status='ativa'):
        id_campanha = _criar_campanha(usuario, status)
        criadas.append(id_campanha)
        return id_campanha

    yield criar

    for id_campanha in criadas:
        _executar("DELETE FROM doacoes_informadas WHERE campanha_id = %s", (id_campanha,))
        _executar("DELETE FROM campanhas WHERE id = %s", (id_campanha,))


def _dados(client):
    resposta = client.get('/api/publico/dados')
    assert resposta.status_code == 200
    return resposta.get_json(), resposta.get_data(as_text=True)


def _cartao(dados, id_cartao):
    return next((cartao for cartao in dados['ongs'] if cartao['id'] == id_cartao), None)


def _campanha(cartao, id_campanha):
    return next((c for c in cartao['campanhas'] if c['id'] == id_campanha), None)


def _url_do_aviso(id_campanha):
    return f'/api/publico/campanhas/{id_campanha}/doacao-informada'


def _avisos(id_campanha):
    return _consultar(
        "SELECT valor, status FROM doacoes_informadas WHERE campanha_id = %s", (id_campanha,)
    )


# ---------- campanhas na API pública ----------

def test_campanha_de_ong_aparece_no_cartao_com_campos_fixos(client, usuario, animal, campanhas):
    nome = _nome_unico('ONG Campanha')
    _configurar_conta(usuario, 'ONG', nome, chave_pix='chave-aleatoria-pytest')
    _divulgar(animal)
    id_campanha = campanhas()

    dados, _ = _dados(client)

    cartao = _cartao(dados, usuario)
    assert cartao is not None
    item = _campanha(cartao, id_campanha)
    assert item is not None
    assert set(item) == CAMPOS_DA_CAMPANHA
    assert item['recebedor'] == nome
    assert item['meta'] == 100.0
    assert item['arrecadado'] == 0.0
    assert item['chavePix'] == 'chave-aleatoria-pytest'


def test_ong_com_campanha_e_sem_animal_divulgado_aparece(client, usuario, campanhas):
    _configurar_conta(usuario, 'ONG', _nome_unico('ONG Sem Animais'))
    id_campanha = campanhas()

    dados, _ = _dados(client)

    cartao = _cartao(dados, usuario)
    assert cartao is not None, 'a ONG com campanha ativa deveria aparecer'
    assert cartao['animais'] == []
    assert _campanha(cartao, id_campanha) is not None


def test_campanha_de_protetor_independente_nao_revela_dados_da_pessoa(client, usuario, campanhas):
    nome = _nome_unico('Nome Reservado')
    _configurar_conta(usuario, 'PROTETOR', nome, telefone='19999990001')
    email = _consultar("SELECT email FROM usuarios WHERE id = %s", (usuario,))[0]['email']
    id_campanha = campanhas()

    dados, texto = _dados(client)

    item = _campanha(_cartao(dados, 0), id_campanha)
    assert item is not None
    assert item['recebedor'] == 'Protetor(a) independente'
    assert nome not in texto
    assert '19999990001' not in texto
    assert email not in texto


def test_chave_pix_aparece_so_dentro_da_campanha(client, usuario, campanhas):
    chave = f'chave-{uuid.uuid4().hex[:8]}'
    _configurar_conta(usuario, 'PROTETOR', _nome_unico('Protetor Pix'), chave_pix=chave)
    campanhas()

    _, texto = _dados(client)

    assert texto.count(chave) == 1


@pytest.mark.parametrize('status', ['concluida', 'cancelada'])
def test_campanha_encerrada_nao_aparece(client, usuario, campanhas, status):
    _configurar_conta(usuario, 'PROTETOR', _nome_unico('Protetor Encerrada'))
    id_campanha = campanhas(status)

    dados, _ = _dados(client)

    cartao = _cartao(dados, 0)
    assert cartao is None or _campanha(cartao, id_campanha) is None


# ---------- logo e formulário de adoção dos cartões ----------

def test_cartao_dos_independentes_nao_usa_logo_nem_link_de_ninguem(client, usuario, animal):
    _configurar_conta(
        usuario, 'PROTETOR', _nome_unico('Protetor Logo'),
        logo_url='https://exemplo.invalido/logo-pytest.png',
        link_formulario_adocao='https://exemplo.invalido/formulario-pytest',
    )
    _divulgar(animal)

    dados, texto = _dados(client)

    cartao = _cartao(dados, 0)
    assert cartao['linkFormulario'] == LINK_FORMULARIO
    assert cartao['logoUrl'] is None
    assert 'logo-pytest' not in texto
    assert 'formulario-pytest' not in texto


def test_ong_usa_o_proprio_formulario_e_logo(client, usuario, animal):
    _configurar_conta(
        usuario, 'ONG', _nome_unico('ONG Propria'),
        logo_url='https://exemplo.invalido/logo-da-ong.png',
        link_formulario_adocao='https://exemplo.invalido/formulario-da-ong',
    )
    _divulgar(animal)

    dados, _ = _dados(client)

    cartao = _cartao(dados, usuario)
    assert cartao['linkFormulario'] == 'https://exemplo.invalido/formulario-da-ong'
    assert cartao['logoUrl'] == 'https://exemplo.invalido/logo-da-ong.png'


def test_ong_sem_formulario_usa_o_formulario_do_grupo(client, usuario, animal):
    _configurar_conta(usuario, 'ONG', _nome_unico('ONG Sem Link'))
    _divulgar(animal)

    dados, _ = _dados(client)

    cartao = _cartao(dados, usuario)
    assert cartao['linkFormulario'] == LINK_FORMULARIO
    assert cartao['logoUrl'] is None


# ---------- aviso de doação (rota aberta, sem login) ----------

def test_aviso_de_doacao_cria_pendente_sem_mexer_no_arrecadado(client, campanhas):
    id_campanha = campanhas()

    resposta = client.post(_url_do_aviso(id_campanha), json={'valor': '25,50'})

    assert resposta.status_code == 201
    (aviso,) = _avisos(id_campanha)
    assert aviso['valor'] == Decimal('25.50')
    assert aviso['status'] == 'pendente'
    arrecadado = _consultar(
        "SELECT arrecadado FROM campanhas WHERE id = %s", (id_campanha,)
    )[0]['arrecadado']
    assert arrecadado == 0


@pytest.mark.parametrize('valor', ['0', '-5', 'abc', '', '100000.01', 'NaN', 'Infinity'])
def test_aviso_com_valor_invalido_e_recusado(client, campanhas, valor):
    id_campanha = campanhas()

    resposta = client.post(_url_do_aviso(id_campanha), json={'valor': valor})

    assert resposta.status_code == 400
    assert len(_avisos(id_campanha)) == 0


def test_corpo_que_nao_e_objeto_json_e_recusado(client, campanhas):
    id_campanha = campanhas()
    url = _url_do_aviso(id_campanha)

    respostas = (
        client.post(url, json={}),
        client.post(url, json=[1]),
        client.post(url, json='texto'),
        client.post(url, data='isto não é json', content_type='application/json'),
    )

    for resposta in respostas:
        assert resposta.status_code == 400
    assert len(_avisos(id_campanha)) == 0


def test_aviso_em_campanha_inexistente_e_recusado(client):
    resposta = client.post(_url_do_aviso(2147483647), json={'valor': '10'})

    assert resposta.status_code == 404


def test_aviso_em_campanha_encerrada_e_recusado(client, campanhas):
    id_campanha = campanhas('concluida')

    resposta = client.post(_url_do_aviso(id_campanha), json={'valor': '10'})

    assert resposta.status_code == 404
    assert len(_avisos(id_campanha)) == 0


def test_aviso_tem_limite_de_pendentes_por_campanha(client, campanhas):
    id_campanha = campanhas()
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO doacoes_informadas (campanha_id, valor) VALUES (%s, %s)",
                [(id_campanha, Decimal('1.00'))] * LIMITE_PENDENTES_POR_CAMPANHA,
            )
        conexao.commit()
    finally:
        conexao.close()

    resposta = client.post(_url_do_aviso(id_campanha), json={'valor': '10'})

    assert resposta.status_code == 429
    assert len(_avisos(id_campanha)) == LIMITE_PENDENTES_POR_CAMPANHA

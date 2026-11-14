"""Ligação entre os cards de saúde (vacina, medicamento, consulta) e as finanças.

Cobre a exclusão: apagar o card tem de apagar a despesa que ele gerou, para não
sobrar lançamento "órfão" somando em Finanças.
"""
import pytest

from database.connection import conectar_banco

TABELAS = {'vacina': 'vacinas', 'medicamento': 'medicamentos', 'consulta': 'consultas'}
ORIGENS = {'vacina': 'VACINA', 'medicamento': 'MEDICAMENTO', 'consulta': 'CONSULTA'}


# ---------- Apoio ----------

def _limpar_saude_de(id_usuario):
    """Apaga os cards de saúde dos animais da pessoa (as chaves estrangeiras exigem isso
    antes de o conftest apagar os animais)."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            for tabela in TABELAS.values():
                cursor.execute(
                    f"DELETE FROM {tabela} WHERE animal_id IN "
                    "(SELECT id FROM animais WHERE usuario_id = %s)",
                    (id_usuario,),
                )
        conexao.commit()
    finally:
        conexao.close()


@pytest.fixture
def limpar_saude(usuario):
    yield
    _limpar_saude_de(usuario)


@pytest.fixture
def limpar_saude_do_outro(outro_usuario):
    yield
    _limpar_saude_de(outro_usuario)


def _salvar_card(client, tipo, animal, valor):
    """Cadastra o card pelo mesmo caminho que a pessoa usa na tela."""
    if tipo == 'vacina':
        url = f'/salvar_vacina/{animal}'
        dados = {'vacina': 'Raiva', 'data_vacina': '2026-11-01',
                 'status_vacina': 'aplicada', 'dose': '1', 'valor': valor}
    elif tipo == 'medicamento':
        url = f'/salvar_medicacao/{animal}'
        dados = {'medicacao': 'Vermífugo', 'dose_med': '1', 'frequencia': '8',
                 'data_inicio': '2026-11-01', 'duracao': '7', 'valor': valor}
    else:
        url = f'/cadastrar_consulta/{animal}'
        dados = {'data_consulta': '2026-11-01', 'hora_consulta': '10:00',
                 'clinica': 'Clínica de teste', 'veterinario': 'Dra. Teste',
                 'motivo': 'Rotina', 'valor': valor}
    resposta = client.post(url, data=dados)
    assert resposta.status_code == 302


def _url_apagar(tipo, id_card, animal):
    rota = {'vacina': 'deletar_vacina', 'medicamento': 'deletar_medicacao',
            'consulta': 'deletar_consulta'}[tipo]
    return f'/{rota}/{id_card}/{animal}'


def _lancamentos_do_animal(client, animal):
    return client.get(f'/api/financas/transacoes?animal_id={animal}').get_json()


def _id_do_card(client, tipo, animal):
    """O id do card, lido do lançamento que ele gerou (origem_id)."""
    lancamentos = [l for l in _lancamentos_do_animal(client, animal)
                   if l['origem_tipo'] == ORIGENS[tipo]]
    assert len(lancamentos) == 1
    return lancamentos[0]['origem_id']


def _card_existe(tipo, id_card):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total FROM {TABELAS[tipo]} WHERE id = %s", (id_card,))
            return cursor.fetchone()['total'] == 1
    finally:
        conexao.close()


def _ids_dos_cards(tipo, animal):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(f"SELECT id FROM {TABELAS[tipo]} WHERE animal_id = %s", (animal,))
            return [linha['id'] for linha in cursor.fetchall()]
    finally:
        conexao.close()


# ---------- Exclusão ----------

@pytest.mark.parametrize('tipo', ['vacina', 'medicamento', 'consulta'])
def test_apagar_card_apaga_a_despesa_dele(client_logado, animal, limpar_saude, tipo):
    _salvar_card(client_logado, tipo, animal, '80,50')
    id_card = _id_do_card(client_logado, tipo, animal)
    assert client_logado.get('/api/financas/resumo').get_json()['despesas'] == '80.50'

    resposta = client_logado.get(_url_apagar(tipo, id_card, animal))

    assert resposta.status_code == 302
    assert not _card_existe(tipo, id_card)
    assert _lancamentos_do_animal(client_logado, animal) == []
    assert client_logado.get('/api/financas/resumo').get_json()['despesas'] == '0.00'


def test_apagar_card_nao_mexe_nos_outros_lancamentos(client_logado, animal, limpar_saude):
    categoria = next(c['id'] for c in client_logado.get('/api/categorias').get_json()
                     if c['tipo'] == 'DESPESA' and c['nome'] == 'Alimentação')
    client_logado.post('/api/financas/transacoes',
                       json={'categoria_id': categoria, 'valor': 10, 'animal_id': animal})
    _salvar_card(client_logado, 'vacina', animal, '80')
    _salvar_card(client_logado, 'consulta', animal, '120')
    id_vacina = _id_do_card(client_logado, 'vacina', animal)

    client_logado.get(_url_apagar('vacina', id_vacina, animal))

    restantes = _lancamentos_do_animal(client_logado, animal)
    origens = {l['origem_tipo'] for l in restantes}
    assert len(restantes) == 2
    assert 'VACINA' not in origens
    assert 'CONSULTA' in origens
    assert client_logado.get('/api/financas/resumo').get_json()['despesas'] == '130.00'


def test_apagar_card_sem_valor_continua_funcionando(client_logado, animal, limpar_saude):
    _salvar_card(client_logado, 'vacina', animal, '')
    assert _lancamentos_do_animal(client_logado, animal) == []
    ids = _ids_dos_cards('vacina', animal)
    assert len(ids) == 1

    resposta = client_logado.get(_url_apagar('vacina', ids[0], animal))

    assert resposta.status_code == 302
    assert not _card_existe('vacina', ids[0])


def test_apagar_card_de_outra_conta_da_404_e_preserva_a_despesa(
        client_logado, outro_client, animal, animal_de_outro,
        limpar_saude, limpar_saude_do_outro):
    _salvar_card(outro_client, 'vacina', animal_de_outro, '50')
    id_card = _id_do_card(outro_client, 'vacina', animal_de_outro)

    # pelo animal da outra conta
    assert client_logado.get(_url_apagar('vacina', id_card, animal_de_outro)).status_code == 404
    # e pelo próprio animal, com o id do card alheio
    assert client_logado.get(_url_apagar('vacina', id_card, animal)).status_code == 404

    assert _card_existe('vacina', id_card)
    assert len(_lancamentos_do_animal(outro_client, animal_de_outro)) == 1

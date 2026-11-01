import uuid

import pytest

from database.connection import conectar_banco


def _dados(**mudancas):
    """Dados válidos de cadastro; cada teste troca só o que quer testar."""
    dados = {
        'tipo': 'PROTETOR',
        'nome': 'Conta de teste',
        'email': f'pytest_{uuid.uuid4().hex[:12]}@exemplo.invalido',
        'senha': 'senha-de-teste',
        'cidade': 'Campinas',
        'uf': 'SP',
    }
    dados.update(mudancas)
    return dados


def _buscar_conta(email):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT tipo, cidade, uf FROM usuarios WHERE email = %s", (email,))
            return cursor.fetchone()
    finally:
        conexao.close()


def test_tela_de_cadastro_traz_perfil_e_estados(client):
    html = client.get('/cadastro').get_data(as_text=True)
    assert 'value="PROTETOR"' in html
    assert 'value="ONG"' in html
    assert '<option value="SP">' in html


@pytest.mark.parametrize('tipo', ['PROTETOR', 'ONG'])
def test_cadastro_grava_perfil_cidade_e_estado(client, emails_de_teste, tipo):
    dados = _dados(tipo=tipo)
    emails_de_teste.append(dados['email'])

    resposta = client.post('/cadastrar', data=dados)

    assert resposta.status_code == 302
    assert resposta.headers['Location'].endswith('/painel')
    assert _buscar_conta(dados['email']) == {'tipo': tipo, 'cidade': 'Campinas', 'uf': 'SP'}


@pytest.mark.parametrize('mudanca', [
    {'tipo': 'ADMIN'},
    {'tipo': ''},
    {'uf': 'XX'},
    {'uf': ''},
    {'cidade': ''},
    {'cidade': '   '},
    {'cidade': 'x' * 101},
    {'nome': ''},
    {'senha': ''},
])
def test_cadastro_invalido_e_recusado(client, emails_de_teste, mudanca):
    dados = _dados(**mudanca)
    emails_de_teste.append(dados['email'])

    resposta = client.post('/cadastrar', data=dados)

    assert resposta.status_code == 400
    assert _buscar_conta(dados['email']) is None


def test_cadastro_sem_escolher_o_perfil_e_recusado(client, emails_de_teste):
    dados = _dados()
    del dados['tipo']
    emails_de_teste.append(dados['email'])

    assert client.post('/cadastrar', data=dados).status_code == 400
    assert _buscar_conta(dados['email']) is None


def test_email_repetido_continua_sendo_recusado(client, emails_de_teste):
    dados = _dados()
    emails_de_teste.append(dados['email'])
    client.post('/cadastrar', data=dados)

    resposta = client.post('/cadastrar', data=dados)

    assert 'E-mail já cadastrado' in resposta.get_data(as_text=True)
"""
Testes do acesso à conta: erros do login mostrados na própria tela, tamanho mínimo
da senha e página de erro no mesmo estilo das demais telas.

As contas de teste são criadas pelo cadastro (e-mail iniciado em pytest_) e apagadas
no fim pela fixture emails_de_teste, do conftest.py.
"""
import uuid

import pytest

from app import app as flask_app
from database.connection import conectar_banco

SENHA = 'senha-de-teste'
MENSAGEM_DE_LOGIN = 'E-mail ou senha incorretos.'


# ---------- ajudas ----------

def _email_novo(emails_de_teste):
    email = f'pytest_{uuid.uuid4().hex[:12]}@exemplo.invalido'
    emails_de_teste.append(email)
    return email


def _dados_de_cadastro(email, **extras):
    return {
        'tipo': 'PROTETOR', 'nome': 'Pessoa de teste', 'email': email,
        'senha': SENHA, 'cidade': 'Campinas', 'uf': 'SP', **extras,
    }


def _conta_existe(email):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            return cursor.fetchone() is not None
    finally:
        conexao.close()


@pytest.fixture
def visitante():
    """Navegador sem login (o `client` do conftest fica logado depois de um cadastro)."""
    flask_app.config['TESTING'] = True
    return flask_app.test_client()


@pytest.fixture
def conta(client, emails_de_teste):
    """Uma conta de teste criada pelo cadastro; devolve o e-mail dela."""
    email = _email_novo(emails_de_teste)
    assert client.post('/cadastrar', data=_dados_de_cadastro(email)).status_code == 302
    return email


# ---------- login ----------

def test_login_certo_entra_no_painel(visitante, conta):
    resposta = visitante.post('/login', data={'email': conta, 'senha': SENHA})

    assert resposta.status_code == 302
    assert resposta.headers['Location'].endswith('/painel')


def test_login_com_senha_errada_mostra_a_mensagem_na_tela(visitante, conta):
    resposta = visitante.post('/login', data={'email': conta, 'senha': 'senha-errada'})
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 401
    assert MENSAGEM_DE_LOGIN in html
    assert 'alert(' not in html  # não é mais um alert() do navegador
    assert 'pp-navbar' in html  # continua no tema das telas
    assert f'value="{conta}"' in html  # o e-mail digitado fica preenchido
    assert 'senha-errada' not in html  # a senha nunca volta para a tela


def test_login_com_email_inexistente_tem_a_mesma_resposta(visitante, conta):
    errada = visitante.post('/login', data={'email': conta, 'senha': 'senha-errada'})
    inexistente = visitante.post(
        '/login', data={'email': 'ninguem@exemplo.invalido', 'senha': SENHA}
    )

    # igual para os dois casos: não revela se o e-mail tem conta
    assert inexistente.status_code == errada.status_code == 401
    assert MENSAGEM_DE_LOGIN in inexistente.get_data(as_text=True)


@pytest.mark.parametrize('dados', [{}, {'email': 'a@exemplo.invalido'}, {'senha': SENHA}])
def test_login_sem_preencher_pede_e_mail_e_senha(visitante, dados):
    resposta = visitante.post('/login', data=dados)

    assert resposta.status_code == 400
    assert 'Informe o e-mail e a senha.' in resposta.get_data(as_text=True)


def test_login_nao_executa_o_que_foi_digitado_no_email(visitante):
    perigoso = '"><script>alert(1)</script>@exemplo.invalido'

    html = visitante.post('/login', data={'email': perigoso, 'senha': SENHA}).get_data(as_text=True)

    assert '<script>alert(1)' not in html
    assert '&lt;script&gt;' in html


# ---------- senha mínima no cadastro ----------

@pytest.mark.parametrize('senha', ['', 'abc', '1234567'])
def test_cadastro_recusa_senha_curta(client, emails_de_teste, senha):
    email = _email_novo(emails_de_teste)

    resposta = client.post('/cadastrar', data=_dados_de_cadastro(email, senha=senha))

    assert resposta.status_code == 400
    assert not _conta_existe(email)


def test_cadastro_explica_o_tamanho_minimo_da_senha(client, emails_de_teste):
    email = _email_novo(emails_de_teste)

    html = client.post('/cadastrar', data=_dados_de_cadastro(email, senha='abc1234')).get_data(as_text=True)

    assert 'pelo menos 8 caracteres' in html


def test_cadastro_aceita_senha_com_oito_caracteres(client, emails_de_teste):
    email = _email_novo(emails_de_teste)

    resposta = client.post('/cadastrar', data=_dados_de_cadastro(email, senha='12345678'))

    assert resposta.status_code == 302
    assert _conta_existe(email)


# ---------- páginas de erro no tema ----------

def test_erro_de_validacao_do_cadastro_usa_a_pagina_no_tema(client, emails_de_teste):
    email = _email_novo(emails_de_teste)

    resposta = client.post('/cadastrar', data=_dados_de_cadastro(email, uf='XX'))
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 400
    assert 'pp-navbar' in html
    assert 'Escolha o estado.' in html
    assert 'href="/cadastro"' in html  # botão para voltar
    assert 'color: red' not in html  # sem o HTML solto de antes


def test_email_repetido_mostra_a_pagina_no_tema_com_opcao_de_entrar(client, conta):
    resposta = client.post('/cadastrar', data=_dados_de_cadastro(conta))
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 409
    assert 'E-mail já cadastrado' in html
    assert 'pp-navbar' in html
    assert 'href="/login"' in html


def test_erro_do_perfil_usa_a_pagina_no_tema(client_logado):
    resposta = client_logado.post('/editar_usuario', data={
        'tipo': 'PROTETOR', 'nome': 'Pessoa de teste', 'cidade': 'Campinas', 'uf': 'SP',
        'chave_pix': '', 'logo_url': 'javascript:alert(1)',
    })
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 400
    assert 'pp-navbar' in html
    assert 'href="/editar_usuario"' in html

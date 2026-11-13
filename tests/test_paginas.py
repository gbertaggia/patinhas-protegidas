"""
Testes das páginas HTML: cada tela abre sem erro, as páginas internas mostram a
barra do topo comum e os arquivos do tema (CSS e ícone) existem.

Usam a pessoa de teste (e-mail iniciado em pytest_) criada pelas fixtures do
conftest.py; o que for criado é apagado no fim.
"""
import pytest


@pytest.fixture
def navegador(client_logado):
    """Navegador logado, com os dados de sessão que as telas internas mostram."""
    with client_logado.session_transaction() as sessao:
        sessao['usuario_logado'] = 'pytest@exemplo.invalido'
        sessao['nome_usuario'] = 'Pessoa de teste'
    return client_logado


def _confere_barra_do_topo(resposta):
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'pp-navbar' in html
    assert 'css/tema.css' in html
    assert html.count('aria-current="page"') == 1  # só um item do menu fica destacado
    assert 'Pessoa de teste' in html  # o nome da sessão aparece na saudação


@pytest.mark.parametrize('caminho', ['/painel', '/financas'])
def test_pagina_interna_abre_com_a_barra_do_topo(navegador, caminho):
    _confere_barra_do_topo(navegador.get(caminho))


def test_pagina_do_animal_abre_com_a_barra_do_topo(navegador, animal):
    _confere_barra_do_topo(navegador.get(f'/pagina_animal/{animal}'))


@pytest.mark.parametrize('caminho', ['/login', '/cadastro'])
def test_pagina_sem_login_abre(client, caminho):
    assert client.get(caminho).status_code == 200


def test_pagina_publica_para_visitante_tem_entrar_e_criar_conta(client):
    resposta = client.get('/')
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert 'pp-navbar' in html
    assert 'css/tema.css' in html
    assert 'css/publico.css' not in html  # arquivo que não existe
    assert 'href="/login"' in html
    assert 'href="/cadastro"' in html
    assert 'pp-menu' not in html  # o menu é só de quem está logado


def test_pagina_publica_para_quem_esta_logado_tem_o_menu(navegador):
    resposta = navegador.get('/')
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert 'pp-menu' in html
    assert html.count('aria-current="page"') == 1  # "Página pública" destacada
    assert 'Pessoa de teste' in html
    assert 'href="/cadastro"' not in html  # quem já tem conta não vê "Criar conta"


@pytest.mark.parametrize('caminho, tipo', [
    ('/static/css/tema.css', 'text/css'),
    ('/static/img/favicon.svg', 'image/svg+xml'),
])
def test_arquivos_do_tema_existem(client, caminho, tipo):
    resposta = client.get(caminho)

    assert resposta.status_code == 200
    assert resposta.mimetype == tipo
    resposta.close()

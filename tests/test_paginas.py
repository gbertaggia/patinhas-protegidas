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
def test_login_e_cadastro_tem_barra_do_topo_e_volta_para_a_pagina_publica(client, caminho):
    resposta = client.get(caminho)
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert 'pp-navbar' in html
    assert 'css/tema.css' in html
    assert html.count('aria-current="page"') == 1  # o botão da página atual
    assert 'href="/"' in html  # caminho de volta para a página pública


def test_cadastro_avisa_o_que_fica_publico(client):
    html = client.get('/cadastro').get_data(as_text=True)

    assert 'Sua privacidade' in html
    # os campos que o servidor lê continuam no formulário
    for campo in ('tipo', 'nome', 'email', 'telefone', 'cidade', 'uf', 'missao',
                  'logo_url', 'link_formulario_adocao', 'senha'):
        assert f'name="{campo}"' in html


def test_editar_perfil_abre_com_a_barra_do_topo(navegador):
    resposta = navegador.get('/editar_usuario')
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert 'pp-navbar' in html
    assert 'css/tema.css' in html
    assert html.count('aria-current="page"') == 1  # "Editar perfil" destacado
    for campo in ('tipo', 'nome', 'telefone', 'cidade', 'uf', 'missao',
                  'logo_url', 'link_formulario_adocao', 'chave_pix'):
        assert f'name="{campo}"' in html


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

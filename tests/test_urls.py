"""
Testes dos links (URLs) informados em formulários.

Só endereços http:// e https:// são aceitos: o resto (javascript:, data:...)
poderia executar código quando o link fosse usado numa página.

Os testes de rotas usam a pessoa de teste (e-mail iniciado em pytest_) criada
pelas fixtures do conftest.py. O que é criado aqui é apagado no fim: as
campanhas saem antes da pessoa, porque a chave estrangeira é RESTRICT.
"""
import uuid

import pytest

from database.connection import conectar_banco
from utils.urls import normalizar_url_http

LINK_PERIGOSO = 'javascript:alert(1)'
LINK_BOM = 'https://exemplo.invalido/imagem.png'
CAMPOS_DE_LINK_DO_PERFIL = ['logo_url', 'link_formulario_adocao']


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


@pytest.fixture
def limpar_campanhas(usuario):
    """Apaga as campanhas criadas pelo teste antes de a pessoa de teste ser removida."""
    yield
    _executar(
        "DELETE FROM doacoes_informadas WHERE campanha_id IN "
        "(SELECT id FROM campanhas WHERE usuario_id = %s)",
        (usuario,),
    )
    _executar("DELETE FROM campanhas WHERE usuario_id = %s", (usuario,))


# ---------- a regra em si (não usa o banco) ----------

@pytest.mark.parametrize('texto, esperado', [
    ('https://exemplo.com/foto.png', 'https://exemplo.com/foto.png'),
    ('http://exemplo.com', 'http://exemplo.com'),
    ('  https://exemplo.com/a?b=1&c=2  ', 'https://exemplo.com/a?b=1&c=2'),
    ('HTTPS://EXEMPLO.COM/Foto.png', 'HTTPS://EXEMPLO.COM/Foto.png'),
    ('https://forms.gle/abc123', 'https://forms.gle/abc123'),
])
def test_link_valido_e_aceito(texto, esperado):
    assert normalizar_url_http(texto, 'O link') == (esperado, None)


@pytest.mark.parametrize('texto', [None, '', '   ', '\n'])
def test_link_vazio_vira_none_sem_erro(texto):
    assert normalizar_url_http(texto, 'O link') == (None, None)


@pytest.mark.parametrize('texto', [
    'javascript:alert(1)',
    'JavaScript:alert(1)',
    'data:text/html,<b>x</b>',
    'vbscript:x',
    'ftp://exemplo.com/a.png',
    'file:///etc/passwd',
    'exemplo.com/foto.png',
    'www.exemplo.com',
    '//exemplo.com/a.png',
    'https://',
    'http:///foto.png',
    'https://exemplo .com/foto.png',
    'https://exemplo.com/foto\n.png',
    'https://exemplo.com/\x00',
    'http://[::1',
    123,
    ['https://exemplo.com'],
])
def test_link_invalido_e_recusado(texto):
    url, erro = normalizar_url_http(texto, 'O link da foto')

    assert url is None
    assert erro and erro.startswith('O link da foto')


def test_link_longo_demais_e_recusado():
    url, erro = normalizar_url_http('https://exemplo.com/' + 'a' * 300, 'O link', limite=255)

    assert url is None
    assert 'muito longo' in erro


def test_link_no_limite_e_aceito():
    link = 'https://exemplo.com/' + 'a' * (255 - len('https://exemplo.com/'))

    assert len(link) == 255
    assert normalizar_url_http(link, 'O link', limite=255) == (link, None)


# ---------- cadastro de conta ----------

def _dados_de_cadastro(email, **extras):
    return {
        'tipo': 'PROTETOR', 'nome': 'Pessoa de teste', 'email': email,
        'senha': 'senha-de-teste', 'cidade': 'Campinas', 'uf': 'SP', **extras,
    }


def _email_novo(emails_de_teste):
    email = f'pytest_{uuid.uuid4().hex[:12]}@exemplo.invalido'
    emails_de_teste.append(email)
    return email


@pytest.mark.parametrize('campo', CAMPOS_DE_LINK_DO_PERFIL)
def test_cadastro_recusa_link_perigoso(client, emails_de_teste, campo):
    email = _email_novo(emails_de_teste)

    resposta = client.post('/cadastrar', data=_dados_de_cadastro(email, **{campo: LINK_PERIGOSO}))

    assert resposta.status_code == 400
    assert len(_consultar("SELECT id FROM usuarios WHERE email = %s", (email,))) == 0


def test_cadastro_aceita_links_https(client, emails_de_teste):
    email = _email_novo(emails_de_teste)

    resposta = client.post('/cadastrar', data=_dados_de_cadastro(
        email, logo_url=LINK_BOM, link_formulario_adocao='https://exemplo.invalido/formulario',
    ))

    assert resposta.status_code == 302
    conta = _consultar(
        "SELECT logo_url, link_formulario_adocao FROM usuarios WHERE email = %s", (email,)
    )[0]
    assert conta['logo_url'] == LINK_BOM
    assert conta['link_formulario_adocao'] == 'https://exemplo.invalido/formulario'


# ---------- edição do perfil ----------

def _dados_de_perfil(**extras):
    return {
        'tipo': 'PROTETOR', 'nome': 'Pessoa de teste', 'cidade': 'Campinas',
        'uf': 'SP', 'chave_pix': '', **extras,
    }


@pytest.mark.parametrize('campo', CAMPOS_DE_LINK_DO_PERFIL)
def test_perfil_recusa_link_perigoso(client_logado, usuario, campo):
    resposta = client_logado.post('/editar_usuario', data=_dados_de_perfil(**{campo: LINK_PERIGOSO}))

    assert resposta.status_code == 400
    conta = _consultar(
        "SELECT logo_url, link_formulario_adocao FROM usuarios WHERE id = %s", (usuario,)
    )[0]
    assert conta['logo_url'] is None
    assert conta['link_formulario_adocao'] is None


def test_perfil_aceita_links_https(client_logado, usuario):
    resposta = client_logado.post('/editar_usuario', data=_dados_de_perfil(
        logo_url=LINK_BOM, link_formulario_adocao='https://exemplo.invalido/formulario',
    ))

    assert resposta.status_code == 302
    conta = _consultar(
        "SELECT logo_url, link_formulario_adocao FROM usuarios WHERE id = %s", (usuario,)
    )[0]
    assert conta['logo_url'] == LINK_BOM
    assert conta['link_formulario_adocao'] == 'https://exemplo.invalido/formulario'


# ---------- foto do animal ----------

def test_cadastro_de_animal_recusa_foto_perigosa(client_logado, usuario):
    resposta = client_logado.post('/cadastrar_animal', data={
        'nome': 'Bichano', 'especie': 'gato', 'foto-pet': LINK_PERIGOSO,
    })

    assert resposta.status_code == 400
    assert len(_consultar("SELECT id FROM animais WHERE usuario_id = %s", (usuario,))) == 0


def test_cadastro_de_animal_aceita_foto_https(client_logado, usuario):
    resposta = client_logado.post('/cadastrar_animal', data={
        'nome': 'Bichano', 'especie': 'gato', 'foto-pet': LINK_BOM,
    })

    assert resposta.status_code == 302
    (animal,) = _consultar("SELECT foto_url FROM animais WHERE usuario_id = %s", (usuario,))
    assert animal['foto_url'] == LINK_BOM


def test_edicao_de_animal_recusa_foto_perigosa(client_logado, animal):
    resposta = client_logado.post(f'/salvar_edicao/{animal}', data={
        'nome': 'Novo nome', 'especie': 'gato', 'raca': 'SRD', 'foto-pet': LINK_PERIGOSO,
    })

    assert resposta.status_code == 400
    linha = _consultar("SELECT nome, foto_url FROM animais WHERE id = %s", (animal,))[0]
    assert linha['nome'] == 'Animal de teste'  # nada foi alterado
    assert linha['foto_url'] is None


def test_edicao_de_animal_aceita_foto_https(client_logado, animal):
    resposta = client_logado.post(f'/salvar_edicao/{animal}', data={
        'nome': 'Novo nome', 'especie': 'gato', 'raca': 'SRD', 'foto-pet': LINK_BOM,
    })

    assert resposta.status_code == 302
    linha = _consultar("SELECT foto_url FROM animais WHERE id = %s", (animal,))[0]
    assert linha['foto_url'] == LINK_BOM


# ---------- foto da campanha ----------

def _campanha(**extras):
    return {'titulo': 'Campanha de teste', 'descricao': 'Descrição de teste', 'meta': '100', **extras}


def test_campanha_recusa_foto_perigosa(client_logado, usuario, limpar_campanhas):
    resposta = client_logado.post('/api/campanhas', json=_campanha(foto_url=LINK_PERIGOSO))

    assert resposta.status_code == 400
    assert 'http' in resposta.get_json()['erro']
    assert len(_consultar("SELECT id FROM campanhas WHERE usuario_id = %s", (usuario,))) == 0


@pytest.mark.parametrize('foto, esperado', [(LINK_BOM, LINK_BOM), (None, None), ('', None)])
def test_campanha_aceita_foto_https_ou_sem_foto(client_logado, usuario, limpar_campanhas, foto, esperado):
    resposta = client_logado.post('/api/campanhas', json=_campanha(foto_url=foto))

    assert resposta.status_code == 201
    (campanha,) = _consultar("SELECT foto_url FROM campanhas WHERE usuario_id = %s", (usuario,))
    assert campanha['foto_url'] == esperado

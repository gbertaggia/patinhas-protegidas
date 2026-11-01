import pytest

from database.connection import conectar_banco


def _perfil(id_usuario):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT nome, telefone, tipo, cidade, uf FROM usuarios WHERE id = %s",
                (id_usuario,),
            )
            return cursor.fetchone()
    finally:
        conexao.close()


def _dados(**mudancas):
    """Dados válidos de edição; cada teste troca só o que quer testar."""
    dados = {
        'nome': 'Nome novo',
        'telefone': '(19) 99999-0000',
        'tipo': 'ONG',
        'cidade': 'Campinas',
        'uf': 'SP',
    }
    dados.update(mudancas)
    return dados


def test_editar_perfil_exige_login(client):
    resposta = client.get('/editar_usuario')
    assert resposta.status_code == 302
    assert 'login' in resposta.headers['Location']


def test_editar_perfil_grava_os_novos_dados(client_logado, usuario):
    resposta = client_logado.post('/editar_usuario', data=_dados())

    assert resposta.status_code == 302
    assert _perfil(usuario) == {
        'nome': 'Nome novo',
        'telefone': '(19) 99999-0000',
        'tipo': 'ONG',
        'cidade': 'Campinas',
        'uf': 'SP',
    }


def test_telefone_vazio_vira_nulo(client_logado, usuario):
    client_logado.post('/editar_usuario', data=_dados(telefone=''))
    assert _perfil(usuario)['telefone'] is None


def test_tela_de_edicao_mostra_os_dados_salvos(client_logado):
    client_logado.post('/editar_usuario', data=_dados(cidade='Santos'))

    html = client_logado.get('/editar_usuario').get_data(as_text=True)

    assert 'value="Santos"' in html


@pytest.mark.parametrize('mudanca', [
    {'tipo': 'ADMIN'},
    {'tipo': ''},
    {'uf': 'XX'},
    {'uf': ''},
    {'cidade': ''},
    {'cidade': '   '},
    {'cidade': 'x' * 101},
    {'nome': ''},
    {'nome': 'x' * 101},
])
def test_edicao_invalida_e_recusada(client_logado, usuario, mudanca):
    antes = _perfil(usuario)

    resposta = client_logado.post('/editar_usuario', data=_dados(**mudanca))

    assert resposta.status_code == 400
    assert _perfil(usuario) == antes


def test_editar_perfil_nao_altera_a_conta_de_outra_pessoa(client_logado, outro_usuario):
    antes = _perfil(outro_usuario)

    client_logado.post('/editar_usuario', data=_dados())

    assert _perfil(outro_usuario) == antes
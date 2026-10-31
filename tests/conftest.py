import uuid

import pytest
from werkzeug.security import generate_password_hash

from app import app as flask_app
from database.connection import conectar_banco


def _criar_usuario():
    email = f"pytest_{uuid.uuid4().hex[:12]}@exemplo.invalido"
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
                ("Usuário de teste", email, generate_password_hash("senha-de-teste")),
            )
            id_usuario = cursor.lastrowid
        conexao.commit()
    finally:
        conexao.close()
    return id_usuario


def _remover_usuario(id_usuario):
    """Apaga o usuário de teste e tudo o que ele criou (nessa ordem, por causa das chaves)."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM transacoes WHERE usuario_id = %s", (id_usuario,))
            cursor.execute("DELETE FROM animais WHERE usuario_id = %s", (id_usuario,))
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        conexao.commit()
    finally:
        conexao.close()


def _client_logado(id_usuario):
    cliente = flask_app.test_client()
    with cliente.session_transaction() as sessao:
        sessao['id_usuario'] = id_usuario
    return cliente


@pytest.fixture
def client():
    """Navegador falso, sem login."""
    flask_app.config['TESTING'] = True
    return flask_app.test_client()


@pytest.fixture
def usuario():
    id_usuario = _criar_usuario()
    yield id_usuario
    _remover_usuario(id_usuario)


@pytest.fixture
def outro_usuario():
    id_usuario = _criar_usuario()
    yield id_usuario
    _remover_usuario(id_usuario)


@pytest.fixture
def client_logado(usuario):
    """Navegador falso, já logado como o usuário de teste."""
    flask_app.config['TESTING'] = True
    return _client_logado(usuario)


@pytest.fixture
def outro_client(outro_usuario):
    """Navegador falso logado como uma segunda pessoa."""
    return _client_logado(outro_usuario)
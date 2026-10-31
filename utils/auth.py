from functools import wraps
from flask import session, redirect, jsonify
from database.connection import conectar_banco

TABELAS_SAUDE = ('vacinas', 'medicamentos', 'consultas', 'historico_veterinario')


def login_required(f):
    """Barra quem não está logado e manda para a tela de login."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'id_usuario' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorada

def api_login_required(f):
    """Como o login_required, mas responde JSON 401 em vez de redirecionar."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'id_usuario' not in session:
            return jsonify({"erro": "Faça login para continuar."}), 401
        return f(*args, **kwargs)
    return decorada


def animal_do_usuario(id_animal):
    """Retorna True somente se o animal pertence ao usuário logado."""
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id FROM animais WHERE id = %s AND usuario_id = %s",
            (id_animal, session['id_usuario'])
        )
        return cursor.fetchone() is not None
    finally:
        conexao.close()


def registro_do_usuario(tabela, id_registro, id_animal=None):
    """True somente se o registro de saúde pertence a um animal do usuário logado
    (e, quando informado, ao animal indicado na URL)."""
    if tabela not in TABELAS_SAUDE:  # a tabela vem do código, nunca do usuário
        raise ValueError("tabela inválida")
    sql = (f"SELECT t.id FROM {tabela} t JOIN animais a ON a.id = t.animal_id "
           "WHERE t.id = %s AND a.usuario_id = %s")
    valores = [id_registro, session['id_usuario']]
    if id_animal is not None:
        sql += " AND t.animal_id = %s"
        valores.append(id_animal)
    conexao = conectar_banco()
    try:
        cursor = conexao.cursor()
        cursor.execute(sql, tuple(valores))
        return cursor.fetchone() is not None
    finally:
        conexao.close()
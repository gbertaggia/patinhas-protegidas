from flask import Blueprint, jsonify

from database.connection import conectar_banco
from utils.auth import login_required

financas_bp = Blueprint('financas', __name__)


@financas_bp.route('/api/categorias')
@login_required
def listar_categorias():
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id, tipo, nome FROM categorias ORDER BY tipo, nome")
            categorias = cursor.fetchall()
        return jsonify(categorias)
    finally:
        conexao.close()
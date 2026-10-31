from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, current_app, jsonify, request, session

from database.connection import conectar_banco
from utils.auth import animal_do_usuario, api_login_required

financas_bp = Blueprint('financas', __name__)

VALOR_MAXIMO = Decimal('99999999.99')


def _erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def _como_inteiro(valor):
    """Aceita 7 ou '7'; qualquer outra coisa vira None."""
    if isinstance(valor, int) and not isinstance(valor, bool):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor)
    return None


@financas_bp.route('/api/categorias')
@api_login_required
def listar_categorias():
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id, tipo, nome FROM categorias ORDER BY tipo, nome")
            categorias = cursor.fetchall()
        return jsonify(categorias)
    finally:
        conexao.close()


@financas_bp.route('/api/financas/transacoes', methods=['POST'])
@api_login_required
def criar_transacao():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return _erro("Envie os dados em formato JSON.")

    # Valor: aceita 25.5 ou "25,50"
    try:
        valor = Decimal(str(dados.get('valor', '')).strip().replace(',', '.'))
    except InvalidOperation:
        return _erro("Valor inválido.")
    if not valor.is_finite() or valor <= 0 or valor > VALOR_MAXIMO:
        return _erro("O valor deve ser maior que zero e menor que 100 milhões.")
    valor = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Categoria
    categoria_id = _como_inteiro(dados.get('categoria_id'))
    if categoria_id is None:
        return _erro("Escolha uma categoria.")

    # Animal (opcional: sem animal = lançamento geral)
    animal_id = None
    if dados.get('animal_id') not in (None, ''):
        animal_id = _como_inteiro(dados.get('animal_id'))
        if animal_id is None or not animal_do_usuario(animal_id):
            return _erro("Animal não encontrado.", 404)

    # Data (opcional: padrão é hoje)
    data_transacao = date.today()
    if dados.get('data_transacao') not in (None, ''):
        try:
            data_transacao = date.fromisoformat(str(dados['data_transacao']))
        except ValueError:
            return _erro("Data inválida. Use o formato AAAA-MM-DD.")

    # Descrição (opcional)
    descricao = dados.get('descricao')
    if descricao is not None:
        if not isinstance(descricao, str):
            return _erro("Descrição inválida.")
        descricao = descricao.strip() or None
        if descricao and len(descricao) > 255:
            return _erro("A descrição pode ter no máximo 255 caracteres.")

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT tipo FROM categorias WHERE id = %s", (categoria_id,))
            categoria = cursor.fetchone()
            if categoria is None:
                return _erro("Categoria não encontrada.")

            cursor.execute(
                """INSERT INTO transacoes
                   (usuario_id, animal_id, categoria_id, tipo, valor, descricao, data_transacao)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (session['id_usuario'], animal_id, categoria_id,
                 categoria['tipo'], valor, descricao, data_transacao)
            )
            novo_id = cursor.lastrowid
        conexao.commit()
        return jsonify({
            "id": novo_id,
            "tipo": categoria['tipo'],
            "valor": str(valor),
            "data_transacao": data_transacao.isoformat(),
        }), 201
    except Exception:
        conexao.rollback()
        current_app.logger.exception("Erro ao criar transação")
        return _erro("Não foi possível salvar o lançamento.", 500)
    finally:
        conexao.close()
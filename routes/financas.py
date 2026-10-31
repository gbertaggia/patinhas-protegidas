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

def _ler_data(nome):
    """Lê uma data AAAA-MM-DD da URL. Devolve (data, erro)."""
    texto = request.args.get(nome, '').strip()
    if not texto:
        return None, None
    try:
        return date.fromisoformat(texto), None
    except ValueError:
        return None, f"Data inválida em '{nome}'. Use o formato AAAA-MM-DD."


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

@financas_bp.route('/api/financas/transacoes')
@api_login_required
def listar_transacoes():
    # Sempre filtra pela pessoa logada: ninguém vê lançamento de outra conta.
    condicoes = ["t.usuario_id = %s"]
    parametros = [session['id_usuario']]

    inicio, erro = _ler_data('inicio')
    if erro:
        return _erro(erro)
    fim, erro = _ler_data('fim')
    if erro:
        return _erro(erro)
    if inicio and fim and inicio > fim:
        return _erro("A data inicial não pode ser maior que a final.")
    if inicio:
        condicoes.append("t.data_transacao >= %s")
        parametros.append(inicio)
    if fim:
        condicoes.append("t.data_transacao <= %s")
        parametros.append(fim)

    tipo = request.args.get('tipo', '').strip().upper()
    if tipo:
        if tipo not in ('RECEITA', 'DESPESA'):
            return _erro("Tipo inválido. Use RECEITA ou DESPESA.")
        condicoes.append("t.tipo = %s")
        parametros.append(tipo)

    categoria = request.args.get('categoria_id', '').strip()
    if categoria:
        categoria_id = _como_inteiro(categoria)
        if categoria_id is None:
            return _erro("Categoria inválida.")
        condicoes.append("t.categoria_id = %s")
        parametros.append(categoria_id)

    # animal_id=7 filtra um animal; animal_id=geral traz só os lançamentos gerais
    animal = request.args.get('animal_id', '').strip()
    if animal:
        if animal.lower() == 'geral':
            condicoes.append("t.animal_id IS NULL")
        else:
            animal_id = _como_inteiro(animal)
            if animal_id is None:
                return _erro("Animal inválido.")
            condicoes.append("t.animal_id = %s")
            parametros.append(animal_id)

    limite = _como_inteiro(request.args.get('limite', '100'))
    if limite is None or not 1 <= limite <= 500:
        return _erro("O limite deve estar entre 1 e 500.")
    parametros.append(limite)

    # As condições acima são textos fixos do código; os valores vão em parâmetros (%s).
    consulta = f"""
        SELECT t.id, t.tipo, t.valor, t.descricao, t.data_transacao,
               t.categoria_id, c.nome AS categoria,
               t.animal_id, a.nome AS animal,
               t.origem_tipo, t.origem_id
        FROM transacoes t
        JOIN categorias c ON c.id = t.categoria_id
        LEFT JOIN animais a ON a.id = t.animal_id
        WHERE {' AND '.join(condicoes)}
        ORDER BY t.data_transacao DESC, t.id DESC
        LIMIT %s
    """

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(consulta, parametros)
            linhas = cursor.fetchall()
    finally:
        conexao.close()

    return jsonify([{
        "id": l['id'],
        "tipo": l['tipo'],
        "valor": str(l['valor']),
        "descricao": l['descricao'],
        "data_transacao": l['data_transacao'].isoformat(),
        "categoria_id": l['categoria_id'],
        "categoria": l['categoria'],
        "animal_id": l['animal_id'],
        "animal": l['animal'],
        "origem_tipo": l['origem_tipo'],
        "origem_id": l['origem_id'],
    } for l in linhas])


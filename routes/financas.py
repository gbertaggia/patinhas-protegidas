from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, current_app, jsonify, render_template, request, session

from database.connection import conectar_banco
from utils.auth import animal_do_usuario, api_login_required, login_required

financas_bp = Blueprint('financas', __name__)

VALOR_MAXIMO = Decimal('99999999.99')
MESES_MAXIMOS = 120  # limite de barras no gráfico mensal (10 anos)


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


def _montar_filtros():
    """Lê os filtros da URL e monta as condições do WHERE."""
    condicoes = ["t.usuario_id = %s"]
    parametros = [session['id_usuario']]

    inicio, erro = _ler_data('inicio')
    if erro:
        return None, None, erro
    fim, erro = _ler_data('fim')
    if erro:
        return None, None, erro
    if inicio and fim and inicio > fim:
        return None, None, "A data inicial não pode ser maior que a final."
    if inicio:
        condicoes.append("t.data_transacao >= %s")
        parametros.append(inicio)
    if fim:
        condicoes.append("t.data_transacao <= %s")
        parametros.append(fim)

    tipo = request.args.get('tipo', '').strip().upper()
    if tipo:
        if tipo not in ('RECEITA', 'DESPESA'):
            return None, None, "Tipo inválido. Use RECEITA ou DESPESA."
        condicoes.append("t.tipo = %s")
        parametros.append(tipo)

    categoria = request.args.get('categoria_id', '').strip()
    if categoria:
        categoria_id = _como_inteiro(categoria)
        if categoria_id is None:
            return None, None, "Categoria inválida."
        condicoes.append("t.categoria_id = %s")
        parametros.append(categoria_id)

    animal = request.args.get('animal_id', '').strip()
    if animal:
        if animal.lower() == 'geral':
            condicoes.append("t.animal_id IS NULL")
        else:
            animal_id = _como_inteiro(animal)
            if animal_id is None:
                return None, None, "Animal inválido."
            condicoes.append("t.animal_id = %s")
            parametros.append(animal_id)

    return condicoes, parametros, None


# ==========================================
# ROTAS DE CATEGORIAS E TRANSAÇÕES
# ==========================================

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

    try:
        valor = Decimal(str(dados.get('valor', '')).strip().replace(',', '.'))
    except InvalidOperation:
        return _erro("Valor inválido.")
    if not valor.is_finite() or valor <= 0:
        return _erro("O valor deve ser maior que zero.")
    if valor > VALOR_MAXIMO:
        return _erro("O valor máximo permitido é R$ 99.999.999,99.")
    valor = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    categoria_id = _como_inteiro(dados.get('categoria_id'))
    if categoria_id is None:
        return _erro("Escolha uma categoria.")

    animal_id = None
    if dados.get('animal_id') not in (None, ''):
        animal_id = _como_inteiro(dados.get('animal_id'))
        if animal_id is None or not animal_do_usuario(animal_id):
            return _erro("Animal não encontrado.", 404)

    data_transacao = date.today()
    if dados.get('data_transacao') not in (None, ''):
        try:
            data_transacao = date.fromisoformat(str(dados['data_transacao']))
        except ValueError:
            return _erro("Data inválida. Use o formato AAAA-MM-DD.")

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
    condicoes, parametros, erro = _montar_filtros()
    if erro:
        return _erro(erro)

    limite = _como_inteiro(request.args.get('limite', '100'))
    if limite is None or not 1 <= limite <= 500:
        return _erro("O limite deve estar entre 1 e 500.")
    parametros.append(limite)

    consulta = f"""
        SELECT t.id, t.tipo, t.valor, t.descricao, t.data_transacao,
               t.categoria_id, c.nome AS categoria,
               t.animal_id, a.nome AS animal,
               t.origem_tipo, t.origem_id, t.campanha_id
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
        "campanha_id": l.get('campanha_id'),
    } for l in linhas])


@financas_bp.route('/api/financas/resumo')
@api_login_required
def resumo_financeiro():
    condicoes, parametros, erro = _montar_filtros()
    if erro:
        return _erro(erro)

    consulta = f"""
        SELECT c.id AS categoria_id, c.nome AS categoria, t.tipo,
               SUM(t.valor) AS total, COUNT(*) AS quantidade
        FROM transacoes t
        JOIN categorias c ON c.id = t.categoria_id
        WHERE {' AND '.join(condicoes)}
        GROUP BY c.id, c.nome, t.tipo
        ORDER BY total DESC
    """

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(consulta, parametros)
            linhas = cursor.fetchall()
    finally:
        conexao.close()

    zero = Decimal('0.00')
    receitas = sum((l['total'] for l in linhas if l['tipo'] == 'RECEITA'), zero)
    despesas = sum((l['total'] for l in linhas if l['tipo'] == 'DESPESA'), zero)

    return jsonify({
        "receitas": format(receitas, '.2f'),
        "despesas": format(despesas, '.2f'),
        "saldo": format(receitas - despesas, '.2f'),
        "por_categoria": [{
            "categoria_id": l['categoria_id'],
            "categoria": l['categoria'],
            "tipo": l['tipo'],
            "total": format(l['total'], '.2f'),
            "quantidade": l['quantidade'],
        } for l in linhas],
    })

@financas_bp.route('/api/financas/mensal')
@api_login_required
def resumo_mensal():
    """Totais de receitas e despesas mês a mês, para o gráfico de barras.

    Aceita os mesmos filtros do resumo. Meses sem lançamento aparecem zerados
    dentro do período, para o gráfico não "pular" meses.
    """
    condicoes, parametros, erro = _montar_filtros()
    if erro:
        return _erro(erro)

    consulta = f"""
        SELECT YEAR(t.data_transacao) AS ano, MONTH(t.data_transacao) AS numero_mes,
               t.tipo, SUM(t.valor) AS total
        FROM transacoes t
        WHERE {' AND '.join(condicoes)}
        GROUP BY YEAR(t.data_transacao), MONTH(t.data_transacao), t.tipo
        ORDER BY ano, numero_mes
    """

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(consulta, parametros)
            linhas = cursor.fetchall()
    finally:
        conexao.close()

    zero = Decimal('0.00')
    totais = {}
    for l in linhas:
        mes = totais.setdefault((l['ano'], l['numero_mes']), {'RECEITA': zero, 'DESPESA': zero})
        mes[l['tipo']] = l['total']

    # Intervalo de meses: o período pedido ou, sem ele, do primeiro ao último lançamento.
    inicio, _ = _ler_data('inicio')
    fim, _ = _ler_data('fim')
    meses_com_dados = sorted(totais)
    primeiro = (inicio.year, inicio.month) if inicio else (meses_com_dados[0] if meses_com_dados else None)
    ultimo = (fim.year, fim.month) if fim else (meses_com_dados[-1] if meses_com_dados else primeiro)
    if primeiro is None:
        return jsonify([])

    resultado = []
    ano, numero_mes = primeiro
    while (ano, numero_mes) <= ultimo and len(resultado) < MESES_MAXIMOS:
        mes = totais.get((ano, numero_mes), {'RECEITA': zero, 'DESPESA': zero})
        resultado.append({
            "mes": f"{ano:04d}-{numero_mes:02d}",
            "receitas": format(mes['RECEITA'], '.2f'),
            "despesas": format(mes['DESPESA'], '.2f'),
        })
        numero_mes += 1
        if numero_mes > 12:
            ano, numero_mes = ano + 1, 1

    return jsonify(resultado)

# ==========================================
# ROTAS DO MÓDULO DE CAMPANHAS
# ==========================================

@financas_bp.route('/campanhas/nova')
@login_required
def pagina_nova_campanha():
    """Renderiza o formulário de criação de campanhas com os animais da conta logada."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome FROM animais WHERE usuario_id = %s ORDER BY nome ASC",
                (session['id_usuario'],)
            )
            animais = cursor.fetchall()
    finally:
        conexao.close()
    return render_template('campanha.html', animais=animais)


@financas_bp.route('/api/campanhas', methods=['POST'])
@api_login_required
def criar_campanha():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return _erro("Envie os dados em formato JSON.")

    titulo = str(dados.get('titulo', '')).strip()
    if not titulo or len(titulo) > 150:
        return _erro("O título é obrigatório e deve ter até 150 caracteres.")

    descricao = str(dados.get('descricao', '')).strip()
    if not descricao:
        return _erro("A descrição da campanha é obrigatória.")

    try:
        meta = Decimal(str(dados.get('meta', '')).strip().replace(',', '.'))
    except InvalidOperation:
        return _erro("Meta inválida.")
    if not meta.is_finite() or meta <= 0:
        return _erro("A meta deve ser maior que zero.")
    if meta > VALOR_MAXIMO:
        return _erro("Meta acima do valor permitido.")
    meta = meta.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Animal vinculado (opcional)
    animal_id = None
    if dados.get('animal_id') not in (None, ''):
        animal_id = _como_inteiro(dados.get('animal_id'))
        if animal_id is None or not animal_do_usuario(animal_id):
            return _erro("Animal não encontrado ou não pertence ao usuário.", 404)

    foto_url = dados.get('foto_url')
    if foto_url:
        foto_url = str(foto_url).strip() or None

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO campanhas (usuario_id, animal_id, titulo, descricao, meta, foto_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'ativa')
                """,
                (session['id_usuario'], animal_id, titulo, descricao, meta, foto_url)
            )
            nova_campanha_id = cursor.lastrowid
        conexao.commit()
        return jsonify({
            "id": nova_campanha_id,
            "titulo": titulo,
            "meta": str(meta),
            "status": "ativa"
        }), 201
    except Exception:
        conexao.rollback()
        current_app.logger.exception("Erro ao criar campanha")
        return _erro("Não foi possível salvar a campanha.", 500)
    finally:
        conexao.close()


@financas_bp.route('/api/campanhas')
@api_login_required
def listar_campanhas_usuario():
    """Lista as campanhas criadas pela organização logada."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id, c.titulo, c.descricao, c.meta, c.arrecadado,
                       c.foto_url, c.status, c.criado_em,
                       c.animal_id, a.nome AS nome_animal
                FROM campanhas c
                LEFT JOIN animais a ON a.id = c.animal_id
                WHERE c.usuario_id = %s
                ORDER BY c.id DESC
                """,
                (session['id_usuario'],)
            )
            campanhas = cursor.fetchall()
    finally:
        conexao.close()

    return jsonify([{
        "id": c['id'],
        "titulo": c['titulo'],
        "descricao": c['descricao'],
        "meta": str(c['meta']),
        "arrecadado": str(c['arrecadado']),
        "foto_url": c['foto_url'],
        "status": c['status'],
        "criado_em": c['criado_em'].strftime('%Y-%m-%d %H:%M:%S') if c.get('criado_em') else None,
        "animal_id": c['animal_id'],
        "nome_animal": c['nome_animal'],
    } for c in campanhas])


@financas_bp.route('/api/campanhas/<int:campanha_id>/doar', methods=['POST'])
@api_login_required
def registrar_doacao_campanha(campanha_id):
    """
    Registra uma doação financeira para a campanha:
    1. Atualiza o montante arrecadado na tabela 'campanhas'.
    2. Registra a entrada como 'RECEITA' na tabela 'transacoes' (origem_tipo='CAMPANHA').
    """
    dados = request.get_json(silent=True) or {}
    try:
        valor = Decimal(str(dados.get('valor', '')).strip().replace(',', '.'))
    except InvalidOperation:
        return _erro("Valor inválido.")
    if not valor.is_finite() or valor <= 0:
        return _erro("O valor da doação deve ser positivo.")
    valor = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    data_transacao = date.today()
    if dados.get('data_transacao'):
        try:
            data_transacao = date.fromisoformat(str(dados['data_transacao']))
        except ValueError:
            return _erro("Data inválida. Use AAAA-MM-DD.")

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            # Verifica existência e permissão da campanha
            cursor.execute(
                """
                SELECT id, usuario_id, animal_id, titulo, status 
                FROM campanhas 
                WHERE id = %s AND usuario_id = %s
                """,
                (campanha_id, session['id_usuario'])
            )
            campanha = cursor.fetchone()
            if not campanha:
                return _erro("Campanha não encontrada.", 404)
            if campanha['status'] != 'ativa':
                return _erro("Esta campanha não está mais ativa para receber doações.")

            # Busca ID da categoria 'Doação via Campanha'
            cursor.execute(
                "SELECT id FROM categorias WHERE tipo = 'RECEITA' AND nome = 'Doação via Campanha' LIMIT 1"
            )
            categoria = cursor.fetchone()
            if not categoria:
                # Fallback caso a migration não tenha rodado
                cursor.execute(
                    "SELECT id FROM categorias WHERE tipo = 'RECEITA' LIMIT 1"
                )
                categoria = cursor.fetchone()

            # 1. Incrementa total da campanha
            cursor.execute(
                "UPDATE campanhas SET arrecadado = arrecadado + %s WHERE id = %s",
                (valor, campanha_id)
            )

            # 2. Insere a transação no livro-caixa
            cursor.execute(
                """
                INSERT INTO transacoes
                (usuario_id, animal_id, categoria_id, tipo, valor, descricao, data_transacao, origem_tipo, origem_id, campanha_id)
                VALUES (%s, %s, %s, 'RECEITA', %s, %s, %s, 'CAMPANHA', %s, %s)
                """,
                (
                    session['id_usuario'],
                    campanha['animal_id'],
                    categoria['id'],
                    valor,
                    f"Doação para campanha: {campanha['titulo']}",
                    data_transacao,
                    campanha_id,
                    campanha_id
                )
            )
            transacao_id = cursor.lastrowid

        conexao.commit()
        return jsonify({
            "mensagem": "Doação registrada com sucesso!",
            "transacao_id": transacao_id,
            "campanha_id": campanha_id,
            "valor": str(valor)
        }), 201
    except Exception:
        conexao.rollback()
        current_app.logger.exception("Erro ao registrar doação para campanha")
        return _erro("Não foi possível registrar a doação.", 500)
    finally:
        conexao.close()


# ==========================================
# PÁGINA PRINCIPAL DE FINANÇAS
# ==========================================

@financas_bp.route('/financas')
@login_required
def pagina_financas():
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome FROM animais WHERE usuario_id = %s ORDER BY nome",
                (session['id_usuario'],)
            )
            animais = cursor.fetchall()
    finally:
        conexao.close()
    return render_template('financas.html', animais=animais)



# ==========================================
# DOAÇÕES INFORMADAS PELOS VISITANTES
# ==========================================

@financas_bp.route('/api/financas/doacoes-pendentes')
@api_login_required
def listar_doacoes_pendentes():
    """Avisos de doação ainda não analisados, das campanhas do usuário logado."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.id, d.valor, UNIX_TIMESTAMP(d.criado_em) AS informado_em,
                       c.id AS campanha_id, c.titulo
                FROM doacoes_informadas d
                JOIN campanhas c ON c.id = d.campanha_id
                WHERE c.usuario_id = %s AND d.status = 'pendente'
                ORDER BY d.criado_em DESC
                """,
                (session['id_usuario'],)
            )
            linhas = cursor.fetchall()
    finally:
        conexao.close()

    return jsonify([{
        "id": l['id'],
        "valor": str(l['valor']),
        "informado_em": int(l['informado_em']),
        "campanha_id": l['campanha_id'],
        "campanha": l['titulo'],
    } for l in linhas])


@financas_bp.route('/api/financas/doacoes-pendentes/<int:doacao_id>/confirmar', methods=['POST'])
@api_login_required
def confirmar_doacao_informada(doacao_id):
    """Confirma o recebimento: soma no arrecadado e lança em Receitas > Doação via Campanha."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            # Trava o aviso para não ser confirmado duas vezes ao mesmo tempo
            cursor.execute(
                """
                SELECT d.id, d.valor, c.id AS campanha_id, c.titulo, c.animal_id
                FROM doacoes_informadas d
                JOIN campanhas c ON c.id = d.campanha_id
                WHERE d.id = %s AND c.usuario_id = %s AND d.status = 'pendente'
                FOR UPDATE
                """,
                (doacao_id, session['id_usuario'])
            )
            doacao = cursor.fetchone()
            if doacao is None:
                conexao.rollback()
                return _erro("Doação não encontrada ou já analisada.", 404)

            cursor.execute(
                "SELECT id FROM categorias WHERE tipo = 'RECEITA' AND nome = 'Doação via Campanha' LIMIT 1"
            )
            categoria = cursor.fetchone()
            if categoria is None:
                raise RuntimeError("Categoria 'Doação via Campanha' não encontrada.")

            cursor.execute(
                "UPDATE campanhas SET arrecadado = arrecadado + %s WHERE id = %s",
                (doacao['valor'], doacao['campanha_id'])
            )
            # origem_id fica vazio: a ligação com o aviso fica em doacoes_informadas.transacao_id
            cursor.execute(
                """
                INSERT INTO transacoes
                (usuario_id, animal_id, categoria_id, tipo, valor, descricao,
                 data_transacao, origem_tipo, campanha_id)
                VALUES (%s, %s, %s, 'RECEITA', %s, %s, %s, 'CAMPANHA', %s)
                """,
                (
                    session['id_usuario'], doacao['animal_id'], categoria['id'], doacao['valor'],
                    f"Doação para campanha: {doacao['titulo']}"[:255], date.today(), doacao['campanha_id']
                )
            )
            transacao_id = cursor.lastrowid
            cursor.execute(
                """
                UPDATE doacoes_informadas
                SET status = 'confirmada', transacao_id = %s, analisado_em = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (transacao_id, doacao_id)
            )
        conexao.commit()
        return jsonify({"mensagem": "Doação confirmada e lançada em Receitas.", "transacao_id": transacao_id})
    except Exception:
        conexao.rollback()
        current_app.logger.exception("Erro ao confirmar doação informada")
        return _erro("Não foi possível confirmar a doação.", 500)
    finally:
        conexao.close()


@financas_bp.route('/api/financas/doacoes-pendentes/<int:doacao_id>/recusar', methods=['POST'])
@api_login_required
def recusar_doacao_informada(doacao_id):
    """Marca o aviso como não recebido. Nada entra em Finanças."""
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE doacoes_informadas d
                JOIN campanhas c ON c.id = d.campanha_id
                SET d.status = 'recusada', d.analisado_em = CURRENT_TIMESTAMP
                WHERE d.id = %s AND c.usuario_id = %s AND d.status = 'pendente'
                """,
                (doacao_id, session['id_usuario'])
            )
            alterados = cursor.rowcount
        conexao.commit()
        if alterados == 0:
            return _erro("Doação não encontrada ou já analisada.", 404)
        return jsonify({"mensagem": "Doação marcada como não recebida."})
    except Exception:
        conexao.rollback()
        current_app.logger.exception("Erro ao recusar doação informada")
        return _erro("Não foi possível atualizar a doação.", 500)
    finally:
        conexao.close()
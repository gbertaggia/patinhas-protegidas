from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from flask import Blueprint, current_app, jsonify, request
from database.connection import conectar_banco

publico_bp = Blueprint('publico', __name__)

VALORES_DOACAO = [5, 10, 20, 50]
FOTO_PADRAO = 'https://dummyimage.com/600x400/e9ecef/6c757d.png&text=Sem+foto'
ICONE_PADRAO = '🐾'


def _regiao(cidade, uf):
    return f'{cidade}, {uf}' if cidade and uf else ''


@publico_bp.route('/api/publico/dados')
def dados_publicos():
    """
    Animais divulgados para adoção e campanhas ativas, agrupados por organização/protetor.
    Lê diretamente do banco de dados (MySQL).
    """
    try:
        conexao = conectar_banco()
        try:
            with conexao.cursor() as cursor:
                # 1. Consulta dos animais disponíveis
                cursor.execute(
                    """
                    SELECT a.id, a.nome, a.especie, a.raca, a.idade, a.foto_url, a.castrado,
                           a.info_saude,
                           (a.chip IS NOT NULL AND a.chip <> '') AS tem_chip,
                           EXISTS(SELECT 1 FROM vacinas v
                                  WHERE v.animal_id = a.id AND v.status_vacina = 'aplicada') AS vacinado,
                           u.id AS usuario_id, u.nome AS nome_usuario, u.tipo, u.cidade, u.uf,
                           u.logo_url, u.link_formulario_adocao, u.missao
                    FROM animais a
                    JOIN usuarios u ON u.id = a.usuario_id
                    WHERE a.visivel_publico = 1
                    ORDER BY u.nome, u.id, a.id DESC
                    """
                )
                linhas_animais = cursor.fetchall()

                # 2. Consulta das campanhas ativas
                cursor.execute(
                    """
                    SELECT c.id, c.usuario_id, c.animal_id, c.titulo, c.descricao,
                           c.meta, c.arrecadado, c.foto_url,
                           u.tipo AS usuario_tipo, u.chave_pix,
                           u.nome AS nome_usuario, u.cidade AS cidade_usuario
                    FROM campanhas c
                    JOIN usuarios u ON u.id = c.usuario_id
                    WHERE c.status = 'ativa'
                    ORDER BY c.id DESC
                    """
                )
                linhas_campanhas = cursor.fetchall()
        finally:
            conexao.close()
    except Exception:
        current_app.logger.exception("Erro ao carregar os dados públicos")
        return jsonify({"erro": "Não foi possível carregar os dados agora."}), 500

    ongs = {}
    independentes = {
        'id': 0,
        'nome': 'Protetores independentes',
        'icone': ICONE_PADRAO,
        'logoUrl': None,
        'regiao': 'Vários locais',
        'cidade': '',
        'estado': '',
        'resumo': 'Animais divulgados por protetores e protetoras independentes.',
        'descricao': 'Pessoas que cuidam de animais por conta própria. Os nomes individuais não são divulgados.',
        'linkFormulario': None,
        'animais': [],
        'campanhas': [],
    }

    # Processamento dos animais
    for linha in linhas_animais:
        animal = {
            'id': linha['id'],
            'nome': linha['nome'],
            'especie': linha['especie'],
            'raca': linha['raca'] or '',
            'idade': linha['idade'] or '',
            'foto': linha['foto_url'] or FOTO_PADRAO,
            'castrado': bool(linha['castrado']),
            'temChip': bool(linha['tem_chip']),
            'vacinado': bool(linha['vacinado']),
            'infoSaude': linha['info_saude'] or '',
            'cidade': linha['cidade'] or '',
            'estado': linha['uf'] or '',
        }

        link_form = (linha.get('link_formulario_adocao') or '').strip() or None
        logo_url = (linha.get('logo_url') or '').strip() or None
        missao = (linha.get('missao') or '').strip()

        if linha['tipo'] == 'ONG':
            regiao = _regiao(linha['cidade'], linha['uf'])
            ong = ongs.setdefault(linha['usuario_id'], {
                'id': linha['usuario_id'],
                'nome': linha['nome_usuario'],
                'icone': ICONE_PADRAO,
                'logoUrl': logo_url,
                'regiao': regiao,
                'cidade': linha['cidade'] or '',
                'estado': linha['uf'] or '',
                'resumo': f'ONG em {regiao}' if regiao else 'ONG parceira',
                'descricao': missao,
                'linkFormulario': link_form,
                'animais': [],
                'campanhas': [],
            })
            ong['animais'].append(animal)
        else:
            if logo_url and not independentes['logoUrl']:
                independentes['logoUrl'] = logo_url
            if link_form and not independentes['linkFormulario']:
                independentes['linkFormulario'] = link_form

            independentes['animais'].append(animal)

    # Processamento e alocação das campanhas
    for camp in linhas_campanhas:
        campanha_item = {
            'id': camp['id'],
            'titulo': camp['titulo'],
            'descricao': camp['descricao'],
            'meta': float(camp['meta']),
            'arrecadado': float(camp['arrecadado']),
            'foto': camp['foto_url'] or FOTO_PADRAO,
            'animalId': camp['animal_id'],
            'chavePix': camp['chave_pix'],
            # ONG mostra o nome; protetor independente não tem o nome divulgado
            'recebedor': camp['nome_usuario'] if camp['usuario_tipo'] == 'ONG' else 'Protetor(a) independente',
            'cidade': camp['cidade_usuario'] or '',
        }

        usuario_id = camp['usuario_id']

        if camp['usuario_tipo'] == 'ONG':
            # Se a ONG já existe no dicionário (pois possui animais cadastrados)
            if usuario_id in ongs:
                ongs[usuario_id]['campanhas'].append(campanha_item)
            else:
                # Caso a ONG ainda não tenha animais divulgados, mas tenha campanha ativa
                pass
        else:
            independentes['campanhas'].append(campanha_item)

    lista = list(ongs.values())
    if independentes['animais'] or independentes['campanhas']:
        lista.append(independentes)

    return jsonify({'valoresDoacao': VALORES_DOACAO, 'ongs': lista})



# Proteções do aviso de doação (rota aberta, sem login)
VALOR_MAXIMO_DOACAO = Decimal('100000.00')
LIMITE_PENDENTES_POR_CAMPANHA = 30


@publico_bp.route('/api/publico/campanhas/<int:campanha_id>/doacao-informada', methods=['POST'])
def informar_doacao(campanha_id):
    """O visitante avisa que fez um Pix para a campanha.

    Não mexe no arrecadado nem em Finanças: só cria um aviso pendente,
    que o dono da campanha confirma (ou não) na tela de Finanças.
    """
    dados = request.get_json(silent=True) or {}
    try:
        valor = Decimal(str(dados.get('valor', '')).strip().replace(',', '.'))
    except InvalidOperation:
        return jsonify({"erro": "Valor inválido."}), 400
    if not valor.is_finite() or valor <= 0 or valor > VALOR_MAXIMO_DOACAO:
        return jsonify({"erro": "Informe um valor entre R$ 0,01 e R$ 100.000,00."}), 400
    valor = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM campanhas WHERE id = %s AND status = 'ativa'",
                (campanha_id,)
            )
            if cursor.fetchone() is None:
                return jsonify({"erro": "Campanha não encontrada ou encerrada."}), 404

            # Evita que alguém encha a lista de avisos falsos
            cursor.execute(
                "SELECT COUNT(*) AS total FROM doacoes_informadas WHERE campanha_id = %s AND status = 'pendente'",
                (campanha_id,)
            )
            if cursor.fetchone()['total'] >= LIMITE_PENDENTES_POR_CAMPANHA:
                return jsonify({"erro": "Esta campanha já tem muitas doações aguardando confirmação. Tente mais tarde."}), 429

            cursor.execute(
                "INSERT INTO doacoes_informadas (campanha_id, valor) VALUES (%s, %s)",
                (campanha_id, valor)
            )
        conexao.commit()
        return jsonify({"mensagem": "Quem organizou a campanha vai conferir e confirmar o recebimento."}), 201
    except Exception:
        conexao.rollback()
        current_app.logger.exception("Erro ao registrar doação informada")
        return jsonify({"erro": "Não foi possível registrar agora. Tente de novo."}), 500
    finally:
        conexao.close()
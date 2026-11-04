
from flask import Blueprint, current_app, jsonify
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
    Animais divulgados para adoção agrupados por organização/protetor.
    Lê diretamente do banco de dados (MySQL).
    """
    try:
        conexao = conectar_banco()
        try:
            with conexao.cursor() as cursor:
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
                linhas = cursor.fetchall()
        finally:
            conexao.close()
    except Exception:
        current_app.logger.exception("Erro ao carregar os dados públicos")
        return jsonify({"erro": "Não foi possível carregar os animais agora."}), 500

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

    for linha in linhas:
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

        # Link próprio cadastrado (vazio vira None)
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
            # Caso seja protetor independente e tenha configurado logo ou formulário
            if logo_url and not independentes['logoUrl']:
                independentes['logoUrl'] = logo_url
            if link_form and not independentes['linkFormulario']:
                independentes['linkFormulario'] = link_form

            independentes['animais'].append(animal)

    lista = list(ongs.values())
    if independentes['animais']:
        lista.append(independentes)

    return jsonify({'valoresDoacao': VALORES_DOACAO, 'ongs': lista})
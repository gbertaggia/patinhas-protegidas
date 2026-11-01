from flask import Blueprint, current_app, jsonify

from database.connection import conectar_banco

publico_bp = Blueprint('publico', __name__)

# Valores sugeridos nos botões de doação da página pública
VALORES_DOACAO = [5, 10, 20, 50]

# Formulário externo (Google Forms) para quem quer adotar ou apadrinhar
LINK_FORMULARIO = (
    'https://docs.google.com/forms/d/e/'
    '1FAIpQLSe5xhUYgMcGLOS_Fx-n2urv-4qtMcew3ykvceASDmMdlRqSqA/viewform?usp=publish-editor'
)

FOTO_PADRAO = 'https://dummyimage.com/600x400/e9ecef/6c757d.png&text=Sem+foto'
ICONE = '🐾'


def _regiao(cidade, uf):
    return f'{cidade}, {uf}' if cidade and uf else ''


@publico_bp.route('/api/publico/dados')
def dados_publicos():
    """
    Animais divulgados para adoção, agrupados por ONG. Rota aberta (sem login):
    devolve só uma lista fixa de campos, sem número de chip, histórico clínico,
    contatos nem dados financeiros. Protetores independentes não têm o nome divulgado.
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
                           u.id AS usuario_id, u.nome AS nome_usuario, u.tipo, u.cidade, u.uf
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
        'icone': ICONE,
        'regiao': 'Vários locais',
        'cidade': '',
        'estado': '',
        'resumo': 'Animais divulgados por protetores e protetoras independentes.',
        'descricao': 'Pessoas que cuidam de animais por conta própria. Os nomes não são divulgados.',
        'linkFormulario': LINK_FORMULARIO,
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

        if linha['tipo'] == 'ONG':
            regiao = _regiao(linha['cidade'], linha['uf'])
            ong = ongs.setdefault(linha['usuario_id'], {
                'id': linha['usuario_id'],
                'nome': linha['nome_usuario'],
                'icone': ICONE,
                'regiao': regiao,
                'cidade': linha['cidade'] or '',
                'estado': linha['uf'] or '',
                'resumo': f'ONG em {regiao}' if regiao else 'ONG parceira',
                'descricao': '',
                'linkFormulario': LINK_FORMULARIO,
                'animais': [],
                'campanhas': [],
            })
            ong['animais'].append(animal)
        else:
            independentes['animais'].append(animal)

    lista = list(ongs.values())
    if independentes['animais']:
        lista.append(independentes)

    return jsonify({'valoresDoacao': VALORES_DOACAO, 'ongs': lista})
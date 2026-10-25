from flask import Blueprint, render_template, request, session, redirect, abort, current_app
import pymysql
from database.connection import conectar_banco
from utils.auth import login_required, animal_do_usuario

# Blueprint dos animais e do painel do usuário
bp = Blueprint('animais', __name__)


@bp.route('/cadastro_animal')
@login_required
def tela_cadastro_pet():
    # Renderiza a interface de registro de animais
    return render_template('cadastroAnimal.html')


@bp.route('/pagina_animal/<int:id_animal>')
@login_required
def pagina_animal(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    # Busca animal
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    # Busca vacinas
    cursor.execute("SELECT * FROM vacinas WHERE animal_id = %s", (id_animal,))
    vacinas = cursor.fetchall()
    # Formata a data das vacinas para DD/MM/AAAA
    for v in vacinas:
        if v['data_vacina']:
            v['data_formatada'] = v['data_vacina'].strftime('%d/%m/%Y')

    # Busca medicamentos
    cursor.execute("SELECT * FROM medicamentos WHERE animal_id = %s", (id_animal,))
    medicamentos = cursor.fetchall()

    # Busca as consultas do animal
    cursor.execute("SELECT * FROM consultas WHERE animal_id = %s", (id_animal,))
    consultas = cursor.fetchall()

    # Formata data e hora para o padrão brasileiro
    for c in consultas:
        if c['data_consulta']:
            # Transforma AAAA-MM-DD em DD/MM/AAAA
            c['data_formatada'] = c['data_consulta'].strftime('%d/%m/%Y')
        if c['hora_consulta']:
            # Pega apenas os 5 primeiros caracteres (ex: de "14:00:00" para "14:00")
            c['hora_formatada'] = str(c['hora_consulta'])[:5]

    # Busca o histórico veterinário do animal
    cursor.execute("SELECT * FROM historico_veterinario WHERE animal_id = %s", (id_animal,))
    historico_medico = cursor.fetchall()

    # Formata a data do histórico para o padrão brasileiro
    for h in historico_medico:
        if h['data_registro']:
            h['data_formatada'] = h['data_registro'].strftime('%d/%m/%Y')

    cursor.close()
    conexao.close()

    return render_template(
        'paginaAnimal.html',
        animal=animal,
        vacinas=vacinas,
        medicamentos=medicamentos,
        consultas=consultas,
        historico_medico=historico_medico
    )


@bp.route('/cadastrar_animal', methods=['POST'])
@login_required
def cadastrar_animal():
    """
    Persiste um novo registro de animal vinculado ao ID do usuário autenticado.
    """
    id_protetor = session['id_usuario']

    # --- TRATAMENTO DE CAMPOS VAZIOS (Converte '' para None/NULL) ---
    foto_animal = request.form.get('foto-pet') if request.form.get('foto-pet') else None
    nome_animal = request.form.get('nome')
    especie_animal = request.form.get('especie')
    idade_animal = request.form.get('idade') if request.form.get('idade') else None
    raca_animal = request.form.get('raca') if request.form.get('raca') else 'SRD'

    # Captura o valor exato que veio do formulário de cadastro
    valor_castrado = str(request.form.get('castrado')).lower()
    # Só salva como 1 se o valor for explicitamente '1', 'sim', 'true' ou 'on'
    castrado = 1 if valor_castrado in ['1', 'sim', 'true', 'on'] else 0

    data_castracao = request.form.get('data') if request.form.get('data') else None
    chip_identificacao = request.form.get('chip') if request.form.get('chip') else None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = """
            INSERT INTO animais
            (usuario_id, nome, especie, raca, idade, foto_url, castrado, data_castracao, chip)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        valores = (id_protetor, nome_animal, especie_animal, raca_animal,
                   idade_animal, foto_animal, castrado, data_castracao, chip_identificacao)

        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        erro_str = str(e)
        # Verifica se o erro é o código 1062 de duplicidade referente ao chip
        if "1062" in erro_str and "chip" in erro_str:
            return "<script>alert('⚠️ Ops! Já existe um animal cadastrado com este número de chip. Verifique o número e tente novamente.'); window.history.back();</script>"

        # Qualquer outro erro: detalhes só no log, mensagem genérica para o usuário
        current_app.logger.exception("Erro ao salvar animal")
        return "<script>alert('Erro ao salvar o animal. Tente novamente.'); window.history.back();</script>"


@bp.route('/deletar_animal/<int:id_animal>')
@login_required
def deletar_animal(id_animal):
    """
    Remove um registro de animal (vacinas, consultas etc. saem juntos, por cascata no banco).
    Garante que apenas o dono do registro possa excluí-lo.
    """
    id_protetor = session['id_usuario']

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Validação de segurança: confirma se o animal pertence ao usuário logado
        cursor.execute("SELECT id FROM animais WHERE id = %s AND usuario_id = %s", (id_animal, id_protetor))
        animal_valido = cursor.fetchone()

        if animal_valido:
            cursor.execute("DELETE FROM animais WHERE id = %s", (id_animal,))
            conexao.commit()

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        current_app.logger.exception("Erro ao excluir animal")
        return "<h1>Erro ao excluir o animal. Tente novamente.</h1>"


@bp.route('/editar_animal/<int:id_animal>')
@login_required
def carregar_edicao_animal(id_animal):
    """
    Consulta o registro específico de um animal e renderiza o formulário de atualização pré-preenchido.
    """
    id_protetor = session['id_usuario']

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "SELECT * FROM animais WHERE id = %s AND usuario_id = %s"
        valores = (id_animal, id_protetor)

        cursor.execute(comando_sql, valores)
        animal_para_editar = cursor.fetchone()

        cursor.close()
        conexao.close()

        if not animal_para_editar:
            return "<h1>Registro não localizado ou acesso negado.</h1>"

        return render_template('editar_animal.html', animal=animal_para_editar)

    except Exception as e:
        current_app.logger.exception("Erro ao carregar animal para edição")
        return "<h1>Erro ao carregar o animal.</h1>"


@bp.route('/salvar_edicao/<int:id_animal>', methods=['POST'])
@login_required
def salvar_edicao_animal(id_animal):
    id_protetor = session['id_usuario']

    # Pegando todos os campos do HTML
    novo_nome = request.form.get('nome')
    nova_especie = request.form.get('especie')
    nova_idade = request.form.get('idade') if request.form.get('idade') else None
    nova_raca = request.form.get('raca')
    nova_foto = request.form.get('foto-pet') if request.form.get('foto-pet') else None

    novo_chip = request.form.get('chip') if request.form.get('chip') else None
    # O formulário envia '1' (Sim) ou '0' (Não): só '1', 'sim', 'true' ou 'on' contam como castrado
    valor_castrado = str(request.form.get('castrado')).lower()
    castrado = 1 if valor_castrado in ['1', 'sim', 'true', 'on'] else 0
    # Sem castração, não guarda data
    data_castracao = request.form.get('data') if (castrado and request.form.get('data')) else None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = """
            UPDATE animais
            SET nome = %s, especie = %s, idade = %s, raca = %s, foto_url = %s,
                chip = %s, castrado = %s, data_castracao = %s
            WHERE id = %s AND usuario_id = %s
        """

        valores = (novo_nome, nova_especie, nova_idade, nova_raca, nova_foto,
                   novo_chip, castrado, data_castracao, id_animal, id_protetor)

        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect(f'/pagina_animal/{id_animal}')

    except Exception as e:
        erro_str = str(e)
        if "1062" in erro_str and "chip" in erro_str:
            return "<script>alert('⚠️ Ops! Este número de chip já está vinculado a outro animal no sistema. Verifique o código e tente novamente.'); window.history.back();</script>"

        current_app.logger.exception("Erro na atualização do animal")
        return "<script>alert('Erro ao atualizar o animal. Tente novamente.'); window.history.back();</script>"


@bp.route('/painel')
@login_required
def painel():
    """
    Interface principal do usuário. Consulta a base de dados para retornar
    exclusivamente os animais vinculados à sessão ativa.
    """
    email_do_usuario = session['usuario_logado']
    id_protetor = session['id_usuario']

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "SELECT * FROM animais WHERE usuario_id = %s"
        valores = (id_protetor,)

        cursor.execute(comando_sql, valores)
        lista_animais = cursor.fetchall()

        cursor.close()
        conexao.close()

        return render_template('painel.html', email=email_do_usuario, animais=lista_animais)

    except Exception as e:
        current_app.logger.exception("Erro ao carregar o painel")
        return "<h1>Erro ao carregar o painel. Tente novamente.</h1>"
from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app
import pymysql
from database.connection import conectar_banco
from utils.auth import login_required, animal_do_usuario, registro_do_usuario

# Blueprint da área de saúde: vacinas, medicamentos, consultas e histórico veterinário
bp = Blueprint('saude', __name__)


# --------------------------------------------------------------------------------#
# VACINAS
@bp.route('/animal/<int:id_animal>/vacina')
@login_required
def cadastro_vacina(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    # Busca o animal pelo ID que veio na URL
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    # Envia o objeto 'animal' para o template
    return render_template('cadastroVacinas.html', animal=animal, id_animal=id_animal)


@bp.route('/salvar_vacina/<int:id_animal>', methods=['POST'])
@login_required
def salvar_vacina(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    try:
        nome_vacina = (
            request.form.get('nome_vacina_outra')
            if request.form.get('vacina') == 'outros'
            else request.form.get('vacina')
        )
        data_vacina = request.form.get('data_vacina')
        status_vacina = request.form.get('status_vacina')
        dose_vacina = request.form.get('dose')

        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO vacinas
            (animal_id, nome_vacina, data_vacina, status_vacina, dose_vacina)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_animal, nome_vacina, data_vacina, status_vacina, dose_vacina)
        )
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect(f'/pagina_animal/{id_animal}')
    except Exception:
        current_app.logger.exception("Erro ao salvar vacina")
        return "<h1>Erro ao salvar vacina.</h1>"


@bp.route('/deletar_vacina/<int:id_vacina>/<int:id_animal>')
@login_required
def deletar_vacina(id_vacina, id_animal):
    if not registro_do_usuario('vacinas', id_vacina, id_animal):
        abort(404)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM vacinas WHERE id = %s", (id_vacina,))
        conexao.commit()
        cursor.close()
        conexao.close()
        return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
    except Exception:
        current_app.logger.exception("Erro ao deletar vacina")
        return "<h1>Erro ao deletar vacina.</h1>"


@bp.route('/editar_vacina/<int:id_vacina>/<int:id_animal>', methods=['GET', 'POST'])
@login_required
def editar_vacina(id_vacina, id_animal):
    if not registro_do_usuario('vacinas', id_vacina, id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        # Mantém a mesma inteligência do cadastro para o campo "Outros..."
        nome_vacina = (
            request.form.get('nome_vacina_outra')
            if request.form.get('vacina') == 'outros'
            else request.form.get('vacina')
        )
        data_vacina = request.form.get('data_vacina')
        status_vacina = request.form.get('status_vacina')
        dose_vacina = request.form.get('dose')

        try:
            sql = """
                UPDATE vacinas
                SET nome_vacina=%s, data_vacina=%s, status_vacina=%s, dose_vacina=%s
                WHERE id=%s
            """
            cursor.execute(sql, (nome_vacina, data_vacina, status_vacina, dose_vacina, id_vacina))
            conexao.commit()
            return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
        except Exception:
            current_app.logger.exception("Erro ao atualizar vacina")
            return "<h1>Erro ao atualizar vacina.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Se for GET, busca os dados para preencher a tela
    cursor.execute("SELECT * FROM vacinas WHERE id = %s", (id_vacina,))
    vacina = cursor.fetchone()

    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('editarVacina.html', vacina=vacina, animal=animal)


# --------------------------------------------------------------------------------#
# MEDICAÇÃO
@bp.route('/animal/<int:id_animal>/medicamentos')
@login_required
def cadastro_medicamento(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    # Busca o animal para ter acesso aos dados dele no template
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('cadastroMedicacao.html', animal=animal, id_animal=id_animal)


@bp.route('/salvar_medicacao/<int:id_animal>', methods=['POST'])
@login_required
def salvar_medicacao(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    nome_med = request.form.get('medicacao')
    dose_med = request.form.get('dose_med')
    frequencia = request.form.get('frequencia')
    data_inicio = request.form.get('data_inicio')
    duracao = request.form.get('duracao')

    # Pega a lista de horários gerada pelo JS e transforma em um texto separado por vírgulas
    horarios_lista = request.form.getlist('horarios[]')
    horarios_texto = ",".join(horarios_lista)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = """
            INSERT INTO medicamentos
            (animal_id, nome_medicamento, dose_medicamento, frequencia, horarios, data_inicio_medicamento, duracao_medicamento)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (id_animal, nome_med, dose_med, frequencia, horarios_texto, data_inicio, duracao)

        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect(f'/pagina_animal/{id_animal}')
    except Exception:
        current_app.logger.exception("Erro ao salvar medicamento")
        return "<h1>Erro ao salvar medicamento.</h1>"


@bp.route('/deletar_medicacao/<int:id_medicamento>/<int:id_animal>')
@login_required
def deletar_medicacao(id_medicamento, id_animal):
    if not registro_do_usuario('medicamentos', id_medicamento, id_animal):
        abort(404)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Deleta exatamente o remédio clicado
        cursor.execute("DELETE FROM medicamentos WHERE id = %s", (id_medicamento,))
        conexao.commit()

        cursor.close()
        conexao.close()

        # Depois de deletar, atualiza a página do próprio animal
        return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
    except Exception:
        current_app.logger.exception("Erro ao deletar medicamento")
        return "<h1>Erro ao deletar medicamento.</h1>"


@bp.route('/editar_medicacao/<int:id_medicamento>')
@login_required
def carregar_edicao_medicacao(id_medicamento):
    if not registro_do_usuario('medicamentos', id_medicamento):
        abort(404)

    try:
        conexao = conectar_banco()
        # DictCursor: os dados vêm mapeados com os nomes das colunas
        cursor = conexao.cursor(pymysql.cursors.DictCursor)

        # Busca os dados do medicamento específico
        cursor.execute("SELECT * FROM medicamentos WHERE id = %s", (id_medicamento,))
        remedio = cursor.fetchone()

        cursor.close()
        conexao.close()

        if not remedio:
            return "<h1>Medicação não localizada.</h1>"

        return render_template('editar_medicacao.html', remedio=remedio)
    except Exception:
        current_app.logger.exception("Erro ao ler medicamento")
        return "<h1>Erro ao carregar o medicamento.</h1>"


@bp.route('/salvar_edicao_medicacao/<int:id_medicamento>/<int:id_animal>', methods=['POST'])
@login_required
def salvar_edicao_medicacao(id_medicamento, id_animal):
    if not registro_do_usuario('medicamentos', id_medicamento, id_animal):
        abort(404)

    # Pega os dados novos que o usuário digitou no formulário
    novo_nome = request.form.get('medicacao')
    nova_data = request.form.get('data_inicio')
    nova_duracao = request.form.get('duracao')
    nova_dose = request.form.get('dose_med')
    nova_frequencia = request.form.get('frequencia')
    novos_horarios = request.form.get('horarios_texto')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = """
            UPDATE medicamentos
            SET nome_medicamento = %s, data_inicio_medicamento = %s,
                duracao_medicamento = %s, dose_medicamento = %s,
                frequencia = %s, horarios = %s
            WHERE id = %s
        """
        valores = (novo_nome, nova_data, nova_duracao, nova_dose,
                   nova_frequencia, novos_horarios, id_medicamento)

        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect(f'/pagina_animal/{id_animal}')
    except Exception:
        current_app.logger.exception("Erro ao atualizar medicamento")
        return "<h1>Erro ao atualizar a medicação.</h1>"


# --------------------------------------------------------------------------------#
# CONSULTAS
@bp.route('/cadastrar_consulta/<int:id_animal>', methods=['GET', 'POST'])
@login_required
def cadastrar_consulta(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    # Busca os dados do animal para sabermos quem é
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    if request.method == 'POST':
        data_consulta = request.form.get('data_consulta')
        hora_consulta = request.form.get('hora_consulta') if request.form.get('hora_consulta') else None
        clinica = request.form.get('clinica')
        veterinario = request.form.get('veterinario')
        motivo = request.form.get('motivo')

        try:
            sql = """
                INSERT INTO consultas (animal_id, data_consulta, hora_consulta, clinica, veterinario, motivo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (id_animal, data_consulta, hora_consulta, clinica, veterinario, motivo)

            cursor.execute(sql, valores)
            conexao.commit()

            # Sucesso: volta para a página do animal específico
            return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
        except Exception:
            current_app.logger.exception("Erro ao inserir consulta")
            return "<h1>Erro ao salvar a consulta.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Se for GET, envia a variável animal para preencher a tela
    return render_template('cadastroConsultas.html', animal=animal)


@bp.route('/deletar_consulta/<int:id_consulta>/<int:id_animal>')
@login_required
def deletar_consulta(id_consulta, id_animal):
    if not registro_do_usuario('consultas', id_consulta, id_animal):
        abort(404)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("DELETE FROM consultas WHERE id = %s", (id_consulta,))
        conexao.commit()

        cursor.close()
        conexao.close()

        # Depois de deletar, atualiza a página do próprio animal
        return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
    except Exception:
        current_app.logger.exception("Erro ao deletar consulta")
        return "<h1>Erro ao deletar consulta.</h1>"


@bp.route('/editar_consulta/<int:id_consulta>/<int:id_animal>', methods=['GET', 'POST'])
@login_required
def editar_consulta(id_consulta, id_animal):
    if not registro_do_usuario('consultas', id_consulta, id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        # Pega os dados novos que vieram da tela
        data_consulta = request.form.get('data_consulta')
        hora_consulta = request.form.get('hora_consulta') if request.form.get('hora_consulta') else None
        clinica = request.form.get('clinica')
        veterinario = request.form.get('veterinario')
        motivo = request.form.get('motivo')

        try:
            sql = """
                UPDATE consultas
                SET data_consulta=%s, hora_consulta=%s, clinica=%s, veterinario=%s, motivo=%s
                WHERE id=%s
            """
            cursor.execute(sql, (data_consulta, hora_consulta, clinica, veterinario, motivo, id_consulta))
            conexao.commit()

            # Salva e volta para a página do animal
            return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
        except Exception:
            current_app.logger.exception("Erro ao atualizar consulta")
            return "<h1>Erro ao atualizar consulta.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Se for GET, busca os dados da consulta e do animal para preencher a tela
    cursor.execute("SELECT * FROM consultas WHERE id = %s", (id_consulta,))
    consulta = cursor.fetchone()

    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('editarConsulta.html', consulta=consulta, animal=animal)


# --------------------------------------------------------------------------------#
# HISTÓRICO VETERINÁRIO
@bp.route('/cadastrar_historico/<int:id_animal>', methods=['GET', 'POST'])
@login_required
def cadastrar_historico(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    # Busca o animal para exibir o nome na tela
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    if request.method == 'POST':
        data_registro = request.form.get('data_consulta')
        clinica = request.form.get('local')
        peso = request.form.get('peso')
        temperatura = request.form.get('temp')
        tipo_atendimento = request.form.get('motivo')
        sintomas = request.form.get('sintomas')
        diagnostico = request.form.get('diagnostico')
        tratamento = request.form.get('prescricao')
        anexo_url = request.form.get('arquivo')

        try:
            sql = """
                INSERT INTO historico_veterinario
                (animal_id, data_registro, clinica, peso, temperatura, tipo_atendimento, sintomas, diagnostico, tratamento, anexo_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (id_animal, data_registro, clinica, peso, temperatura,
                       tipo_atendimento, sintomas, diagnostico, tratamento, anexo_url)

            cursor.execute(sql, valores)
            conexao.commit()

            return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
        except Exception:
            current_app.logger.exception("Erro ao salvar histórico")
            return "<h1>Erro ao salvar o histórico.</h1>"
        finally:
            cursor.close()
            conexao.close()

    return render_template('cadastroHistorico.html', animal=animal)


@bp.route('/deletar_historico/<int:id_historico>/<int:id_animal>')
@login_required
def deletar_historico(id_historico, id_animal):
    if not registro_do_usuario('historico_veterinario', id_historico, id_animal):
        abort(404)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("DELETE FROM historico_veterinario WHERE id = %s", (id_historico,))
        conexao.commit()

        cursor.close()
        conexao.close()
        return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
    except Exception:
        current_app.logger.exception("Erro ao deletar histórico")
        return "<h1>Erro ao deletar o histórico.</h1>"


@bp.route('/editar_historico/<int:id_historico>/<int:id_animal>', methods=['GET', 'POST'])
@login_required
def editar_historico(id_historico, id_animal):
    if not registro_do_usuario('historico_veterinario', id_historico, id_animal):
        abort(404)

    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        data_registro = request.form.get('data_consulta')
        clinica = request.form.get('local')
        peso = request.form.get('peso')
        temperatura = request.form.get('temp')
        tipo_atendimento = request.form.get('motivo')
        sintomas = request.form.get('sintomas')
        diagnostico = request.form.get('diagnostico')
        tratamento = request.form.get('prescricao')
        anexo_url = request.form.get('arquivo')

        try:
            sql = """
                UPDATE historico_veterinario
                SET data_registro=%s, clinica=%s, peso=%s, temperatura=%s, tipo_atendimento=%s,
                    sintomas=%s, diagnostico=%s, tratamento=%s, anexo_url=%s
                WHERE id=%s
            """
            cursor.execute(sql, (data_registro, clinica, peso, temperatura, tipo_atendimento,
                                 sintomas, diagnostico, tratamento, anexo_url, id_historico))
            conexao.commit()
            return redirect(url_for('animais.pagina_animal', id_animal=id_animal))
        except Exception:
            current_app.logger.exception("Erro ao atualizar histórico")
            return "<h1>Erro ao atualizar o histórico.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Método GET: busca os dados para preencher a tela de edição
    cursor.execute("SELECT * FROM historico_veterinario WHERE id = %s", (id_historico,))
    historico = cursor.fetchone()

    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('editarHistorico.html', historico=historico, animal=animal)
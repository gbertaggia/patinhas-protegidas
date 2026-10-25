from flask import Flask, render_template, request, session, redirect, url_for, abort
from database.connection import conectar_banco
import pymysql
from utils.auth import login_required, animal_do_usuario, registro_do_usuario
import config
from routes.auth import bp as auth_bp


app = Flask(__name__)  # Instancia a aplicação web Flask

# Chave criptográfica necessária para o gerenciamento de estado (sessões HTTP)
app.secret_key = config.SECRET_KEY
app.register_blueprint(auth_bp)
# --------------------------------------------------------------------------------#

#PÁGINA PÚBLICA
@app.route("/")
def pagina_publica():
    return render_template("publico.html")

# ROTAS DE RENDERIZAÇÃO 

@app.route('/cadastro_animal')
@login_required
def tela_cadastro_pet():    
    # Renderiza a interface de registro de animais
    return render_template('cadastroAnimal.html')

#--------------------------------------------------------------------------------#

#PÁGINA ANIMAL
@app.route('/pagina_animal/<int:id_animal>')
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
   
    # Busca as consultas pelo nome do pet
    cursor.execute("SELECT * FROM consultas WHERE animal_id = %s", (id_animal,))
    consultas = cursor.fetchall()

    # Formata data e hora para o padrão DD/MM/AAAA
    for c in consultas:
        if c['data_consulta']:
            # Transforma AAAA-MM-DD em DD/MM/AAAA
            c['data_formatada'] = c['data_consulta'].strftime('%d/%m/%Y')
        if c['hora_consulta']:
            # Pega apenas os 5 primeiros caracteres (ex: de "14:00:00" para "14:00")
            c['hora_formatada'] = str(c['hora_consulta'])[:5]

    # Busca o histórico veterinário pelo nome do pet
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
#--------------------------------------------------------------------------------#
#CONSULTAS
@app.route('/deletar_consulta/<int:id_consulta>/<int:id_animal>')
@login_required
def deletar_consulta(id_consulta, id_animal):
    if not registro_do_usuario('consultas', id_consulta, id_animal):
        abort(404)
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "DELETE FROM consultas WHERE id = %s"
        cursor.execute(comando_sql, (id_consulta,))
        conexao.commit()

        cursor.close()
        conexao.close()

        # Depois de deletar, atualiza a página do próprio animal
        return redirect(url_for('pagina_animal', id_animal=id_animal))

    except Exception as e:
        app.logger.exception("Erro ao deletar consulta")
        return "<h1>Erro ao deletar consulta.</h1>"
    
@app.route('/editar_consulta/<int:id_consulta>/<int:id_animal>', methods=['GET', 'POST'])
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
            return redirect(url_for('pagina_animal', id_animal=id_animal))
        except Exception as e:
            app.logger.exception("Erro ao atualizar consulta")
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
#--------------------------------------------------------------------------------#
#VACINAS
@app.route('/animal/<int:id_animal>/vacina')
@login_required
def cadastro_vacina(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)
    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)
    
    # 1. Busca o animal pelo ID que veio na URL
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()
    
    cursor.close()
    conexao.close()
    
    # 2. Envia o objeto 'animal' para o template
    return render_template('cadastroVacinas.html', animal=animal, id_animal=id_animal)

@app.route('/salvar_vacina/<int:id_animal>', methods=['POST'])
@login_required
def salvar_vacina(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)
    try:
        nome_vacina = (
        request.form.get('nome_vacina_outra')
        if request.form.get('vacina') == 'outros'
        else request.form.get('vacina'))

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
        app.logger.exception("Erro ao salvar vacina")
        return "<h1>Erro ao salvar vacina.</h1>"   


@app.route('/deletar_vacina/<int:id_vacina>/<int:id_animal>')
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
        return redirect(url_for('pagina_animal', id_animal=id_animal))
    except Exception as e:
        app.logger.exception("Erro ao deletar vacina")
        return "<h1>Erro ao deletar vacina.</h1>"

@app.route('/editar_vacina/<int:id_vacina>/<int:id_animal>', methods=['GET', 'POST'])
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
            return redirect(url_for('pagina_animal', id_animal=id_animal))
        except Exception as e:
            app.logger.exception("Erro ao atualizar vacina")
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
    
#--------------------------------------------------------------------------------#
# MEDICAÇÃO
@app.route('/animal/<int:id_animal>/medicamentos')
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

@app.route('/salvar_medicacao/<int:id_animal>', methods=['POST'])
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

    except Exception as e:
        app.logger.exception("Erro ao salvar medicamento")
        return "<h1>Erro ao salvar medicamento.</h1>" 


@app.route('/deletar_medicacao/<int:id_medicamento>/<int:id_animal>')
@login_required
def deletar_medicacao(id_medicamento, id_animal):
    if not registro_do_usuario('medicamentos', id_medicamento, id_animal):
        abort(404)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # O comando SQL que vai deletar exatamente o remédio clicado
        comando_sql = """
            DELETE FROM medicamentos
            WHERE id = %s
        """

        cursor.execute(comando_sql, (id_medicamento,))
        conexao.commit()

        cursor.close()
        conexao.close()

        # Depois de deletar, atualiza a página do próprio animal
        return redirect(url_for('pagina_animal', id_animal=id_animal))

    except Exception as e:
        app.logger.exception("Erro ao deletar medicamento")
        return "<h1>Erro ao deletar medicamento.</h1>"
    
@app.route('/editar_medicacao/<int:id_medicamento>')
@login_required
def carregar_edicao_medicacao(id_medicamento):
    if not registro_do_usuario('medicamentos', id_medicamento):
        abort(404)
    try:
        conexao = conectar_banco()
        # Usamos DictCursor para os dados virem mapeados com os nomes das colunas
        cursor = conexao.cursor(pymysql.cursors.DictCursor)

        # Busca os dados do medicamento específico
        cursor.execute("SELECT * FROM medicamentos WHERE id = %s", (id_medicamento,))
        remedio = cursor.fetchone()

        cursor.close()
        conexao.close()

        if not remedio:
            return "<h1>Medicação não localizada.</h1>"

        # Abre a tela nova passando os dados do remédio
        return render_template('editar_medicacao.html', remedio=remedio)

    except Exception as e:
        app.logger.exception("Erro ao ler medicamento")
        return "<h1>Erro ao carregar o medicamento.</h1>"
    
@app.route('/salvar_edicao_medicacao/<int:id_medicamento>/<int:id_animal>', methods=['POST'])
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

    except Exception as e:
        app.logger.exception("Erro ao atualizar medicamento")
        return "<h1>Erro ao atualizar a medicação.</h1>"
    
#--------------------------------------------------------------------------------------#
# HISTÓRICO VETERINÁRIO   
 
@app.route('/cadastrar_historico/<int:id_animal>', methods=['GET', 'POST'])
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
            valores = (id_animal, data_registro, clinica, peso, temperatura, tipo_atendimento, sintomas, diagnostico, tratamento, anexo_url)

            cursor.execute(sql, valores)
            conexao.commit()
            
            return redirect(url_for('pagina_animal', id_animal=id_animal))
        except Exception as e:
            app.logger.exception("Erro ao salvar histórico")
            return "<h1>Erro ao salvar o histórico.</h1>"
        finally:
            cursor.close()
            conexao.close()

    return render_template('cadastroHistorico.html', animal=animal)

@app.route('/deletar_historico/<int:id_historico>/<int:id_animal>')
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
        return redirect(url_for('pagina_animal', id_animal=id_animal))
    except Exception as e:
        app.logger.exception("Erro ao deletar histórico")
        return "<h1>Erro ao deletar o histórico.</h1>"

@app.route('/editar_historico/<int:id_historico>/<int:id_animal>', methods=['GET', 'POST'])
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
            return redirect(url_for('pagina_animal', id_animal=id_animal))
        except Exception as e:
            app.logger.exception("Erro ao atualizar histórico")
            return "<h1>Erro ao atualizar o histórico.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Método GET: Busca os dados para preencher a tela de edição
    cursor.execute("SELECT * FROM historico_veterinario WHERE id = %s", (id_historico,))
    historico = cursor.fetchone()
    
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()
    
    cursor.close()
    conexao.close()
    
    return render_template('editarHistorico.html', historico=historico, animal=animal)

#----------------------------------------------------------------------------------------------#
# ROTAS DE PROCESSAMENTO E REGRA DE NEGÓCIO (CRUD DE ANIMAIS)
@app.route('/cadastrar_animal', methods=['POST'])
def cadastrar_animal():
    """
    Persiste um novo registro de animal vinculado ao ID do usuário autenticado.
    """
    if 'usuario_logado' not in session:
        return redirect('/login')

    id_protetor = session['id_usuario']

    # --- TRATAMENTO DE CAMPOS VAZIOS (Converte '' para None/NULL) ---
    foto_animal = request.form.get('foto-pet') if request.form.get('foto-pet') else None
    nome_animal = request.form.get('nome')
    especie_animal = request.form.get('especie')
    idade_animal = request.form.get('idade') if request.form.get('idade') else None
    raca_animal = request.form.get('raca') if request.form.get('raca') else 'SRD'

    # Captura o valor exato que veio do formulário de cadastro
    valor_castrado = str(request.form.get('castrado')).lower()
    # Só salva como 1 se o valor for explicitamente '1', 'sim' ou 'on'
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
        
        # Se for qualquer outro erro, mostra uma mensagem genérica
        app.logger.exception("Erro ao salvar animal")
        return "<script>alert('Erro ao salvar o animal. Tente novamente.'); window.history.back();</script>"


@app.route('/deletar_animal/<int:id_animal>')
def deletar_animal(id_animal):
    """
    Remove um registro de animal limpando antes suas dependências (vacinas, consultas, etc.).
    Garante que apenas o dono do registro possa excluí-lo.
    """
    if 'usuario_logado' not in session:
        return redirect('/login')

    id_protetor = session['id_usuario']

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Validação de Segurança: Confirma se o animal pertence ao usuário logado
        cursor.execute("SELECT id FROM animais WHERE id = %s AND usuario_id = %s", (id_animal, id_protetor))
        animal_valido = cursor.fetchone()

        if animal_valido:         

            cursor.execute("DELETE FROM animais WHERE id = %s", (id_animal,))            
            conexao.commit()

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        app.logger.exception("Erro ao excluir animal")
        return "<h1>Erro ao excluir o animal. Tente novamente.</h1>"


@app.route('/editar_animal/<int:id_animal>')
def carregar_edicao_animal(id_animal):
    """
    Consulta o registro específico de um animal e renderiza o formulário de atualização pré-preenchido.
    """
    if 'usuario_logado' not in session:
        return redirect('/login')

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
        app.logger.exception("Erro ao carregar animal para edição")
        return "<h1>Erro ao carregar o animal.</h1>"


@app.route('/salvar_edicao/<int:id_animal>', methods=['POST'])
def salvar_edicao_animal(id_animal):
    if 'usuario_logado' not in session:
        return redirect('/login')

    id_protetor = session['id_usuario']

    # Pegando todos os campos do HTML
    novo_nome = request.form.get('nome')
    nova_especie = request.form.get('especie')
    nova_idade = request.form.get('idade') if request.form.get('idade') else None
    nova_raca = request.form.get('raca')
    nova_foto = request.form.get('foto-pet') if request.form.get('foto-pet') else None
    
    # Novos campos adicionados
    novo_chip = request.form.get('chip') if request.form.get('chip') else None
    # O formulário envia '1' (Sim) ou '0' (Não): só '1', 'sim', 'true' ou 'on' contam como castrado
    valor_castrado = str(request.form.get('castrado')).lower()
    castrado = 1 if valor_castrado in ['1', 'sim', 'true', 'on'] else 0
    # Sem castração, não guarda data
    data_castracao = request.form.get('data') if (castrado and request.form.get('data')) else None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Adicionamos chip, castrado e data_castracao no UPDATE
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
        
        app.logger.exception("Erro na atualização do animal")
        return "<script>alert('Erro ao atualizar o animal. Tente novamente.'); window.history.back();</script>"
    
@app.route('/cadastrar_consulta/<int:id_animal>', methods=['GET', 'POST'])
@login_required
def cadastrar_consulta(id_animal):
    if not animal_do_usuario(id_animal):
        abort(404)

    conexao = conectar_banco()
    # Usando o DictCursor para ficar igual ao resto do seu código
    cursor = conexao.cursor(pymysql.cursors.DictCursor)
    
    # Busca os dados do animal para sabermos quem é
    cursor.execute("SELECT * FROM animais WHERE id = %s", (id_animal,))
    animal = cursor.fetchone()

    if request.method == 'POST':
        # O nome agora vem automático do banco, não precisa pegar do form
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
            # Aqui usamos id_animal (a variável do Python) para preencher a coluna animal_id no banco
            valores = (id_animal, data_consulta, hora_consulta, clinica, veterinario, motivo)

            cursor.execute(sql, valores)
            conexao.commit()
            
            # Sucesso! Volta para a página do animal específico
            return redirect(url_for('pagina_animal', id_animal=id_animal))
            
        except Exception as e:
            app.logger.exception("Erro ao inserir consulta")
            return "<h1>Erro ao salvar a consulta.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Se for GET, envia a variável animal para preencher a tela
    return render_template('cadastroConsultas.html', animal=animal)

#------------------------------------------------------------------------------------------------#
# ROTAS DE ACESSO RESTRITO
@app.route('/painel')
def painel():
    """
    Interface principal do usuário. Consulta a base de dados para retornar 
    exclusivamente os animais vinculados à sessão ativa.
    """
    if 'usuario_logado' not in session:
        return redirect('/login')

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
        app.logger.exception("Erro ao carregar o painel")
        return "<h1>Erro ao carregar o painel. Tente novamente.</h1>"



# INICIALIZAÇÃO DA APLICAÇÃO
if __name__ == '__main__':
    # Servidor de desenvolvimento: debug só se FLASK_DEBUG=1 no .env local
    app.run(host='127.0.0.1', port=5001, debug=config.DEBUG)



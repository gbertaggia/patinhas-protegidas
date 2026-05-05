from flask import Flask, render_template, request, session, redirect
import pymysql
import os
from dotenv import load_dotenv

# 1. SETUP DE SEGURANÇA E AMBIENTE
load_dotenv() # Lê o arquivo .env

app = Flask(__name__) # Cria o motor do site
app.secret_key = 'chave_do_projeto' # Carimbo de segurança para assinar os crachás (sessões)

# 2. PONTE COM O BANCO DE DADOS
def conectar_banco():
    # Abre o "cano" de comunicação com o MySQL local usando a senha protegida
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="patinhas_protegidas"
    )

# 3. ROTAS VISUAIS (Telas que apenas entregam HTML)
@app.route('/')
def home():
    # entrega a tela visual de Login
    return render_template('login.html')

@app.route('/cadastro')
def tela_cadastro():
    # entrega o formulário em branco para a protetora
    return render_template('cadastro.html')

# 4. ROTAS DE PROCESSAMENTO (Recebem dados, falam com o banco e tomam decisões)
@app.route('/cadastrar', methods=['POST'])
def criar_conta():
    # Pega o que a protetora digitou no HTML
    email_novo = request.form.get('email')
    senha_nova = request.form.get('senha')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor() # Cria a ferramenta para executar comandos

        # Comando SQL protegido contra hackers (%s)
        comando_sql = "INSERT INTO usuarios (email, senha) VALUES (%s, %s)"
        valores = (email_novo, senha_nova)
        
        cursor.execute(comando_sql, valores) # Envia para a prateleira do banco
        conexao.commit() # Salva definitivamente no disco rígido do banco

        cursor.close()
        conexao.close()

        # Resposta rápida (Mock) para testar se funcionou (se der tempo, podemos criar separadamente e fazer render_template('sucesso.html') por ex)
        return "<h1>Sucesso! 🎉</h1> <p>Conta criada! Agora você pode fazer login.</p> <a href='/'>Voltar para o Login</a>"

    except Exception as e:
        return f"<h1>Ops! Erro ao criar conta 🚨</h1> <p>Detalhes: {e}</p>"

@app.route('/login', methods=['POST'])
def fazer_login():
    # Pega as credenciais digitadas no HTML
    email_digitado = request.form.get('email')
    senha_digitada = request.form.get('senha')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Busca no banco se existe alguém com essa combinação exata
        comando_sql = "SELECT * FROM usuarios WHERE email = %s AND senha = %s"
        valores = (email_digitado, senha_digitada)
        cursor.execute(comando_sql, valores)

        # traz 1 registro (ou None se não achar nada)
        usuario_encontrado = cursor.fetchone()

        cursor.close()
        conexao.close()

        # Se trouxe dados (True), o usuário existe
        if usuario_encontrado:
            # Cria o crachá assinado guardando o e-mail dela e manda pro painel
            session['usuario_logado'] = email_digitado
            session['id_usuario'] = usuario_encontrado[0]
            return redirect('/painel')
        else:
            # Se trouxe None (False), barra a entrada
            return "<h1>Acesso Negado ❌</h1> <p>E-mail ou senha incorretos.</p> <a href='/'>Voltar</a>"

    except Exception as e:
        return f"<h1>Ops! Ocorreu um erro no Banco de Dados 🚨</h1> <p>Detalhes: {e}</p>"
    
@app.route('/cadastrar_animal', methods=['POST'])
def cadastrar_animal():
    # VERIFICAÇÃO DE SEGURANÇA (se o usuário não está logado, então é redirecionado para página principal)
    if 'usuario_logado' not in session:
        return redirect('/')

    # IDENTIFICAÇÃO 
    id_protetora = session['id_usuario']

    # CAPTURA DOS DADOS DO HTML
    nome_animal = request.form.get('foto')
    nome_animal = request.form.get('nome')
    especie_animal = request.form.get('especie')
    idade_animal = request.form.get('idade')
    raca_animal = request.form.get('raca')
    castrado = request.form.get('castrado')
    data_castracao = request.form.get('data')
    # INGESTÃO NO BANCO DE DADOS
    try:
        # abrindo conexão e cursor
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Comando SQL de inserção
        comando_sql = "INSERT INTO animais (usuario_id, nome, especie, idade, raca) VALUES (%s, %s, %s, %s, %s)"
        
        # A tupla aguardando a inserção
        valores = (id_protetora, nome_animal, especie_animal, idade_animal, raca_animal)

        # salva no disco e libera os recursos do banco
        cursor.execute(comando_sql, valores)
        conexao.commit()
        
        cursor.close()
        conexao.close()

        return "<h1>Sucesso! 🐾</h1> <p>Animalzinho registrado no sistema.</p> <a href='/painel'>Voltar ao Painel</a>"

    except Exception as e:
        return f"<h1>Ops! Erro ao registrar o animal 🚨</h1> <p>Detalhes: {e}</p>"
    
#rota para deletar animal vinculado a um usuario_id específico   
@app.route('/deletar_animal/<int:id_animal>')
def deletar_animal(id_animal):
    if 'usuario_logado' not in session:
        return redirect('/')

    # Pega quem está logado no momento
    id_protetora = session['id_usuario']

    # comando de exclusão
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "DELETE FROM animais WHERE id = %s AND usuario_id = %s"
        
        valores = (id_animal, id_protetora)

        cursor.execute(comando_sql, valores)
        conexao.commit()
        
        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        return f"<h1>Ops! Erro ao deletar o animal 🚨</h1> <p>Detalhes: {e}</p>"
    
#rota para editar o cadastro de um animal
@app.route('/editar_animal/<int:id_animal>')
def carregar_edicao_animal(id_animal):
    if 'usuario_logado' not in session:
        return redirect('/')
    
    id_protetora = session['id_usuario']

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "SELECT * FROM animais WHERE id = %s AND usuario_id = %s"
        
        # veio da URL: id_animal
        valores = (id_animal, id_protetora)

        cursor.execute(comando_sql, valores)
        
        # Como é apenas UM animal, usamos o fetchone()
        # O animal_para_editar será um dicionário (ou tupla) com os dados atuais
        animal_para_editar = cursor.fetchone()
        
        cursor.close()
        conexao.close()

        # Se por acaso o animal não for encontrado (ID errado ou não é daquela protetora)
        if not animal_para_editar:
            return "<h1>Animal não encontrado! 🔍</h1>"

        # Entregamos o animal para a tela de edição
        return render_template('editar_animal.html', animal=animal_para_editar)

    except Exception as e:
        return f"<h1>Erro ao carregar os dados 🚨</h1> <p>{e}</p>"
    
# rota de edição
# O 'POST' garante que essa rota só aceita dados enviados por um formulário HTML
@app.route('/salvar_edicao/<int:id_animal>', methods=['POST'])
def salvar_edicao_animal(id_animal):
    
    if 'usuario_logado' not in session:
        return redirect('/')
    
    id_protetora = session['id_usuario']


    novo_nome = request.form.get('nome')
    nova_especie = request.form.get('especie')
    nova_idade = request.form.get('idade')
    nova_raca = request.form.get('raca')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = """
            UPDATE animais 
            SET nome = %s, especie = %s, idade = %s, raca = %s 
            WHERE id = %s AND usuario_id = %s
        """
        
        # A Tupla na ordem EXATA dos %s (4 dados novos + 2 travas de segurança)
        valores = (novo_nome, nova_especie, nova_idade, nova_raca, id_animal, id_protetora)

        # 5. Executa e Salva (commit é obrigatório no UPDATE)
        cursor.execute(comando_sql, valores)
        conexao.commit()
        
        cursor.close()
        conexao.close()

        # Manda a usuária de volta pro painel com a lista atualizada
        return redirect('/painel')

    except Exception as e:
        return f"<h1>Ops! Erro ao atualizar o animal 🚨</h1> <p>Detalhes: {e}</p>"

# 5. ROTAS PROTEGIDAS (Apenas para quem tem crachá)
@app.route('/painel')
def painel():
    
    if 'usuario_logado' not in session:
        return redirect('/')
    
    email_da_protetora = session['usuario_logado']
    id_protetora = session['id_usuario'] 

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "SELECT * FROM animais where usuario_id = %s"
        valores = (id_protetora,)
        
        cursor.execute(comando_sql, valores)
        lista_animais = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        return render_template('painel.html', email=email_da_protetora, animais=lista_animais)

    except Exception as e:
        return f"<h1>Ops! Erro ao carregar o painel 🚨</h1> <p>Detalhes: {e}</p>"

@app.route('/logout')
def sair():
    # Rasga o crachá e manda a pessoa de volta pro início
    session.pop('usuario_logado', None)
    return redirect('/')

# 6. LIGAÇÃO DO MOTOR PRINCIPAL
if __name__ == '__main__':
    # Mantém o servidor ligado infinitamente na porta 5000
    app.run(host='0.0.0.0', debug=True)

    
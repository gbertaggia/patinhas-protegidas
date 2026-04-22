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
            return redirect('/painel')
        else:
            # Se trouxe None (False), barra a entrada
            return "<h1>Acesso Negado ❌</h1> <p>E-mail ou senha incorretos.</p> <a href='/'>Voltar</a>"

    except Exception as e:
        return f"<h1>Ops! Ocorreu um erro no Banco de Dados 🚨</h1> <p>Detalhes: {e}</p>"

# 5. ROTAS PROTEGIDAS (Apenas para quem tem crachá)
@app.route('/painel')
def painel():
    # Se não tiver crachá na memória, expulsa de volta para a porta principal
    if 'usuario_logado' not in session:
        return redirect('/')
    
    # Lê o nome no crachá e entrega a tela do painel 
    email_da_protetora = session['usuario_logado']
    return render_template('painel.html', email=email_da_protetora)

@app.route('/logout')
def sair():
    # Rasga o crachá e manda a pessoa de volta pro início
    session.pop('usuario_logado', None)
    return redirect('/')

# 6. LIGAÇÃO DO MOTOR PRINCIPAL
if __name__ == '__main__':
    # Mantém o servidor ligado infinitamente na porta 5000
    app.run(host='0.0.0.0', debug=True)
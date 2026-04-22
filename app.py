from flask import Flask, render_template, request, session, redirect
import pymysql

app = Flask(__name__)

# CHAVE SECRETA: Obrigatória para usar sessões. O Flask usa isso para criptografar o crachá.
app.secret_key = 'chave_super_secreta_do_projeto' 

def conectar_banco():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="Cobinhakai16*16",  
        database="patinhas_protegidas"
    )

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/cadastro')
def tela_cadastro():
    return render_template('cadastro.html')

@app.route('/cadastrar', methods=['POST'])
def criar_conta():
    try:
        email_novo = request.form.get('email')
        senha_nova = request.form.get('senha')

        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "INSERT INTO usuarios (email, senha) VALUES (%s, %s)"
        valores = (email_novo, senha_nova)
        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return "<h1>Sucesso! 🎉</h1> <p>Conta criada! Agora você pode fazer login.</p> <a href='/'>Voltar para o Login</a>"

    except Exception as e:
        return f"<h1>Ops! Erro ao criar conta 🚨</h1> <p>Detalhes: {e}</p>"

@app.route('/login', methods=['POST'])
def fazer_login():
    try:
        email_digitado = request.form.get('email')
        senha_digitada = request.form.get('senha')

        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "SELECT * FROM usuarios WHERE email = %s AND senha = %s"
        valores = (email_digitado, senha_digitada)
        cursor.execute(comando_sql, valores)

        usuario_encontrado = cursor.fetchone()

        cursor.close()
        conexao.close()

        if usuario_encontrado:
            # === A MÁGICA ACONTECE AQUI ===
            # Em vez de só mostrar um texto, nós criamos o "crachá" e redirecionamos pro painel!
            session['usuario_logado'] = email_digitado
            return redirect('/painel')
        else:
            return "<h1>Acesso Negado ❌</h1> <p>E-mail ou senha incorretos.</p> <a href='/'>Voltar</a>"

    except Exception as e:
        return f"<h1>Ops! Ocorreu um erro no Banco de Dados 🚨</h1> <p>Detalhes: {e}</p>"

# === NOVAS ROTAS (PAINEL E SAIR) ===

@app.route('/painel')
def painel():
    # Verifica se a pessoa TEM o crachá. Se não tiver, manda de volta pro login.
    if 'usuario_logado' not in session:
        return redirect('/')
    
    # Se ela tem o crachá, pega o email escrito nele e manda pra tela
    email_da_protetora = session['usuario_logado']
    return render_template('painel.html', email=email_da_protetora)

@app.route('/logout')
def sair():
    # Destrói o crachá e manda pro login
    session.pop('usuario_logado', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
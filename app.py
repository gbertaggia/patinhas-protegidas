from flask import Flask, render_template, request
import pymysql  

app = Flask(__name__)

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
            return f"<h1>Sucesso! 🎉</h1> <p>Bem-vinda, {email_digitado}! O banco de dados confirmou sua identidade.</p>"
        else:
            return "<h1>Acesso Negado ❌</h1> <p>E-mail ou senha incorretos.</p>"

    except Exception as e:
        return f"<h1>Ops! Ocorreu um erro no Banco de Dados 🚨</h1> <p>Detalhes técnicos: {e}</p>"

if __name__ == '__main__':
    app.run(debug=True)
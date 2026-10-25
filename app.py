from flask import Flask, render_template
import config
from routes.auth import bp as auth_bp
from routes.animais import bp as animais_bp
from routes.saude import bp as saude_bp


app = Flask(__name__)  # Instancia a aplicação web Flask

# Chave criptográfica necessária para o gerenciamento de estado (sessões HTTP)
app.secret_key = config.SECRET_KEY

# Registra os módulos de rotas (cada um com seu arquivo em routes/)
app.register_blueprint(auth_bp)
app.register_blueprint(animais_bp)
app.register_blueprint(saude_bp)


# PÁGINA PÚBLICA
@app.route("/")
def pagina_publica():
    return render_template("publico.html")


# INICIALIZAÇÃO DA APLICAÇÃO
if __name__ == '__main__':
    # Servidor de desenvolvimento: debug só se FLASK_DEBUG=1 no .env local
    app.run(host='127.0.0.1', port=5001, debug=config.DEBUG)
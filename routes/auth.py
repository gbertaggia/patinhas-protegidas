from flask import Blueprint, render_template, request, session, redirect, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from database.connection import conectar_banco
from utils.auth import login_required

# Blueprint = um "pedaço" do aplicativo, com suas próprias rotas
bp = Blueprint('auth', __name__)


@bp.route('/login')
def home():
    # Renderiza a interface de autenticação (Login)
    return render_template('login.html')


@bp.route('/cadastro')
def tela_cadastro():
    # Renderiza a interface de registro de novos usuários
    return render_template('cadastro.html')


@bp.route('/cadastrar', methods=['POST'])
def criar_conta():
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    telefone = request.form.get('telefone')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Trava de segurança: não permite dois cadastros com o mesmo e-mail
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            cursor.close()
            conexao.close()
            return """
                <h1 style="color: red; text-align: center; margin-top: 50px;">E-mail já cadastrado ⚠️</h1>
                <p style="text-align: center;">Este endereço de e-mail já possui uma conta no Patinhas Protegidas.</p>
                <div style="text-align: center;">
                    <a href="/cadastro" style="font-size: 18px;">Tentar outro e-mail</a> ou
                    <a href="/login" style="font-size: 18px;">Fazer Login</a>
                </div>
            """

        comando_sql = "INSERT INTO usuarios (nome, email, senha, telefone) VALUES (%s, %s, %s, %s)"
        valores = (nome, email, generate_password_hash(senha), telefone)
        cursor.execute(comando_sql, valores)
        conexao.commit()

        id_novo_usuario = cursor.lastrowid

        session['usuario_logado'] = email
        session['nome_usuario'] = nome
        session['id_usuario'] = id_novo_usuario

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception:
        current_app.logger.exception("Erro ao criar conta")
        return "<h1>Erro ao criar a conta. Tente novamente.</h1>"


@bp.route('/login', methods=['POST'])
def fazer_login():
    """Valida as credenciais contra o banco e gerencia a sessão."""
    email_digitado = request.form.get('email')
    senha_digitada = request.form.get('senha')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(pymysql.cursors.DictCursor)

        # Busca só pelo e-mail: a senha é conferida no Python, não no SQL
        cursor.execute("SELECT id, nome, email, senha FROM usuarios WHERE email = %s", (email_digitado,))
        usuario = cursor.fetchone()

        senha_correta = False
        if usuario:
            senha_salva = usuario['senha']
            if senha_salva.startswith(('scrypt:', 'pbkdf2:')):
                # Conta nova: a senha guardada é um hash
                senha_correta = check_password_hash(senha_salva, senha_digitada)
            elif senha_salva == senha_digitada:
                # Conta antiga (senha em texto puro): entra e já converte para hash
                senha_correta = True
                cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s",
                               (generate_password_hash(senha_digitada), usuario['id']))
                conexao.commit()

        cursor.close()
        conexao.close()

        if senha_correta:
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            session['id_usuario'] = usuario['id']
            return redirect('/painel')
        else:
            return "<script>alert('⚠️ Autenticação Falhou: E-mail ou senha incorretos.'); window.location.href='/login';</script>"

    except Exception:
        current_app.logger.exception("Erro no login")
        return "<h1>Erro ao entrar. Tente novamente.</h1>"


@bp.route('/editar_usuario', methods=['GET', 'POST'])
@login_required
def editar_perfil_usuario():
    id_usuario = session['id_usuario']
    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        novo_nome = request.form.get('nome')
        novo_telefone = request.form.get('telefone')

        try:
            cursor.execute("UPDATE usuarios SET nome = %s, telefone = %s WHERE id = %s",
                           (novo_nome, novo_telefone if novo_telefone else None, id_usuario))
            conexao.commit()

            # Atualiza o nome na sessão para o painel mostrar o texto de boas-vindas novo
            session['nome_usuario'] = novo_nome

            return redirect('/painel')
        except Exception:
            current_app.logger.exception("Erro ao atualizar usuário")
            return "<h1>Erro ao atualizar o perfil. Tente novamente.</h1>"
        finally:
            cursor.close()
            conexao.close()

    # Método GET: busca os dados atuais para preencher a tela
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
    usuario = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template('editarUsuario.html', usuario=usuario)


@bp.route('/logout')
def sair():
    """Destrói as variáveis de sessão e encerra o acesso autenticado."""
    session.pop('usuario_logado', None)
    session.pop('nome_usuario', None)
    session.pop('id_usuario', None)
    return redirect('/login')
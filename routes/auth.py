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


UFS = (
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
    'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
)
TIPOS_DE_CONTA = ('PROTETOR', 'ONG')


@bp.route('/cadastro')
def tela_cadastro():
    # Renderiza a interface de registro de novos usuários
    return render_template('cadastro.html', ufs=UFS)


def _pagina_de_erro(mensagem, voltar_para, texto_do_link):
    """Página simples de erro de validação de formulário (resposta 400)."""
    return f"""
        <h1 style="color: red; text-align: center; margin-top: 50px;">{mensagem}</h1>
        <div style="text-align: center;">
            <a href="{voltar_para}" style="font-size: 18px;">{texto_do_link}</a>
        </div>
    """, 400


def _validar_perfil(nome, tipo, cidade, uf):
    """Regras do perfil, iguais no cadastro e na edição. Devolve a mensagem de erro ou None."""
    if not nome or len(nome) > 100:
        return 'Informe o nome (até 100 caracteres).'
    if tipo not in TIPOS_DE_CONTA:
        return 'Escolha se você é protetor(a) ou ONG.'
    if not cidade or len(cidade) > 100:
        return 'Informe a cidade (até 100 caracteres).'
    if uf not in UFS:
        return 'Escolha o estado.'
    return None


@bp.route('/cadastrar', methods=['POST'])
def criar_conta():
    nome = (request.form.get('nome') or '').strip()
    email = (request.form.get('email') or '').strip()
    senha = request.form.get('senha') or ''
    telefone = (request.form.get('telefone') or '').strip() or None
    tipo = request.form.get('tipo')
    cidade = (request.form.get('cidade') or '').strip()
    uf = request.form.get('uf')

    # Validação no servidor: o HTML também exige os campos, mas ele pode ser burlado
    if not email or not senha:
        return _pagina_de_erro('Preencha e-mail e senha.', '/cadastro', 'Voltar ao cadastro')
    erro = _validar_perfil(nome, tipo, cidade, uf)
    if erro:
        return _pagina_de_erro(erro, '/cadastro', 'Voltar ao cadastro')

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

        comando_sql = """
            INSERT INTO usuarios (nome, email, senha, telefone, tipo, cidade, uf)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (nome, email, generate_password_hash(senha), telefone, tipo, cidade, uf)
        
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

    if request.method == 'POST':
        novo_nome = (request.form.get('nome') or '').strip()
        novo_telefone = (request.form.get('telefone') or '').strip() or None
        novo_tipo = request.form.get('tipo')
        nova_cidade = (request.form.get('cidade') or '').strip()
        novo_uf = request.form.get('uf')

        erro = _validar_perfil(novo_nome, novo_tipo, nova_cidade, novo_uf)
        if erro:
            return _pagina_de_erro(erro, '/editar_usuario', 'Voltar à edição do perfil')

        conexao = conectar_banco()
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET nome = %s, telefone = %s, tipo = %s, cidade = %s, uf = %s WHERE id = %s",
                (novo_nome, novo_telefone, novo_tipo, nova_cidade, novo_uf, id_usuario),
            )
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

    # Método GET: busca os dados atuais para preencher a tela (sem a senha)
    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "SELECT nome, email, telefone, tipo, cidade, uf FROM usuarios WHERE id = %s", (id_usuario,)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()

    return render_template('editarUsuario.html', usuario=usuario, ufs=UFS)


@bp.route('/logout')
def sair():
    """Destrói as variáveis de sessão e encerra o acesso autenticado."""
    session.pop('usuario_logado', None)
    session.pop('nome_usuario', None)
    session.pop('id_usuario', None)
    return redirect('/login')
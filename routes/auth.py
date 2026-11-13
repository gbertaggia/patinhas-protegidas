from flask import Blueprint, render_template, request, session, redirect, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from database.connection import conectar_banco
from utils.auth import login_required
from utils.pix import normalizar_chave_pix
from utils.urls import normalizar_url_http

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
TAMANHO_MINIMO_DA_SENHA = 8


@bp.route('/cadastro')
def tela_cadastro():
    # Renderiza a interface de registro de novos usuários
    return render_template('cadastro.html', ufs=UFS)


def _pagina_de_erro(mensagem, voltar_para, texto_do_link, status=400, titulo='Não foi possível continuar',
                    outro_link=None):
    """
    Página de erro no mesmo estilo das demais telas (templates/erro.html).

    `outro_link` é um par opcional (endereço, texto) para uma segunda opção.
    O texto vai para o HTML pelo Jinja, que já escapa caracteres perigosos.
    """
    html = render_template(
        'erro.html', titulo=titulo, mensagem=mensagem,
        voltar_para=voltar_para, texto_do_link=texto_do_link, outro_link=outro_link,
    )
    return html, status


def _tela_de_login_com_erro(mensagem, email, status):
    """Mostra a tela de login de novo, com a mensagem de erro e o e-mail já digitado."""
    return render_template('login.html', erro=mensagem, email=email or ''), status


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
    missao = request.form.get("missao", "").strip() or None
    logo_url, erro_logo = normalizar_url_http(request.form.get("logo_url"), "O link da logo")
    link_formulario_adocao, erro_link = normalizar_url_http(
        request.form.get("link_formulario_adocao"), "O link do formulário de adoção"
    )

    # Validação no servidor
    if not email or not senha:
        return _pagina_de_erro('Preencha e-mail e senha.', '/cadastro', 'Voltar ao cadastro')
    if len(senha) < TAMANHO_MINIMO_DA_SENHA:
        return _pagina_de_erro(
            f'A senha deve ter pelo menos {TAMANHO_MINIMO_DA_SENHA} caracteres.',
            '/cadastro', 'Voltar ao cadastro',
        )
    erro = _validar_perfil(nome, tipo, cidade, uf) or erro_logo or erro_link
    if erro:
        return _pagina_de_erro(erro, '/cadastro', 'Voltar ao cadastro')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            cursor.close()
            conexao.close()
            return _pagina_de_erro(
                'Este endereço de e-mail já possui uma conta no Patinhas Protegidas.',
                '/cadastro', 'Tentar outro e-mail',
                status=409, titulo='E-mail já cadastrado', outro_link=('/login', 'Entrar'),
            )

        comando_sql = """
            INSERT INTO usuarios (nome, email, senha, telefone, tipo, cidade, uf, missao, logo_url, link_formulario_adocao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            nome, email, generate_password_hash(senha), telefone, tipo, cidade, uf,
            missao, logo_url, link_formulario_adocao
        )
        
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
        return _pagina_de_erro(
            'Não foi possível criar a conta agora. Tente novamente em instantes.',
            '/cadastro', 'Voltar ao cadastro', status=500, titulo='Algo deu errado',
        )


@bp.route('/login', methods=['POST'])
def fazer_login():
    """Valida as credenciais contra o banco e gerencia a sessão."""
    email_digitado = (request.form.get('email') or '').strip()
    senha_digitada = request.form.get('senha') or ''

    if not email_digitado or not senha_digitada:
        return _tela_de_login_com_erro('Informe o e-mail e a senha.', email_digitado, 400)

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT id, nome, email, senha FROM usuarios WHERE email = %s", (email_digitado,))
        usuario = cursor.fetchone()

        senha_correta = False
        if usuario:
            senha_salva = usuario['senha']
            if senha_salva.startswith(('scrypt:', 'pbkdf2:')):
                senha_correta = check_password_hash(senha_salva, senha_digitada)
            elif senha_salva == senha_digitada:
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
            # Mesma mensagem para e-mail inexistente e senha errada: não revela quem tem conta
            return _tela_de_login_com_erro('E-mail ou senha incorretos.', email_digitado, 401)

    except Exception:
        current_app.logger.exception("Erro no login")
        return _pagina_de_erro(
            'Não foi possível entrar agora. Tente novamente em instantes.',
            '/login', 'Voltar ao login', status=500, titulo='Algo deu errado',
        )


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
        novo_missao = request.form.get('missao', '').strip() or None
        novo_logo_url, erro_logo = normalizar_url_http(request.form.get('logo_url'), 'O link da logo')
        novo_link_formulario, erro_link = normalizar_url_http(
            request.form.get('link_formulario_adocao'), 'O link do formulário de adoção'
        )
        nova_chave_pix, erro_pix = normalizar_chave_pix(request.form.get('chave_pix'))
        if erro_pix:
            return _pagina_de_erro(erro_pix, '/editar_usuario', 'Voltar à edição do perfil')

        erro = _validar_perfil(novo_nome, novo_tipo, nova_cidade, novo_uf) or erro_logo or erro_link
        if erro:
            return _pagina_de_erro(erro, '/editar_usuario', 'Voltar à edição do perfil')

        conexao = conectar_banco()
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE usuarios
                SET tipo = %s, nome = %s, telefone = %s, cidade = %s, uf = %s,
                    missao = %s, logo_url = %s, link_formulario_adocao = %s, chave_pix = %s
                WHERE id = %s
                """,
                (
                    novo_tipo, novo_nome, novo_telefone, nova_cidade, novo_uf,
                    novo_missao, novo_logo_url, novo_link_formulario, nova_chave_pix, id_usuario
                )
            )
            conexao.commit()

            session['nome_usuario'] = novo_nome

            return redirect('/painel')
        except Exception:
            current_app.logger.exception("Erro ao atualizar usuário")
            return _pagina_de_erro(
                'Não foi possível salvar o perfil agora. Tente novamente em instantes.',
                '/editar_usuario', 'Voltar à edição do perfil', status=500, titulo='Algo deu errado',
            )
        finally:
            cursor.close()
            conexao.close()

    # Método GET: busca os dados atuais para preencher a tela
    conexao = conectar_banco()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            """
            SELECT id, nome, email, telefone, cidade, uf, tipo, missao, logo_url, link_formulario_adocao, chave_pix
            FROM usuarios
            WHERE id = %s
            """,
            (id_usuario,)
        )
        usuario = cursor.fetchone()
    finally:
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
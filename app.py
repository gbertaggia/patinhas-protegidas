from ast import Try
from flask import Flask, render_template, request, session, redirect, url_for
from database.connection import conectar_banco
import os
import pymysql
# 1. CONFIGURAÇÃO DO AMBIENTE E INICIALIZAÇÃO
#  # Carrega as variáveis de ambiente do arquivo .env

app = Flask(__name__)  # Instancia a aplicação web Flask

# Chave criptográfica necessária para o gerenciamento de estado (sessões HTTP)
app.secret_key = os.getenv("SECRET_KEY")


# 3. ROTAS DE RENDERIZAÇÃO (MÉTODO GET)
@app.route('/')
def home():
    # Renderiza a interface de autenticação (Login)
    return render_template('login.html')


@app.route('/cadastro')
def tela_cadastro():
    # Renderiza a interface de registro de novos usuários
    return render_template('cadastro.html')


@app.route('/cadastro_animal')
def tela_cadastro_pet():
    # Renderiza a interface de registro de animais
    return render_template('cadastroAnimal.html')


@app.route('/pagina_animal/<int:id_animal>')
def pagina_animal(id_animal):

    conexao = conectar_banco()

    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    # Busca animal
    cursor.execute(
        "SELECT * FROM animais WHERE id = %s",
        (id_animal,)
    )

    animal = cursor.fetchone()#retorna um dicionario

    # Busca vacinas
    cursor.execute(
        "SELECT * FROM vacinas WHERE animal_id = %s",
        (id_animal,)
    )

    vacinas = cursor.fetchall()#retorna uma lista

    cursor.close()
    conexao.close()

    return render_template(
        'paginaAnimal.html',
        animal=animal,
        vacinas=vacinas
    )


@app.route('/animal/<int:id_animal>/vacina')
def cadastro_vacina(id_animal):

    return render_template(
        'cadastroVacinas.html',
        id_animal=id_animal
    )


@app.route('/salvar_vacina/<int:id_animal>', methods=['POST'])
def salvar_vacina(id_animal):

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
            VALUES (%s, %s, %s, %s,%s)
            """,
            (id_animal, nome_vacina, data_vacina, status_vacina, dose_vacina)
        )

        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect(f'/pagina_animal/{id_animal}')
    except Exception as e:
        return f"Erro: {e}"     

@app.route('/deletar_vacina/<int:id_vacina>/<int:id_animal>')
def deletar_vacina(id_vacina, id_animal):

    try:

        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = """
            DELETE FROM vacinas
            WHERE id = %s
        """

        cursor.execute(comando_sql, (id_vacina,))

        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect(
            url_for(
                'pagina_animal',
                id_animal=id_animal
            )
        )

    except Exception as e:
        return f"Erro ao deletar vacina: {e}" 

# 4. ROTAS DE PROCESSAMENTO E REGRA DE NEGÓCIO (CRUD DE USUÁRIOS E AUTENTICAÇÃO)
@app.route('/cadastrar', methods=['POST'])
def criar_conta():
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    telefone = request.form.get('telefone')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor() 

        # --- NOVA TRAVA DE SEGURANÇA ---
        # 1. Pergunta ao banco se já existe alguém com esse e-mail
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario_existente = cursor.fetchone()

        # Se retornou algo, o e-mail já existe. Barrar o cadastro!
        if usuario_existente:
            cursor.close()
            conexao.close()
            return """
                <h1 style="color: red; text-align: center; margin-top: 50px;">E-mail já cadastrado ⚠️</h1>
                <p style="text-align: center;">Este endereço de e-mail já possui uma conta no Patinhas Protegidas.</p>
                <div style="text-align: center;">
                    <a href="/cadastro" style="font-size: 18px;">Tentar outro e-mail</a> ou 
                    <a href="/" style="font-size: 18px;">Fazer Login</a>
                </div>
            """

        # Se não existir, segue o fluxo normal de Inserção
        comando_sql = "INSERT INTO usuarios (nome, email, senha, telefone) VALUES (%s, %s, %s, %s)"
        valores = (nome, email, senha, telefone)

        cursor.execute(comando_sql, valores)
        conexao.commit() 

        id_novo_usuario = cursor.lastrowid

        session['usuario_logado'] = email
        session['nome_usuario'] = nome
        session['id_usuario'] = id_novo_usuario

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        return f"<h1>Erro interno na criação de conta</h1> <p>Detalhes: {e}</p>"

@app.route('/login', methods=['POST'])
def fazer_login():
    """
    Valida as credenciais do usuário contra o banco de dados e gerencia a sessão.
    """
    email_digitado = request.form.get('email')
    senha_digitada = request.form.get('senha')

    try:
        conexao = conectar_banco()
        # Utiliza DictCursor para retornar os registros mapeados por chave-valor (coluna: dado)
        cursor = conexao.cursor(pymysql.cursors.DictCursor)

        comando_sql = "SELECT id, nome, email, senha FROM usuarios WHERE email = %s AND senha = %s"
        valores = (email_digitado, senha_digitada)
        
        cursor.execute(comando_sql, valores)
        usuario = cursor.fetchone()

        cursor.close()
        conexao.close()

        if usuario:
            # Credenciais validadas: armazena os dados no payload da sessão
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome'] 
            session['id_usuario'] = usuario['id']
            
            return redirect('/painel')
        else:
            return "<h1>Autenticação Falhou</h1> <p>E-mail ou senha incorretos.</p> <a href='/'>Retornar</a>"

    except Exception as e:
        return f"<h1>Erro de persistência de dados</h1> <p>Detalhes: {e}</p>"


@app.route('/logout')
def sair():
    """
    Destrói as variáveis de sessão e encerra o acesso autenticado.
    """
    session.pop('usuario_logado', None)
    session.pop('nome_usuario', None)
    session.pop('id_usuario', None)
    return redirect('/')


# 5. ROTAS DE PROCESSAMENTO E REGRA DE NEGÓCIO (CRUD DE ANIMAIS)
@app.route('/cadastrar_animal', methods=['POST'])
def cadastrar_animal():
    """
    Persiste um novo registro de animal vinculado ao ID do usuário autenticado.
    """
    if 'usuario_logado' not in session:
        return redirect('/')

    id_protetor = session['id_usuario']

    # Extração do payload recebido via POST
    foto_animal = request.form.get('foto-pet')
    nome_animal = request.form.get('nome')
    especie_animal = request.form.get('especie')
    idade_animal = request.form.get('idade')
    raca_animal = request.form.get('raca')
    castrado = 1 if request.form.get('castrado') else 0
    data_castracao = request.form.get('data')
    chip_identificacao = request.form.get('chip')

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
        return f"<h1>Erro na inserção do registro do animal</h1> <p>Detalhes: {e}</p>"


@app.route('/deletar_animal/<int:id_animal>')
def deletar_animal(id_animal):
    """
    Remove um registro de animal. A cláusula WHERE garante que apenas o dono do registro possa excluí-lo.
    """
    if 'usuario_logado' not in session:
        return redirect('/')

    id_protetor = session['id_usuario']

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando_sql = "DELETE FROM animais WHERE id = %s AND usuario_id = %s"
        valores = (id_animal, id_protetor)

        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        return f"<h1>Erro na exclusão do registro</h1> <p>Detalhes: {e}</p>"


@app.route('/editar_animal/<int:id_animal>')
def carregar_edicao_animal(id_animal):
    """
    Consulta o registro específico de um animal e renderiza o formulário de atualização pré-preenchido.
    """
    if 'usuario_logado' not in session:
        return redirect('/')

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
        return f"<h1>Erro na leitura dos dados</h1> <p>{e}</p>"


@app.route('/salvar_edicao/<int:id_animal>', methods=['POST'])
def salvar_edicao_animal(id_animal):
    """
    Processa a submissão do formulário de edição e atualiza (UPDATE) os dados do animal no banco.
    """
    if 'usuario_logado' not in session:
        return redirect('/')

    id_protetor = session['id_usuario']

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

        valores = (novo_nome, nova_especie, nova_idade, nova_raca, id_animal, id_protetor)

        cursor.execute(comando_sql, valores)
        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect('/painel')

    except Exception as e:
        return f"<h1>Erro na atualização do registro</h1> <p>Detalhes: {e}</p>"


# 6. ROTAS DE ACESSO RESTRITO
@app.route('/painel')
def painel():
    """
    Interface principal do usuário. Consulta a base de dados para retornar 
    exclusivamente os animais vinculados à sessão ativa.
    """
    if 'usuario_logado' not in session:
        return redirect('/')

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
        return f"<h1>Erro de renderização do painel</h1> <p>Detalhes: {e}</p>"


# 7. INICIALIZAÇÃO DA APLICAÇÃO
if __name__ == '__main__':
    # Inicializa o servidor WSGI de desenvolvimento na porta 5001
    app.run(host='0.0.0.0', port=5001, debug=True)
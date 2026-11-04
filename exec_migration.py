import os
import sys

# Garante que a raiz do projeto esteja no caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.connection import conectar_banco


def aplicar_migration():
    # Caminho até o arquivo SQL dentro da pasta migrations
    caminho_sql = os.path.join(os.path.dirname(__file__), "migrations", "005_campanhas_doacao.sql")

    if not os.path.exists(caminho_sql):
        # Tenta também dentro de database/migrations caso esteja lá
        caminho_sql = os.path.join(os.path.dirname(__file__), "database", "migrations", "005_campanhas_doacao.sql")

    if not os.path.exists(caminho_sql):
        print(f"Erro: Arquivo não encontrado em {caminho_sql}")
        return

    print(f"Lendo migration: {caminho_sql}")
    with open(caminho_sql, "r", encoding="utf-8") as f:
        conteudo_sql = f.read()

    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        # Separa os comandos caso haja mais de um delimitado por ponto e vírgula
        comandos = [cmd.strip() for cmd in conteudo_sql.split(";") if cmd.strip()]

        for comando in comandos:
            print(f"Executando:\n{comando}\n")
            cursor.execute(comando)

        conexao.commit()
        print("✓ Migration aplicada com sucesso!")
    except Exception as erro:
        conexao.rollback()
        # Código 1060 indica que a coluna já existe no MySQL
        if "1060" in str(erro) or "Duplicate column name" in str(erro):
            print("Aviso: Uma ou mais colunas já existem na tabela.")
        else:
            print(f"Erro ao executar a migration: {erro}")
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    aplicar_migration()
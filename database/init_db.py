import os
import sys

# Garante que o Python encontre a pasta raiz do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import conectar_banco


def run_migration():
    connection = conectar_banco()

    caminho_sql = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(caminho_sql, "r", encoding="utf-8") as file:
        sql_script = file.read()

    cursor = connection.cursor()

    for command in sql_script.split(";"):
        if command.strip():
            cursor.execute(command)

    connection.commit()

    print("Banco configurado com sucesso!")

    cursor.close()
    connection.close()


if __name__ == "__main__":
    run_migration()
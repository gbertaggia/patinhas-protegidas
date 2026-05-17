from connection import conectar_banco

def run_migration():
    connection = conectar_banco()

    with open("database/schema.sql", "r", encoding="utf-8") as file:
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
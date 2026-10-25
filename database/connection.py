import pymysql
import config


def conectar_banco():
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT,
        ssl={"ssl": {}},
        cursorclass=pymysql.cursors.DictCursor
    )
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def conectar_banco():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        ssl={"ssl": {}},
        cursorclass=pymysql.cursors.DictCursor
    )
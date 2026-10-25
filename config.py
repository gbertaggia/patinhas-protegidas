"""Configuração do Patinhas Protegidas: lê as variáveis de ambiente em um só lugar."""
import os
from dotenv import load_dotenv

load_dotenv(override=True)  # o arquivo .env tem prioridade no computador local

OBRIGATORIAS = ("SECRET_KEY", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT")

_faltando = [nome for nome in OBRIGATORIAS if not os.getenv(nome)]
if _faltando:
    raise RuntimeError(
        "Variáveis de ambiente ausentes: " + ", ".join(_faltando)
        + ". Configure no arquivo .env (local) ou no painel do servidor (Render)."
    )

SECRET_KEY = os.getenv("SECRET_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
try:
    DB_PORT = int(os.getenv("DB_PORT"))
except ValueError:
    raise RuntimeError("DB_PORT deve ser um número inteiro.") from None

# Modo debug só quando FLASK_DEBUG=1 (use apenas no seu computador)
DEBUG = os.getenv("FLASK_DEBUG") == "1"
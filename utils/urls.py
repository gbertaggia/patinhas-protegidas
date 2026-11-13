"""Validação de links (URLs) informados por quem usa o sistema."""
from urllib.parse import urlsplit

# Tamanho das colunas de link no banco (VARCHAR(500)); a foto do animal usa 255.
LIMITE_PADRAO = 500


def normalizar_url_http(texto, rotulo, limite=LIMITE_PADRAO):
    """
    Confere um link digitado num formulário.

    Aceita só endereços completos http:// ou https://. Isso barra esquemas
    perigosos, como javascript: e data:, que poderiam executar código quando
    o link fosse usado numa página.

    Devolve (url, erro):
      - url: o link sem espaços nas pontas, ou None se o campo veio vazio;
      - erro: a mensagem para mostrar à pessoa, ou None se estiver tudo certo.
    `rotulo` é o começo da mensagem (ex.: "O link da logo").
    """
    if texto is None:
        return None, None
    if not isinstance(texto, str):
        return None, f"{rotulo} é inválido."

    url = texto.strip()
    if not url:
        return None, None

    if len(url) > limite:
        return None, f"{rotulo} é muito longo (máximo de {limite} caracteres)."

    mensagem = f"{rotulo} deve ser um endereço completo, começando com http:// ou https://."

    # Espaços e caracteres de controle (quebra de linha, nulo...) no meio do link
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        return None, mensagem

    try:
        partes = urlsplit(url)
        servidor = partes.hostname
    except ValueError:
        return None, mensagem

    if partes.scheme.lower() not in ('http', 'https') or not servidor:
        return None, mensagem

    return url, None

"""Validação da chave Pix informada no perfil."""
import re

TAMANHO_MAXIMO = 77
_ALEATORIA = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
_EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')


def _cpf_valido(numeros):
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(numeros[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if digito != int(numeros[tamanho]):
            return False
    return True


def _cnpj_valido(numeros):
    if len(numeros) != 14 or numeros == numeros[0] * 14:
        return False
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for tamanho in (12, 13):
        soma = sum(int(numeros[i]) * pesos[i + 13 - tamanho] for i in range(tamanho))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(numeros[tamanho]):
            return False
    return True


def normalizar_chave_pix(texto):
    """Confere o formato da chave Pix e devolve (chave, erro).

    Aceita CPF, CNPJ, e-mail, telefone e chave aleatória.
    Campo vazio devolve (None, None): o perfil fica sem chave.
    """
    chave = (texto or '').strip()
    if not chave:
        return None, None
    if len(chave) > TAMANHO_MAXIMO:
        return None, "A chave Pix pode ter no máximo 77 caracteres."

    if _ALEATORIA.fullmatch(chave.lower()):
        return chave.lower(), None

    if '@' in chave:
        if _EMAIL.fullmatch(chave):
            return chave.lower(), None
        return None, "E-mail inválido para chave Pix."

    numeros = re.sub(r'\D', '', chave)
    sobrou = re.sub(r'[\d\s.\-/()+]', '', chave)
    if sobrou or not numeros:
        return None, "Chave Pix inválida. Use CPF, CNPJ, e-mail, telefone ou chave aleatória."

    if chave.startswith('+'):
        if re.fullmatch(r'55\d{10,11}', numeros):
            return '+' + numeros, None
        return None, "Telefone inválido. Use o formato +55 DDD número, por exemplo +55 11 91234-5678."

    if len(numeros) == 14:
        if _cnpj_valido(numeros):
            return numeros, None
        return None, "CNPJ inválido. Confira os números."

    if len(numeros) == 11 and _cpf_valido(numeros):
        return numeros, None
    if re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', chave):
        return None, "CPF inválido. Confira os números."

    # Celular ou fixo com DDD, sem o +55
    if len(numeros) in (10, 11):
        return '+55' + numeros, None

    return None, "Chave Pix inválida. Use CPF, CNPJ, e-mail, telefone ou chave aleatória."
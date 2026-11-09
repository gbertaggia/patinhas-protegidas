"""Ligação entre os registros de saúde (vacina, medicamento, consulta) e o Pet Finanças."""
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

VALOR_MAXIMO = Decimal('99999999.99')

# Categoria de despesa usada para cada tipo de registro de saúde
CATEGORIA_POR_ORIGEM = {
    'VACINA': 'Vacina',
    'MEDICAMENTO': 'Medicamento',
    'CONSULTA': 'Consulta',
}


def ler_valor(texto):
    """Converte o valor digitado no formulário. Devolve (valor, erro).

    Aceita '120', '120,50', '1.200', '1.200,50' e '120.50'. Campo vazio vale zero.
    """
    texto = (texto or '').strip().replace('R$', '').replace(' ', '')
    if not texto:
        return Decimal('0.00'), None
    if ',' in texto or re.fullmatch(r'\d{1,3}(\.\d{3})+', texto):
        # Formato brasileiro: ponto separa milhar, vírgula separa centavos
        texto = texto.replace('.', '').replace(',', '.')
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        return None, "Valor inválido. Use números, por exemplo 120,50."
    if not valor.is_finite() or valor < 0:
        return None, "O valor não pode ser negativo."
    if valor > VALOR_MAXIMO:
        return None, "O valor máximo permitido é R$ 99.999.999,99."
    return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), None


def sincronizar_lancamento(cursor, usuario_id, animal_id, origem_tipo, origem_id,
                           valor, data_transacao, descricao):
    """Cria ou atualiza a despesa ligada a um registro de saúde.

    - valor maior que zero: cria a despesa, ou atualiza a que já existe;
    - valor zero ou vazio: não faz nada (nenhuma despesa é apagada).
    Não faz commit: quem chama confirma tudo junto com o registro de saúde.
    """
    if not valor or valor <= 0:
        return

    cursor.execute(
        "SELECT id FROM categorias WHERE tipo = 'DESPESA' AND nome = %s",
        (CATEGORIA_POR_ORIGEM[origem_tipo],)
    )
    categoria = cursor.fetchone()
    if categoria is None:
        raise RuntimeError(f"Categoria '{CATEGORIA_POR_ORIGEM[origem_tipo]}' não encontrada.")

    # A chave única (origem_tipo, origem_id) garante um só lançamento por registro.
    cursor.execute(
        """
        INSERT INTO transacoes
            (usuario_id, animal_id, categoria_id, tipo, valor, descricao,
             data_transacao, origem_tipo, origem_id)
        VALUES (%s, %s, %s, 'DESPESA', %s, %s, %s, %s, %s) AS novo
        ON DUPLICATE KEY UPDATE
            valor = novo.valor,
            descricao = novo.descricao,
            data_transacao = novo.data_transacao
        """,
        (usuario_id, animal_id, categoria['id'], valor, (descricao or '')[:255] or None,
         data_transacao, origem_tipo, origem_id)
    )
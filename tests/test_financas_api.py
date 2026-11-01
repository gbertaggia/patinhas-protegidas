import pytest


def _id_categoria(client, tipo, nome):
    categorias = client.get('/api/categorias').get_json()
    return next(c['id'] for c in categorias if c['tipo'] == tipo and c['nome'] == nome)


def _lancar(client, **dados):
    return client.post('/api/financas/transacoes', json=dados)


# ---------- Categorias ----------

def test_categorias_exige_login(client):
    assert client.get('/api/categorias').status_code == 401


def test_categorias_lista_receitas_e_despesas(client_logado):
    resposta = client_logado.get('/api/categorias')
    dados = resposta.get_json()
    assert resposta.status_code == 200
    assert len(dados) >= 14
    assert {c['tipo'] for c in dados} == {'RECEITA', 'DESPESA'}


# ---------- Lançamento manual ----------

def test_lancar_exige_login(client):
    resposta = client.post('/api/financas/transacoes', json={'categoria_id': 1, 'valor': 10})
    assert resposta.status_code == 401


def test_despesa_tem_tipo_definido_pela_categoria(client_logado):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    resposta = _lancar(client_logado, categoria_id=categoria, valor="25,50")
    assert resposta.status_code == 201
    assert resposta.get_json()['tipo'] == 'DESPESA'
    assert resposta.get_json()['valor'] == '25.50'


def test_receita_tem_tipo_definido_pela_categoria(client_logado):
    categoria = _id_categoria(client_logado, 'RECEITA', 'Doação via Pix')
    resposta = _lancar(client_logado, categoria_id=categoria, valor=100)
    assert resposta.status_code == 201
    assert resposta.get_json()['tipo'] == 'RECEITA'


@pytest.mark.parametrize('valor', [0, -5, 'abc', '', 100000000])
def test_valor_invalido_e_recusado(client_logado, valor):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    assert _lancar(client_logado, categoria_id=categoria, valor=valor).status_code == 400


def test_categoria_inexistente_e_recusada(client_logado):
    assert _lancar(client_logado, categoria_id=999999, valor=10).status_code == 400


def test_corpo_que_nao_e_json_e_recusado(client_logado):
    resposta = client_logado.post('/api/financas/transacoes', data='texto solto')
    assert resposta.status_code == 400


# ---------- Listagem ----------

def test_listagem_filtra_por_tipo(client_logado):
    despesa = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    receita = _id_categoria(client_logado, 'RECEITA', 'Doação direta')
    _lancar(client_logado, categoria_id=despesa, valor=10)
    _lancar(client_logado, categoria_id=receita, valor=50)

    todas = client_logado.get('/api/financas/transacoes').get_json()
    so_receitas = client_logado.get('/api/financas/transacoes?tipo=RECEITA').get_json()

    assert len(todas) == 2
    assert len(so_receitas) == 1
    assert so_receitas[0]['tipo'] == 'RECEITA'


def test_listagem_filtra_por_periodo(client_logado):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    _lancar(client_logado, categoria_id=categoria, valor=10, data_transacao='2026-01-15')
    _lancar(client_logado, categoria_id=categoria, valor=20, data_transacao='2026-02-15')

    resposta = client_logado.get('/api/financas/transacoes?inicio=2026-02-01').get_json()

    assert len(resposta) == 1
    assert resposta[0]['data_transacao'] == '2026-02-15'


def test_listagem_so_mostra_dados_do_proprio_usuario(client_logado, outro_client):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    _lancar(client_logado, categoria_id=categoria, valor=10)

    assert len(client_logado.get('/api/financas/transacoes').get_json()) == 1
    assert outro_client.get('/api/financas/transacoes').get_json() == []


@pytest.mark.parametrize('consulta', [
    'tipo=XYZ',
    'inicio=abc',
    'inicio=2026-11-05&fim=2026-11-01',
    'limite=0',
    'limite=501',
    'categoria_id=abc',
    'animal_id=abc',
])
def test_filtros_invalidos_sao_recusados(client_logado, consulta):
    assert client_logado.get(f'/api/financas/transacoes?{consulta}').status_code == 400


# ---------- Resumo ----------

def test_resumo_exige_login(client):
    assert client.get('/api/financas/resumo').status_code == 401


def test_resumo_calcula_totais_e_saldo(client_logado):
    receita = _id_categoria(client_logado, 'RECEITA', 'Doação via Pix')
    alimentacao = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    higiene = _id_categoria(client_logado, 'DESPESA', 'Higiene e limpeza')
    _lancar(client_logado, categoria_id=receita, valor=100)
    _lancar(client_logado, categoria_id=alimentacao, valor="25,50")
    _lancar(client_logado, categoria_id=higiene, valor=10)

    resumo = client_logado.get('/api/financas/resumo').get_json()

    assert resumo['receitas'] == '100.00'
    assert resumo['despesas'] == '35.50'
    assert resumo['saldo'] == '64.50'
    assert len(resumo['por_categoria']) == 3


def test_resumo_vazio_para_quem_nao_tem_lancamentos(client_logado):
    resumo = client_logado.get('/api/financas/resumo').get_json()
    assert resumo['receitas'] == '0.00'
    assert resumo['despesas'] == '0.00'
    assert resumo['saldo'] == '0.00'
    assert resumo['por_categoria'] == []


def test_resumo_nao_mistura_dados_de_outra_conta(client_logado, outro_client):
    categoria = _id_categoria(client_logado, 'RECEITA', 'Doação direta')
    _lancar(client_logado, categoria_id=categoria, valor=100)

    assert outro_client.get('/api/financas/resumo').get_json()['receitas'] == '0.00'

# ---------- Animais ----------

def test_lancar_em_animal_proprio(client_logado, animal):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Vacina')
    resposta = _lancar(client_logado, categoria_id=categoria, valor=80, animal_id=animal)
    assert resposta.status_code == 201


def test_lancar_em_animal_de_outra_conta_e_recusado(client_logado, animal_de_outro):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Vacina')
    resposta = _lancar(client_logado, categoria_id=categoria, valor=80, animal_id=animal_de_outro)
    assert resposta.status_code == 404
    # e nada foi gravado
    assert client_logado.get('/api/financas/transacoes').get_json() == []


def test_lancar_em_animal_inexistente_e_recusado(client_logado):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Vacina')
    resposta = _lancar(client_logado, categoria_id=categoria, valor=80, animal_id=999999)
    assert resposta.status_code == 404


def test_listagem_filtra_por_animal_e_por_geral(client_logado, animal):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    _lancar(client_logado, categoria_id=categoria, valor=80, animal_id=animal)
    _lancar(client_logado, categoria_id=categoria, valor=10)

    do_animal = client_logado.get(f'/api/financas/transacoes?animal_id={animal}').get_json()
    gerais = client_logado.get('/api/financas/transacoes?animal_id=geral').get_json()

    assert len(do_animal) == 1
    assert do_animal[0]['animal_id'] == animal
    assert do_animal[0]['animal'] == 'Animal de teste'
    assert len(gerais) == 1
    assert gerais[0]['animal_id'] is None


def test_resumo_filtra_por_animal_e_por_geral(client_logado, animal):
    categoria = _id_categoria(client_logado, 'DESPESA', 'Alimentação')
    _lancar(client_logado, categoria_id=categoria, valor=80, animal_id=animal)
    _lancar(client_logado, categoria_id=categoria, valor=10)

    do_animal = client_logado.get(f'/api/financas/resumo?animal_id={animal}').get_json()
    gerais = client_logado.get('/api/financas/resumo?animal_id=geral').get_json()

    assert do_animal['despesas'] == '80.00'
    assert gerais['despesas'] == '10.00'

    # ---------- Página de finanças ----------

def test_pagina_financas_exige_login(client):
    resposta = client.get('/financas')
    assert resposta.status_code == 302
    assert '/login' in resposta.headers['Location']


def test_pagina_financas_abre_para_quem_esta_logado(client_logado):
    resposta = client_logado.get('/financas')
    assert resposta.status_code == 200
    assert 'Finanças' in resposta.get_data(as_text=True)


def test_pagina_financas_lista_os_animais_do_proprio_usuario(client_logado, animal):
    html = client_logado.get('/financas').get_data(as_text=True)
    assert 'Animal de teste' in html


def test_pagina_financas_nao_lista_animal_de_outra_conta(client_logado, animal_de_outro):
    html = client_logado.get('/financas').get_data(as_text=True)
    assert 'Animal de teste' not in html

def test_pagina_do_animal_mostra_o_painel_financeiro(client_logado, animal):
    resposta = client_logado.get(f'/pagina_animal/{animal}')
    assert resposta.status_code == 200
    assert f'data-animal-id="{animal}"' in resposta.get_data(as_text=True)


def test_pagina_do_animal_de_outra_conta_da_404(client_logado, animal_de_outro):
    assert client_logado.get(f'/pagina_animal/{animal_de_outro}').status_code == 404


def test_pagina_do_animal_tem_link_para_voltar_ao_painel_no_celular(client_logado, animal):
    import re

    html = client_logado.get(f'/pagina_animal/{animal}').get_data(as_text=True)
    links = re.findall(r'<a\b[^>]*>', html)
    # d-lg-none = visível só em telas pequenas (a navbar não tem botão de menu)
    assert any('d-lg-none' in a and 'href="/painel"' in a for a in links)
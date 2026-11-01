import uuid

from database.connection import conectar_banco


def _executar(comando, valores=()):
    conexao = conectar_banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(comando, valores)
        conexao.commit()
    finally:
        conexao.close()


def _tornar_ong(id_usuario, cidade='Campinas', uf='SP'):
    _executar(
        "UPDATE usuarios SET tipo = 'ONG', nome = %s, cidade = %s, uf = %s WHERE id = %s",
        ('ONG de teste', cidade, uf, id_usuario),
    )


def _divulgar(id_animal, info_saude='vermifugado', chip=None):
    _executar(
        "UPDATE animais SET visivel_publico = 1, info_saude = %s, chip = %s WHERE id = %s",
        (info_saude, chip, id_animal),
    )


def _buscar(client, id_animal):
    """Procura o animal na resposta pública, em qualquer cartão. Devolve (ong, animal) ou (None, None)."""
    dados = client.get('/api/publico/dados').get_json()
    for ong in dados['ongs']:
        for animal in ong['animais']:
            if animal['id'] == id_animal:
                return ong, animal
    return None, None


def test_dados_publicos_nao_exigem_login(client):
    resposta = client.get('/api/publico/dados')

    assert resposta.status_code == 200
    dados = resposta.get_json()
    assert dados['valoresDoacao'] == [5, 10, 20, 50]
    assert isinstance(dados['ongs'], list)


def test_animal_nao_divulgado_nao_aparece(client, usuario, animal):
    _tornar_ong(usuario)

    assert _buscar(client, animal) == (None, None)


def test_animal_divulgado_por_ong_aparece_no_cartao_da_ong(client, usuario, animal):
    _tornar_ong(usuario)
    _divulgar(animal, info_saude='vermifugado, FIV/FELV negativo')

    ong, dados_do_animal = _buscar(client, animal)

    assert ong['id'] == usuario
    assert ong['nome'] == 'ONG de teste'
    assert ong['regiao'] == 'Campinas, SP'
    assert dados_do_animal['nome'] == 'Animal de teste'
    assert dados_do_animal['especie'] == 'gato'
    assert dados_do_animal['infoSaude'] == 'vermifugado, FIV/FELV negativo'
    assert dados_do_animal['cidade'] == 'Campinas'
    assert dados_do_animal['estado'] == 'SP'
    assert dados_do_animal['castrado'] is False
    assert dados_do_animal['temChip'] is False
    assert dados_do_animal['vacinado'] is False


def test_animal_sem_foto_recebe_a_foto_padrao(client, usuario, animal):
    _tornar_ong(usuario)
    _divulgar(animal)

    _, dados_do_animal = _buscar(client, animal)

    assert dados_do_animal['foto'].startswith('https://')


def test_numero_do_chip_nunca_e_divulgado(client, usuario, animal):
    _tornar_ong(usuario)
    chip = f'CHIP-SECRETO-{uuid.uuid4().hex[:8]}'
    _divulgar(animal, chip=chip)

    resposta = client.get('/api/publico/dados')
    _, dados_do_animal = _buscar(client, animal)

    assert dados_do_animal['temChip'] is True
    assert chip not in resposta.get_data(as_text=True)


def test_vacinado_so_com_vacina_aplicada(client, usuario, animal):
    _tornar_ong(usuario)
    _divulgar(animal)
    _executar(
        "INSERT INTO vacinas (animal_id, nome_vacina, data_vacina, status_vacina, dose_vacina) "
        "VALUES (%s, 'v4', '2026-12-01', 'agendada', 1)",
        (animal,),
    )
    assert _buscar(client, animal)[1]['vacinado'] is False

    _executar(
        "INSERT INTO vacinas (animal_id, nome_vacina, data_vacina, status_vacina, dose_vacina) "
        "VALUES (%s, 'v4', '2026-10-01', 'aplicada', 1)",
        (animal,),
    )
    assert _buscar(client, animal)[1]['vacinado'] is True


def test_protetor_independente_vai_para_o_cartao_agrupado_sem_nome(client, usuario, animal):
    _executar(
        "UPDATE usuarios SET nome = 'Nome Reservado Pytest', telefone = '19999990000', "
        "cidade = 'Santos', uf = 'SP' WHERE id = %s",
        (usuario,),
    )
    _divulgar(animal)

    resposta = client.get('/api/publico/dados')
    ong, dados_do_animal = _buscar(client, animal)

    assert ong['id'] == 0
    assert ong['nome'] == 'Protetores independentes'
    assert dados_do_animal['cidade'] == 'Santos'
    texto = resposta.get_data(as_text=True)
    assert 'Nome Reservado Pytest' not in texto
    assert '19999990000' not in texto


def test_so_a_lista_fixa_de_campos_e_divulgada(client, usuario, animal):
    _tornar_ong(usuario)
    _divulgar(animal)

    ong, dados_do_animal = _buscar(client, animal)

    assert set(ong) == {
        'id', 'nome', 'icone', 'regiao', 'cidade', 'estado', 'resumo',
        'descricao', 'linkFormulario', 'animais', 'campanhas',
    }
    assert set(dados_do_animal) == {
        'id', 'nome', 'especie', 'raca', 'idade', 'foto', 'castrado',
        'temChip', 'vacinado', 'infoSaude', 'cidade', 'estado',
    }
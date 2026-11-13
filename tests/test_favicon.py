def test_favicon_e_servido(client):
    resposta = client.get('/favicon.ico')

    assert resposta.status_code == 200
    assert resposta.mimetype == 'image/vnd.microsoft.icon'
    assert resposta.data[:4] == b'\x00\x00\x01\x00'  # começo de todo arquivo .ico
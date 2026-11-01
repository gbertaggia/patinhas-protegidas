# Patinhas Protegidas: testes

Este documento registra como o sistema é testado, o que já foi verificado, os resultados e as medições. Deve ser atualizado a cada etapa nova.

Última atualização: 01/11/2026.

## 1. Estratégia

| Tipo | Como é feito | Situação |
|---|---|---|
| Funcional manual | uso das telas e das rotas, com duas contas (uma em janela normal e outra em janela anônima) | realizado a cada etapa |
| Controle de acesso | rotas sem login, registros de outra conta, API sem login | realizado (manual e automatizado) |
| Validação de entradas | valores, datas, filtros e textos inválidos | realizado (manual e automatizado) |
| Automatizado (`pytest`) | testes em Python que chamam a API, as páginas e o cadastro e conferem as respostas | 69 testes, todos passando |
| Banco de dados | conferência das migrações e da restauração de backup com consultas SQL | realizado |
| Não funcional | responsividade em celular, acessibilidade (WCAG 2.2) e latência do banco | planejado |

## 2. Testes manuais realizados

### 2.1 Segurança do back-end (Fase 1)

Feitos com duas contas, primeiro no computador e depois no site publicado.

| Área | Teste | Resultado |
|---|---|---|
| Senha | login com conta antiga | entrou e a senha foi convertida em hash |
| Senha | cadastro e login com conta nova | funcionou, hash visível no banco |
| Senha | senha errada | alerta de falha |
| Acesso | rotas sem login | voltam para a tela de login |
| Acesso | animal ou registro de outra conta | erro 404 |
| Acesso | registro de uma conta com animal de outra na URL | erro 404, registro intacto |
| Fluxo | cadastrar, editar e apagar animal, vacina, medicamento, consulta e histórico | funcionou, datas no padrão brasileiro |
| Castração | marcar e desmarcar na edição, reabrir | valor e data corretos |
| Chip | chip duplicado | alerta de chip já cadastrado |
| Erros | nome com mais de 100 letras | mensagem simples na tela, erro completo só no terminal |
| Medicação | alterar a frequência e reabrir | frequência salva e exibida |
| Configuração | com e sem `FLASK_DEBUG=1` | depurador só aparece quando pedido |

### 2.2 Banco de dados

| Teste | Resultado |
|---|---|
| Número de usuários após restaurar o backup no novo serviço | 17, igual ao original |
| Migração 001: contagem de categorias | 14 |
| Migração 001: coluna `valor` em vacinas, medicamentos, consultas e transacoes | presente nas quatro tabelas |
| Migração 001: regra das chaves estrangeiras de `transacoes` | três chaves, todas com `RESTRICT` |
| Cadastro de vacina depois da migração | funcionou normalmente |
| Migração 002: colunas `tipo` e `cidade` em `usuarios`, `visivel_publico` e `info_saude` em `animais` | presentes, com os tipos e padrões esperados |
| Migração 002: contas existentes | 19 contas, todas `PROTETOR` |
| Migração 002: animais existentes | 22 animais, todos com `visivel_publico = 0` (nenhum fica público sem a pessoa marcar) |
| Migração 002: testes automatizados das páginas, depois de aplicada | 7 passaram |

### 2.3 API do Pet Finanças

Feitos no navegador (console com `fetch` e endereços na barra), logada.

| Teste | Resultado |
|---|---|
| Despesa geral, despesa de um animal e receita | 201, tipo definido pela categoria |
| Valor zero, valor `"abc"` e categoria inexistente | 400, com mensagem explicando |
| Animal de outra conta | 404 |
| Chamada sem login | 401 |
| Listagem sem filtro e com cada filtro (tipo, animal, categoria, período, limite) | conforme o esperado |
| Filtros inválidos (tipo, data, período invertido, limite) | 400, com mensagem |
| Listagem e resumo com uma segunda conta | lista vazia e totais zerados |
| Resumo com os dados de teste | receitas 100,00; despesas 115,50; saldo -15,50 |

### 2.4 Tela de finanças (JavaScript)

Feitos no navegador, na página `/financas` do sistema rodando localmente.

| Teste | Resultado |
|---|---|
| Totais e lista de lançamentos conferidos com os dados do banco | receitas 100,00; despesas 115,50; saldo -15,50; quatro linhas com data no padrão brasileiro e "Geral" nos lançamentos sem animal |
| Segunda conta, sem lançamentos | totais em R$ 0,00 e a mensagem "Nenhum lançamento ainda." |
| Página sem login | redireciona para a tela de login |
| Lançamentos registrados pelo formulário (despesas e receita com animal) | aparecem na tabela e entram nos totais |
| Descrição com código HTML (`<b>oi</b>`) | exibida como texto literal na tabela, sem ser interpretada |
| Valor igual a zero | mensagem de erro do servidor, mostrada acima do formulário |
| Simulação de celular (modo dispositivo do navegador) | cartões e campos empilham; a tabela ganha rolagem horizontal; nada estoura a tela |
| Celular real, pelo site publicado no Render (botão Finanças, cartões, formulário, registro de lançamento e tabela) | funcionou normalmente |

### 2.5 Painel financeiro na página do animal

Feitos no navegador, com o sistema rodando localmente.

| Teste | Resultado |
|---|---|
| Cartão "Finanças" na Página Pet | mostra só os lançamentos daquele animal; para o SURURU, receitas 5,00, despesas 80,00 e saldo -75,00 |
| Tabela do cartão | três colunas (data, categoria com a descrição em letra pequena abaixo, e valor), para caber em telas de celular |
| Lançamento registrado pelo cartão (despesa de medicamento) | aparece na lista do animal e entra nos totais |
| Simulação de celular | o cartão ocupa a largura toda; sinal e valor ficam na mesma linha e as três colunas cabem na tela |
| Celular real, pelo site publicado no Render (cartão Finanças, tabela, formulário e registro de lançamento) | funcionou normalmente |
| Celular real: voltar da Página Pet ao painel | **falha encontrada**: não havia botão de voltar visível (o menu da barra de topo fica recolhido em telas pequenas, sem botão para abri-lo) |
| Simulação de celular, depois da correção | link "Voltar ao Painel" visível abaixo do nome do sistema |
| Tela larga, depois da correção | continua aparecendo um único "Voltar ao Painel" |
| Celular real, depois da correção publicada no Render | o link "Voltar ao Painel" aparece e leva ao painel |

### 2.6 Exclusão de animal que tem lançamentos

Feito no navegador, com o sistema rodando localmente.

| Teste | Resultado |
|---|---|
| Apagar o animal SURURU, que tem lançamentos financeiros | mensagem "Este animal não pode ser apagado", com link de volta; o animal continua no painel |

### 2.7 Cadastro com perfil, cidade e estado

Feitos no navegador, com o sistema rodando localmente. As contas de teste foram apagadas depois.

| Teste | Resultado |
|---|---|
| Migração 003: coluna `uf` em `usuarios` | gravada junto com a cidade no cadastro |
| Cadastro como ONG, com cidade e estado | conta criada com `tipo = ONG`, cidade e `uf` corretos, e entrada no painel |
| Escolha do perfil no formulário | nenhuma opção marcada no começo; o navegador exige a escolha |
| Rótulo do campo de nome | muda para "Nome da ONG" ou "Seu nome completo" conforme o perfil |
| Formulário em tela de celular | cabe sem corte, com o botão "Criar Conta" visível |
| Cadastro no site publicado (Render) | a tela `/cadastro` nova abre normalmente |

### 2.8 Edição do perfil

Feito no navegador, com o sistema rodando localmente.

| Teste | Resultado |
|---|---|
| Editar o perfil de uma conta (perfil, nome, cidade e estado) | alterações gravadas, conferidas no banco: `tipo = ONG`, cidade e `uf` preenchidos |

### 2.9 API pública dos animais

Feito no navegador, com o sistema rodando localmente. O animal usado voltou ao estado original depois.

| Teste | Resultado |
|---|---|
| Marcar um animal de teste como divulgado (`visivel_publico = 1`) e abrir `/api/publico/dados` **sem estar logada** | resposta 200 em JSON, com o animal dentro do cartão "Protetores independentes" |
| Campos do animal na resposta | só os previstos: nome, espécie, raça, idade, foto, castrado, `temChip`, `vacinado`, `infoSaude`, cidade e estado |
| Dados que não podem sair | número do chip, telefone, e-mail, nome da pessoa e histórico não aparecem em lugar nenhum da resposta |
| `temChip` e `vacinado` | `temChip: true` (o animal tem chip, mas o número não vai); `vacinado: false` (não há vacina aplicada) |
| Desfazer a divulgação (`visivel_publico = 0`) | o animal deixa de aparecer |

### 2.10 Formulário do animal: divulgação e informações de saúde

Feito no navegador, com o sistema rodando localmente, na conta principal do grupo. A divulgação foi desfeita no fim.

| Teste | Resultado |
|---|---|
| Cadastro de animal numa conta **sem** cidade e estado | a opção "Divulgar" aparece desabilitada, com o aviso e o link para "Meu perfil" |
| Preencher cidade e estado em "Meu perfil" e voltar ao cadastro | a opção "Divulgar" fica habilitada, com o texto que explica o que os visitantes veem |
| Tela de edição de um animal que já tinha texto de saúde | o campo vem preenchido com o que estava salvo |
| Editar o animal, marcar "Divulgar" e salvar; abrir `/api/publico/dados` | o animal aparece no cartão dos protetores independentes, com cidade, estado e texto de saúde, `temChip: true` e sem o número do chip |
| Editar de novo, desmarcar "Divulgar" e salvar | o animal some da API pública |

## 3. Testes automatizados (pytest)

### 3.1 Como rodar

Com a venv ativa e o `.env` configurado, na raiz do projeto:

```
pip install -r requirements-dev.txt
pytest -v
```

A configuração está em `pytest.ini`. Os testes ficam em `tests/`.

### 3.2 Como funcionam

- Cada teste é uma função `test_...` que chama a API como um navegador e confere a resposta com `assert`.
- As **fixtures** (em `tests/conftest.py`) preparam e limpam o cenário: criam uma pessoa de teste no banco (e-mail iniciado em `pytest_`), um animal quando preciso, e fazem o login simulado. No fim de cada teste, apagam tudo o que foi criado (transações, animais e usuário). Nos testes do cadastro, que criam contas pela própria tela, a fixture `emails_de_teste` guarda os e-mails usados e apaga essas contas no fim.
- Como só existe um banco, os testes nunca limpam tabelas inteiras: removem só os registros que eles mesmos criaram. Os dados reais do grupo não são tocados.

### 3.3 O que é testado (90 testes)

Os testes de finanças, da página do animal e da exclusão ficam em `tests/test_financas_api.py`, os do cadastro em `tests/test_cadastro.py`, os da edição do perfil em `tests/test_perfil.py`, os da API pública em `tests/test_publico.py` e os da divulgação pelo formulário do animal em `tests/test_divulgacao.py`.

| Assunto | Teste | O que verifica |
|---|---|---|
| Categorias | `test_categorias_exige_login` | sem login, 401 |
| Categorias | `test_categorias_lista_receitas_e_despesas` | logada, devolve ao menos 14 categorias dos dois tipos |
| Lançamento | `test_lancar_exige_login` | sem login, 401 |
| Lançamento | `test_despesa_tem_tipo_definido_pela_categoria` | 201, tipo DESPESA, valor "25,50" gravado como 25.50 |
| Lançamento | `test_receita_tem_tipo_definido_pela_categoria` | 201, tipo RECEITA |
| Lançamento | `test_valor_invalido_e_recusado` (5 casos) | 0, -5, "abc", vazio e acima do limite dão 400 |
| Lançamento | `test_categoria_inexistente_e_recusada` | 400 |
| Lançamento | `test_corpo_que_nao_e_json_e_recusado` | 400 |
| Lançamento | `test_lancar_em_animal_proprio` | 201 |
| Lançamento | `test_lancar_em_animal_de_outra_conta_e_recusado` | 404 e nada gravado |
| Lançamento | `test_lancar_em_animal_inexistente_e_recusado` | 404 |
| Listagem | `test_listagem_filtra_por_tipo` | filtro por RECEITA devolve só receitas |
| Listagem | `test_listagem_filtra_por_periodo` | filtro de data devolve só o período |
| Listagem | `test_listagem_so_mostra_dados_do_proprio_usuario` | outra conta vê lista vazia |
| Listagem | `test_filtros_invalidos_sao_recusados` (7 casos) | tipo, datas, período invertido, limites e ids inválidos dão 400 |
| Listagem | `test_listagem_filtra_por_animal_e_por_geral` | `animal_id=N` e `animal_id=geral` separam corretamente |
| Resumo | `test_resumo_exige_login` | sem login, 401 |
| Resumo | `test_resumo_calcula_totais_e_saldo` | receitas 100,00; despesas 35,50; saldo 64,50; 3 categorias |
| Resumo | `test_resumo_vazio_para_quem_nao_tem_lancamentos` | tudo zerado e sem categorias |
| Resumo | `test_resumo_nao_mistura_dados_de_outra_conta` | outra conta vê zeros |
| Resumo | `test_resumo_filtra_por_animal_e_por_geral` | totais separados por animal e geral |
| Página | `test_pagina_financas_exige_login` | sem login, redireciona para a tela de login |
| Página | `test_pagina_financas_abre_para_quem_esta_logado` | logada, a página abre (200) |
| Página | `test_pagina_financas_lista_os_animais_do_proprio_usuario` | o formulário traz os animais da pessoa |
| Página | `test_pagina_financas_nao_lista_animal_de_outra_conta` | animal de outra conta não aparece |
| Página do animal | `test_pagina_do_animal_mostra_o_painel_financeiro` | a Página Pet traz o painel, ligado ao id do animal |
| Página do animal | `test_pagina_do_animal_de_outra_conta_da_404` | animal de outra conta responde 404 |
| Página do animal | `test_pagina_do_animal_tem_link_para_voltar_ao_painel_no_celular` | a página traz um link para `/painel` visível em telas pequenas |
| Exclusão de animal | `test_animal_com_lancamentos_nao_pode_ser_apagado` | animal com lançamento: resposta 409 com a mensagem, e o animal continua existindo |
| Exclusão de animal | `test_animal_sem_lancamentos_continua_podendo_ser_apagado` | animal sem lançamentos: redireciona (302) e a página do animal passa a dar 404 |
| Cadastro | `test_tela_de_cadastro_traz_perfil_e_estados` | o formulário traz as opções Protetor(a) e ONG e a lista de estados |
| Cadastro | `test_cadastro_grava_perfil_cidade_e_estado` (2 casos) | PROTETOR e ONG: redireciona para o painel e grava perfil, cidade e estado |
| Cadastro | `test_cadastro_invalido_e_recusado` (10 casos) | perfil inválido ou vazio, estado inválido ou vazio, cidade vazia, só com espaços ou com mais de 100 letras, nome vazio ou com mais de 100 letras e senha vazia dão 400 e não gravam nada |
| Cadastro | `test_cadastro_sem_escolher_o_perfil_e_recusado` | sem o campo do perfil, 400 e nada gravado |
| Cadastro | `test_email_repetido_continua_sendo_recusado` | segundo cadastro com o mesmo e-mail é barrado |
| Edição do perfil | `test_editar_perfil_exige_login` | sem login, redireciona para a tela de login |
| Edição do perfil | `test_editar_perfil_grava_os_novos_dados` | grava nome, telefone, perfil, cidade e estado |
| Edição do perfil | `test_telefone_vazio_vira_nulo` | telefone em branco é gravado como vazio (NULL) |
| Edição do perfil | `test_tela_de_edicao_mostra_os_dados_salvos` | a tela abre com a cidade que foi salva |
| Edição do perfil | `test_edicao_invalida_e_recusada` (9 casos) | perfil, estado, cidade e nome inválidos dão 400 e os dados da conta não mudam |
| Edição do perfil | `test_editar_perfil_nao_altera_a_conta_de_outra_pessoa` | a edição só afeta a conta de quem está logada |
| API pública | `test_dados_publicos_nao_exigem_login` | sem login, responde 200 com a lista de ONGs e os valores de doação |
| API pública | `test_animal_nao_divulgado_nao_aparece` | animal com `visivel_publico = 0` não aparece |
| API pública | `test_animal_divulgado_por_ong_aparece_no_cartao_da_ong` | animal de conta ONG aparece no cartão da ONG, com os dados esperados |
| API pública | `test_animal_sem_foto_recebe_a_foto_padrao` | sem foto cadastrada, a resposta traz a imagem padrão |
| API pública | `test_numero_do_chip_nunca_e_divulgado` | com chip cadastrado, só `temChip` sai; o número não aparece na resposta |
| API pública | `test_vacinado_so_com_vacina_aplicada` | vacina agendada não conta; ao ficar `aplicada`, `vacinado` vira verdadeiro |
| API pública | `test_protetor_independente_vai_para_o_cartao_agrupado_sem_nome` | nome e telefone da pessoa não aparecem; o animal vai para o cartão "Protetores independentes" |
| API pública | `test_so_a_lista_fixa_de_campos_e_divulgada` | as chaves do animal e do cartão são exatamente as permitidas (trava contra vazamento de campo novo) |
| Divulgação | `test_tela_de_cadastro_libera_a_divulgacao_com_cidade_e_estado` | com cidade e estado, a opção de divulgar vem habilitada, junto com o campo de saúde |
| Divulgação | `test_tela_de_cadastro_bloqueia_a_divulgacao_sem_cidade_e_estado` | sem eles, a opção vem desabilitada e a tela traz o link para o perfil |
| Divulgação | `test_tela_de_edicao_mostra_o_que_esta_salvo` | a edição traz o texto de saúde e a opção marcada, como salvos |
| Divulgação | `test_cadastrar_animal_com_divulgacao` | grava `visivel_publico = 1` e o texto de saúde, sem os espaços das pontas |
| Divulgação | `test_cadastrar_animal_sem_marcar_nao_divulga` | sem marcar, grava 0 e texto vazio (NULL) |
| Divulgação | `test_divulgar_sem_cidade_e_estado_e_recusado` | resposta 400 e nenhum animal gravado |
| Divulgação | `test_cadastrar_sem_divulgar_funciona_mesmo_sem_cidade_e_estado` | cadastrar sem divulgar continua permitido para quem não tem cidade e estado |
| Divulgação | `test_limite_do_texto_de_saude` (2 casos) | 500 caracteres é aceito; 501 dá 400 e nada é gravado |
| Divulgação | `test_editar_animal_liga_e_desliga_a_divulgacao` | marcar divulga; salvar de novo sem marcar tira da página pública |
| Divulgação | `test_editar_para_divulgar_sem_cidade_e_estado_e_recusado` | 400 e o animal continua não divulgado |
| Divulgação | `test_nao_divulga_animal_de_outra_conta` | outra pessoa não consegue divulgar nem alterar o texto do animal alheio |
| Divulgação | `test_animal_divulgado_pelo_formulario_aparece_na_api_publica` | de ponta a ponta: animal cadastrado com divulgação aparece na API, sem login, com cidade, estado e texto, e o número do chip não sai |

### 3.4 Resultado

Última execução completa: **90 passaram em 500,86 s** (8 min 20 s).

## 4. Medições

| Execução | Testes | Tempo total | Média por teste |
|---|---|---|---|
| 31/10/2026, primeira versão | 26 | 128,07 s | 4,9 s |
| 31/10/2026, com testes de animais | 31 | 177,54 s | 5,7 s |
| 31/10/2026, com testes da página de finanças | 35 | 204,21 s | 5,8 s |
| 31/10/2026, com testes da página do animal | 37 | 222,77 s | 6,0 s |
| 31/10/2026, com o teste do link de voltar | 38 | 232,48 s | 6,1 s |
| 31/10/2026, com os testes de exclusão de animal | 40 | 252,21 s | 6,3 s |
| 01/11/2026, com os testes do cadastro | 54 | 287,44 s | 5,3 s |
| 01/11/2026, com os testes da edição do perfil | 69 | 364,06 s | 5,3 s |
| 01/11/2026, com os testes da API pública | 77 | 405,15 s | 5,3 s |
| 01/11/2026, com os testes da divulgação no formulário do animal | 90 | 500,86 s | 5,6 s |

Os testes rodam contra o banco hospedado na nuvem (Aiven), e cada teste abre várias conexões (criar o usuário, lançar, consultar e limpar). O tempo é, portanto, dominado pela comunicação com o banco. Esses números são apenas um indício: não separam a latência de conexão da latência de consulta. A medição específica de latência, prevista no relatório, ainda será feita.

## 5. O que ainda não está coberto

- Lançamentos automáticos a partir de vacinas, medicamentos e consultas com valor.
- O JavaScript da tela de finanças e o da página pública (hoje verificados só manualmente).
- Filtros e gráfico na tela de finanças.
- Testes automatizados do login e das rotas de animais e saúde (o cadastro e a edição de perfil já são cobertos; o restante só por testes manuais).
- Testes não funcionais: acessibilidade (WCAG 2.2) e medição de latência. A responsividade da página de finanças e da Página Pet já foi verificada em celular real (seções 2.4 e 2.5).
- Campanhas e integração com o Pix.

## 6. Limpeza de resíduos

Se uma execução for interrompida no meio (por exemplo, com Ctrl+C, ou porque a internet caiu), pode sobrar uma pessoa de teste no banco. Isso aconteceu uma vez, em 01/11/2026: a conexão com o banco caiu no fim da rodada completa, três testes deram erro de conexão (`getaddrinfo failed` e *timeout*), e a limpeza de um deles não rodou, deixando uma conta de teste com um animal marcado como divulgado. Esse resíduo era perigoso porque o animal de teste apareceria na página pública real. Foi removido com o SQL abaixo e a rodada completa foi repetida, com sucesso. Lição: como os testes dependem de uma conexão estável com a nuvem, um erro de rede não indica falha do código. Para repetir só os que falharam, use `pytest --lf`.

Para remover resíduos, no MySQL Workbench:

```sql
SET SQL_SAFE_UPDATES = 0;

DELETE t FROM transacoes t
JOIN usuarios u ON u.id = t.usuario_id
WHERE u.email LIKE 'pytest\_%@exemplo.invalido';

DELETE FROM usuarios WHERE email LIKE 'pytest\_%@exemplo.invalido';
```

A segunda linha também apaga os animais (e suas vacinas) dessas pessoas, porque a chave estrangeira de `animais` é em cascata. A primeira vem antes porque as transações têm `RESTRICT`.

Para conferir se ficou algo para trás, as duas consultas abaixo devem voltar **sem nenhuma linha de teste**:

```sql
SELECT id, email FROM usuarios WHERE email LIKE 'pytest\_%@exemplo.invalido';
SELECT id, nome, usuario_id FROM animais WHERE visivel_publico = 1;
```

(A segunda lista os animais divulgados de verdade; só não pode haver animal de teste nela.)

## 7. Como acrescentar um teste

1. Escreva uma função `test_...` em `tests/test_financas_api.py` (ou em um arquivo novo `tests/test_*.py`).
2. Peça as fixtures de que precisa pelos parâmetros: `client` (sem login), `client_logado`, `outro_client`, `animal`, `animal_de_outro`.
3. Rode `pytest -v` e confira.
4. Atualize a tabela da seção 3.3 e o resultado da seção 3.4.

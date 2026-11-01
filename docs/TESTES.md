# Patinhas Protegidas: testes

Este documento registra como o sistema é testado, o que já foi verificado, os resultados e as medições. Deve ser atualizado a cada etapa nova.

Última atualização: 31/10/2026.

## 1. Estratégia

| Tipo | Como é feito | Situação |
|---|---|---|
| Funcional manual | uso das telas e das rotas, com duas contas (uma em janela normal e outra em janela anônima) | realizado a cada etapa |
| Controle de acesso | rotas sem login, registros de outra conta, API sem login | realizado (manual e automatizado) |
| Validação de entradas | valores, datas, filtros e textos inválidos | realizado (manual e automatizado) |
| Automatizado (`pytest`) | testes em Python que chamam a API e a página de finanças e conferem as respostas | 40 testes, todos passando |
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
- As **fixtures** (em `tests/conftest.py`) preparam e limpam o cenário: criam uma pessoa de teste no banco (e-mail iniciado em `pytest_`), um animal quando preciso, e fazem o login simulado. No fim de cada teste, apagam tudo o que foi criado (transações, animais e usuário).
- Como só existe um banco, os testes nunca limpam tabelas inteiras: removem só os registros que eles mesmos criaram. Os dados reais do grupo não são tocados.

### 3.3 O que é testado (40 testes)

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

### 3.4 Resultado

Última execução completa: **40 passaram em 252,21 s** (4 min 12 s).

## 4. Medições

| Execução | Testes | Tempo total | Média por teste |
|---|---|---|---|
| 31/10/2026, primeira versão | 26 | 128,07 s | 4,9 s |
| 31/10/2026, com testes de animais | 31 | 177,54 s | 5,7 s |
| 31/10/2026, com testes da página de finanças | 35 | 204,21 s | 5,8 s |
| 31/10/2026, com testes da página do animal | 37 | 222,77 s | 6,0 s |
| 31/10/2026, com o teste do link de voltar | 38 | 232,48 s | 6,1 s |
| 31/10/2026, com os testes de exclusão de animal | 40 | 252,21 s | 6,3 s |

Os testes rodam contra o banco hospedado na nuvem (Aiven), e cada teste abre várias conexões (criar o usuário, lançar, consultar e limpar). O tempo é, portanto, dominado pela comunicação com o banco. Esses números são apenas um indício: não separam a latência de conexão da latência de consulta. A medição específica de latência, prevista no relatório, ainda será feita.

## 5. O que ainda não está coberto

- Lançamentos automáticos a partir de vacinas, medicamentos e consultas com valor.
- O JavaScript da tela de finanças (hoje verificado só manualmente).
- Filtros e gráfico na tela de finanças.
- Testes automatizados das rotas de usuário, animais e saúde (hoje cobertas só por testes manuais).
- Testes não funcionais: acessibilidade (WCAG 2.2) e medição de latência. A responsividade da página de finanças e da Página Pet já foi verificada em celular real (seções 2.4 e 2.5).
- Campanhas e integração com o Pix.

## 6. Limpeza de resíduos

Se uma execução for interrompida no meio (por exemplo, com Ctrl+C), pode sobrar uma pessoa de teste no banco. Para remover, no MySQL Workbench:

```sql
SET SQL_SAFE_UPDATES = 0;

DELETE t FROM transacoes t
JOIN usuarios u ON u.id = t.usuario_id
WHERE u.email LIKE 'pytest\_%@exemplo.invalido';

DELETE FROM usuarios WHERE email LIKE 'pytest\_%@exemplo.invalido';
```

A segunda linha também apaga os animais dessas pessoas, porque a chave estrangeira de `animais` é em cascata. A primeira vem antes porque as transações têm `RESTRICT`.

## 7. Como acrescentar um teste

1. Escreva uma função `test_...` em `tests/test_financas_api.py` (ou em um arquivo novo `tests/test_*.py`).
2. Peça as fixtures de que precisa pelos parâmetros: `client` (sem login), `client_logado`, `outro_client`, `animal`, `animal_de_outro`.
3. Rode `pytest -v` e confira.
4. Atualize a tabela da seção 3.3 e o resultado da seção 3.4.

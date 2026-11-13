# Patinhas Protegidas: testes

Este documento registra como o sistema é testado, o que já foi verificado, os resultados e as medições. Deve ser atualizado a cada etapa nova.

Última atualização: 13/11/2026.

## 1. Estratégia

| Tipo | Como é feito | Situação |
|---|---|---|
| Funcional manual | uso das telas e das rotas, com duas contas (uma em janela normal e outra em janela anônima) | realizado a cada etapa |
| Controle de acesso | rotas sem login, registros de outra conta, API sem login | realizado (manual e automatizado) |
| Validação de entradas | valores, datas, filtros e textos inválidos | realizado (manual e automatizado) |
| Automatizado (`pytest`) | testes em Python que chamam a API, as páginas, o cadastro, o login e a validação de links e conferem as respostas | 180 testes, todos passando |
| Banco de dados | conferência das migrações e da restauração de backup com consultas SQL | realizado |
| Não funcional | responsividade em celular, acessibilidade (WCAG 2.2) e latência do banco | responsividade e contraste de cores (WCAG AA) conferidos nas telas revisadas (seções 2.4, 2.5, 2.11 e 2.12); leitor de tela, teclado e latência do banco: planejados |

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

### 2.11 Página pública: segurança e doação geral

Feitos em 13/11/2026. A verificação de segurança usou um navegador de teste (Chromium sem interface, controlado por script) e uma API simulada com textos maliciosos; a de doação foi feita no navegador, com o sistema rodando localmente.

| Teste | Resultado |
|---|---|
| Textos com código HTML (`<img src=x onerror=...>`) no nome, na região, no resumo e na descrição da ONG, no animal e na campanha, e aspas dentro do endereço da foto | **versão antiga:** o código inserido foi executado; **versão nova:** nada foi executado e o texto aparece literal na tela |
| Link do formulário de adoção com `javascript:...` | a versão nova não cria o link: o botão aparece desativado, "Adoção indisponível" |
| Link do formulário de adoção válido (`https://...`) | botão "Quero Adotar" abre o formulário |
| Foto que não carrega | aparece a imagem padrão, sem ficar em repetição |
| Barra "Ajude a causa" numa organização com campanha geral ativa | os valores sugeridos e "Outro valor" abrem a janela do Pix, já com o valor escolhido |
| Barra "Ajude a causa" numa organização sem campanha geral, e no cartão "Protetores independentes" | a barra não aparece |
| API fora do ar | mensagem de erro na tela, em vez de página vazia |
| Busca por nome ou região | filtra os cartões e atualiza o contador; o texto "Nenhuma organização encontrada" aparece quando nada combina |

### 2.12 Visual, navegação e acesso à conta

Feitos em 13/11/2026, no navegador, com o sistema rodando localmente.

| Teste | Resultado |
|---|---|
| Barra do topo comum no painel, em Finanças, na Página Pet, na página pública, no login, no cadastro e na edição do perfil | mesma barra, logo com a patinha roxa e o item da página atual destacado |
| Barra para quem **não** está logado | botões "Entrar" e "Criar conta"; a frase de convite aparece abaixo do texto de apresentação |
| Barra para quem está logado | menu Painel, Finanças e Campanhas e adoção, saudação com o nome, "Editar perfil" e "Sair"; a frase de convite não aparece |
| Link "← Voltar para campanhas e adoção" no login e no cadastro | leva à página pública |
| Login e cadastro em tela de celular (modo dispositivo, 400 px de largura) | formulários legíveis, sem corte e sem rolagem lateral |
| Rótulos do cadastro ao trocar entre Protetor(a) e ONG | os rótulos do nome, da missão e da logo trocam, como antes |
| Login com senha errada | volta para a tela de login com a faixa "E-mail ou senha incorretos." e o e-mail digitado preenchido |
| Cadastro com senha de 2 caracteres | o navegador barra e pede 8 ou mais |
| Cadastro com e-mail já usado | página de erro no tema, com "Tentar outro e-mail" e "Entrar" |
| Contraste de cores (WCAG AA), por cálculo e por script no navegador de teste | texto amarelo do Bootstrap (1,63:1 no branco) trocado por âmbar escuro (6,92:1); verde da marca 5,48:1 e 8,83:1 (escuro); cinza de apoio da página pública de 4,24:1 para 5,60:1; selo de vacina agendada 6,39:1. Nenhum texto da página pública abaixo de 4,5:1 |

### 2.13 Dados de teste e de demonstração antes da entrega

Feitos em 13/11/2026, no MySQL Workbench, depois de um backup do banco inteiro (Data Export).

| Teste | Resultado |
|---|---|
| Contas de teste automático (`pytest_`) no banco | 0 (a limpeza dos testes está funcionando) |
| Contas que aparecem na página pública com nome real de pessoa | uma conta apagada, com as campanhas, o lançamento e o animal dela (conferido por consulta antes e depois, dentro de uma transação, e só então confirmado) |
| Chaves Pix de demonstração | todas trocadas por chave aleatória (formato UUID v4, que não existe em nenhum banco); a conferência mostrou 36 caracteres em cada uma |
| Logo com imagem de terceiros em uma organização de exemplo | removida; a página mostra a patinha padrão |
| Página pública depois da limpeza | três cartões: duas organizações de exemplo e "Protetores independentes" |

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
- As **fixtures** (em `tests/conftest.py`) preparam e limpam o cenário: criam uma pessoa de teste no banco (e-mail iniciado em `pytest_`), um animal quando preciso, e fazem o login simulado. No fim de cada teste, apagam tudo o que foi criado (transações, animais e usuário). Nos testes do cadastro, que criam contas pela própria tela, a fixture `emails_de_teste` guarda os e-mails usados e apaga essas contas no fim. Nos testes de campanhas, a fixture `campanhas` apaga os avisos de doação e as campanhas criadas antes de a pessoa de teste ser removida, porque a chave estrangeira de `campanhas` é `RESTRICT`; nos testes de links (`test_urls.py`), a fixture `limpar_campanhas` faz o mesmo. Nos testes de acesso (`test_acesso.py`), a conta é criada pelo próprio cadastro e apagada pela fixture `emails_de_teste`, e o login é feito num navegador novo, sem sessão.
- Como só existe um banco, os testes nunca limpam tabelas inteiras: removem só os registros que eles mesmos criaram. Os dados reais do grupo não são tocados.

### 3.3 O que é testado (180 testes)

Os testes de finanças, da página do animal e da exclusão ficam em `tests/test_financas_api.py`, os do cadastro em `tests/test_cadastro.py`, os da edição do perfil em `tests/test_perfil.py`, os da API pública dos animais em `tests/test_publico.py`, os da divulgação pelo formulário do animal em `tests/test_divulgacao.py` os das campanhas e do aviso de doação em `tests/test_publico_campanhas.py`, os do ícone do site em `tests/test_favicon.py`, os da validação de links em `tests/test_urls.py`, os das páginas HTML (barra do topo e arquivos do tema) em `tests/test_paginas.py` e os do login, da senha mínima e das páginas de erro em `tests/test_acesso.py`.

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
| Página do animal | `test_pagina_do_animal_tem_link_para_voltar_ao_painel_no_celular` | o menu da barra do topo, que aparece em todos os tamanhos de tela (no celular passa para uma linha abaixo do logo), traz o link para `/painel` e nada o esconde |
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
| API pública | `test_so_a_lista_fixa_de_campos_e_divulgada` | as chaves do animal e do cartão (agora incluindo `logoUrl`) são exatamente as permitidas (trava contra vazamento de campo novo) |
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
| Campanhas | `test_campanha_de_ong_aparece_no_cartao_com_campos_fixos` | campanha ativa de ONG aparece no cartão da ONG, só com os campos previstos, e o recebedor é o nome da ONG |
| Campanhas | `test_ong_com_campanha_e_sem_animal_divulgado_aparece` | a ONG com campanha ativa aparece mesmo sem animais divulgados |
| Campanhas | `test_campanha_de_protetor_independente_nao_revela_dados_da_pessoa` | o recebedor é "Protetor(a) independente"; nome, telefone e e-mail da pessoa não aparecem |
| Campanhas | `test_chave_pix_aparece_so_dentro_da_campanha` | a chave Pix aparece uma única vez na resposta, dentro da campanha |
| Campanhas | `test_campanha_encerrada_nao_aparece` (2 casos) | campanha concluída ou cancelada não aparece na página pública |
| Cartões | `test_cartao_dos_independentes_nao_usa_logo_nem_link_de_ninguem` | o cartão agrupado usa o formulário do grupo e não tem logo, mesmo que o protetor tenha cadastrado os dois |
| Cartões | `test_ong_usa_o_proprio_formulario_e_logo` | a ONG com link e logo no perfil usa os próprios |
| Cartões | `test_ong_sem_formulario_usa_o_formulario_do_grupo` | a ONG sem link usa o formulário do grupo |
| Aviso de doação | `test_aviso_de_doacao_cria_pendente_sem_mexer_no_arrecadado` | sem login, valor "25,50" cria um aviso pendente (201) e o arrecadado continua zerado |
| Aviso de doação | `test_aviso_com_valor_invalido_e_recusado` (7 casos) | 0, negativo, letras, vazio, acima de R$ 100.000, `NaN` e `Infinity` dão 400 e nada é gravado |
| Aviso de doação | `test_corpo_que_nao_e_objeto_json_e_recusado` | corpo vazio, lista, texto e JSON malformado dão 400 (antes, lista e texto davam 500) |
| Aviso de doação | `test_aviso_em_campanha_inexistente_e_recusado` | 404 |
| Aviso de doação | `test_aviso_em_campanha_encerrada_e_recusado` | 404 e nada gravado |
| Aviso de doação | `test_aviso_tem_limite_de_pendentes_por_campanha` | com 30 avisos pendentes, o seguinte recebe 429 |
| Ícone do site | `tests/test_favicon.py` | `/favicon.ico` responde 200 como imagem |
| Links | `test_link_valido_e_aceito` (5 casos) | `http://` e `https://` são aceitos, com os espaços das pontas removidos |
| Links | `test_link_vazio_vira_none_sem_erro` (4 casos) | vazio, só espaços ou ausente viram "sem link", sem erro |
| Links | `test_link_invalido_e_recusado` (17 casos) | `javascript:`, `data:`, `vbscript:`, `ftp:`, `file:`, sem esquema, `//`, endereço sem servidor, espaço ou quebra de linha no meio, caractere nulo, colchete aberto, número e lista são recusados, com mensagem |
| Links | `test_link_longo_demais_e_recusado`, `test_link_no_limite_e_aceito` | acima do limite de caracteres é recusado; exatamente no limite é aceito |
| Links | `test_cadastro_recusa_link_perigoso` (2 casos), `test_cadastro_aceita_links_https` | logo e formulário com `javascript:` dão 400 e não criam a conta; links `https` são gravados |
| Links | `test_perfil_recusa_link_perigoso` (2 casos), `test_perfil_aceita_links_https` | o mesmo na edição do perfil, sem alterar a conta |
| Links | `test_cadastro_de_animal_recusa_foto_perigosa`, `test_cadastro_de_animal_aceita_foto_https`, `test_edicao_de_animal_recusa_foto_perigosa`, `test_edicao_de_animal_aceita_foto_https` | a foto do animal só aceita `http` e `https`, no cadastro e na edição (nada é alterado se for recusada) |
| Links | `test_campanha_recusa_foto_perigosa`, `test_campanha_aceita_foto_https_ou_sem_foto` (3 casos) | a foto da campanha recusa `javascript:` (400) e aceita `https`, vazio ou ausente |
| Páginas | `test_pagina_interna_abre_com_a_barra_do_topo` (2 casos), `test_pagina_do_animal_abre_com_a_barra_do_topo` | painel, Finanças e Página Pet abrem com a barra comum, o arquivo do tema, um único item destacado e o nome da pessoa |
| Páginas | `test_login_e_cadastro_tem_barra_do_topo_e_volta_para_a_pagina_publica` (2 casos) | login e cadastro abrem com a barra, o tema e o caminho de volta para a página pública |
| Páginas | `test_cadastro_avisa_o_que_fica_publico` | o aviso de privacidade aparece e todos os campos que o servidor lê continuam no formulário |
| Páginas | `test_editar_perfil_abre_com_a_barra_do_topo` | a edição do perfil abre com a barra, "Editar perfil" destacado e todos os campos |
| Páginas | `test_pagina_publica_para_visitante_tem_entrar_e_criar_conta` | visitante vê "Entrar" e "Criar conta", sem menu, e a página não aponta mais para um arquivo CSS que não existe |
| Páginas | `test_pagina_publica_para_quem_esta_logado_tem_o_menu` | quem está logado vê o menu e não vê "Criar conta" |
| Páginas | `test_arquivos_do_tema_existem` (2 casos) | o CSS do tema e o ícone da marca são servidos com o tipo certo |
| Acesso | `test_login_certo_entra_no_painel` | login correto redireciona para o painel |
| Acesso | `test_login_com_senha_errada_mostra_a_mensagem_na_tela` | 401, a mensagem na própria tela, sem `alert()`, com o e-mail preenchido e sem a senha |
| Acesso | `test_login_com_email_inexistente_tem_a_mesma_resposta` | mesma resposta para e-mail inexistente e senha errada, para não revelar quem tem conta |
| Acesso | `test_login_sem_preencher_pede_e_mail_e_senha` (3 casos) | campo faltando dá 400 com a mensagem |
| Acesso | `test_login_nao_executa_o_que_foi_digitado_no_email` | um e-mail com `<script>` volta escapado na tela e não é executado |
| Acesso | `test_cadastro_recusa_senha_curta` (3 casos), `test_cadastro_explica_o_tamanho_minimo_da_senha`, `test_cadastro_aceita_senha_com_oito_caracteres` | senha com menos de 8 caracteres dá 400 e não cria conta; com 8 é aceita |
| Acesso | `test_erro_de_validacao_do_cadastro_usa_a_pagina_no_tema` | erro de validação usa a página do tema, com botão de voltar |
| Acesso | `test_email_repetido_mostra_a_pagina_no_tema_com_opcao_de_entrar` | 409, mensagem "E-mail já cadastrado" e opção de entrar |
| Acesso | `test_erro_do_perfil_usa_a_pagina_no_tema` | link perigoso no perfil dá 400 na página do tema, com link de volta para a edição |

### 3.4 Resultado

Última execução completa (13/11/2026): **180 passaram em 876,43 s** (14 min 36 s).

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
| 12/11/2026, depois de juntar as alterações do grupo (1 teste desatualizado por causa do `logoUrl`) | 90 | 511,84 s | 5,7 s |
| 12/11/2026, com os testes de campanhas e do aviso de doação | 111 | 697,79 s | 6,3 s |
| 13/11/2026, com o ícone do site e a validação de links | 154 | 776,13 s | 5,0 s |
| 13/11/2026, com as páginas, o login e a senha mínima (versão final) | 180 | 876,43 s | 4,9 s |

Os testes rodam contra o banco hospedado na nuvem (Aiven), e cada teste abre várias conexões (criar o usuário, lançar, consultar e limpar). O tempo é, portanto, dominado pela comunicação com o banco. Esses números são apenas um indício: não separam a latência de conexão da latência de consulta. A medição específica de latência, prevista no relatório, ainda será feita.

## 5. O que ainda não está coberto

- Lançamentos automáticos a partir de vacinas, medicamentos e consultas com valor.
- O JavaScript da tela de finanças e o da página pública (hoje verificados só manualmente; o da página pública também foi verificado por um script no navegador de teste, que não faz parte do repositório).
- Filtros e gráfico na tela de finanças.
- Testes automatizados das rotas de animais e saúde (o cadastro, o login, a edição de perfil e a validação de links já são cobertos; o restante só por testes manuais).
- Testes não funcionais: acessibilidade com leitor de tela e navegação só pelo teclado, e medição de latência. O contraste de cores (WCAG AA) foi conferido nas telas revisadas, e a responsividade da página de finanças e da Página Pet foi verificada em celular real (seções 2.4 e 2.5), e a do login e do cadastro, no modo dispositivo do navegador (seção 2.12).
- As telas da campanha, do cadastro e da edição de animal e dos formulários de saúde ainda não usam a barra do topo e o tema comuns; não há teste automatizado para elas além de abrirem sem erro nas rotinas já cobertas.
- Campanhas: a parte pública (campanhas na API e aviso de doação) é coberta; ainda sem teste automatizado estão a criação de campanhas, a confirmação e a recusa de avisos em Finanças, a validação da chave Pix, os gráficos e as jornadas concluídas (só verificados manualmente pelo grupo).

## 6. Limpeza de resíduos

Se uma execução for interrompida no meio (por exemplo, com Ctrl+C, ou porque a internet caiu), pode sobrar uma pessoa de teste no banco. Isso aconteceu uma vez, em 01/11/2026: a conexão com o banco caiu no fim da rodada completa, três testes deram erro de conexão (`getaddrinfo failed` e *timeout*), e a limpeza de um deles não rodou, deixando uma conta de teste com um animal marcado como divulgado. Esse resíduo era perigoso porque o animal de teste apareceria na página pública real. Foi removido com o SQL abaixo e a rodada completa foi repetida, com sucesso. Lição: como os testes dependem de uma conexão estável com a nuvem, um erro de rede não indica falha do código. Para repetir só os que falharam, use `pytest --lf`.

Para remover resíduos, no MySQL Workbench:

```sql
SET SQL_SAFE_UPDATES = 0;

DELETE d FROM doacoes_informadas d
JOIN campanhas c ON c.id = d.campanha_id
JOIN usuarios u ON u.id = c.usuario_id
WHERE u.email LIKE 'pytest\_%@exemplo.invalido';

DELETE c FROM campanhas c
JOIN usuarios u ON u.id = c.usuario_id
WHERE u.email LIKE 'pytest\_%@exemplo.invalido';

DELETE t FROM transacoes t
JOIN usuarios u ON u.id = t.usuario_id
WHERE u.email LIKE 'pytest\_%@exemplo.invalido';

DELETE FROM usuarios WHERE email LIKE 'pytest\_%@exemplo.invalido';
```

A última linha também apaga os animais (e suas vacinas) dessas pessoas, porque a chave estrangeira de `animais` é em cascata. As outras vêm antes, e nessa ordem, porque campanhas e transações têm `RESTRICT` sobre o usuário, e os avisos de doação pendem das campanhas.

Para conferir se ficou algo para trás, as consultas abaixo devem voltar **sem nenhuma linha de teste**:

```sql
SELECT id, email FROM usuarios WHERE email LIKE 'pytest\_%@exemplo.invalido';
SELECT id, nome, usuario_id FROM animais WHERE visivel_publico = 1;
SELECT c.id, c.titulo FROM campanhas c
JOIN usuarios u ON u.id = c.usuario_id
WHERE u.email LIKE 'pytest\_%@exemplo.invalido';
```

(A segunda lista os animais divulgados de verdade; só não pode haver animal de teste nela.)

### Dados de demonstração e chaves Pix

Antes da entrega, as chaves Pix de teste foram trocadas por chaves aleatórias, porque a chave aparece na página pública, dentro das campanhas, e um endereço de e-mail ou telefone de teste poderia receber doações de verdade. A troca foi feita no Workbench, dentro de uma transação (`START TRANSACTION`, com `COMMIT` só depois de conferir), depois de um backup. O formato é o de uma chave aleatória do Pix (UUID versão 4), gerada pelo próprio MySQL:

```sql
UPDATE usuarios
SET chave_pix = LOWER(CONCAT(
      HEX(RANDOM_BYTES(4)), '-', HEX(RANDOM_BYTES(2)), '-4',
      SUBSTRING(HEX(RANDOM_BYTES(2)), 2), '-',
      ELT(1 + FLOOR(RAND() * 4), '8', '9', 'a', 'b'), SUBSTRING(HEX(RANDOM_BYTES(2)), 2), '-',
      HEX(RANDOM_BYTES(6))))
WHERE id IN (/* ids das contas de demonstração */);
```

A chave tem o formato certo, mas não existe em nenhum banco: se alguém tentar pagar pelo QR Code da demonstração, o banco recusa.

## 7. Como acrescentar um teste

1. Escreva uma função `test_...` em `tests/test_financas_api.py` (ou em um arquivo novo `tests/test_*.py`).
2. Peça as fixtures de que precisa pelos parâmetros: `client` (sem login), `client_logado`, `outro_client`, `animal`, `animal_de_outro`.
3. Rode `pytest -v` (ou `pytest`, para uma saída mais curta) e confira.
4. Atualize a tabela da seção 3.3 e o resultado da seção 3.4.

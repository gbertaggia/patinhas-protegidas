# Patinhas Protegidas: documentação de desenvolvimento

Este documento registra como o sistema está organizado, o que foi feito desde a refatoração do back-end e quais decisões foram tomadas. Ele deve ser atualizado a cada etapa concluída.

Última atualização: 31/10/2026.

## 1. Visão geral

O Patinhas Protegidas é uma aplicação web em Flask (Python) para protetoras e ONGs de animais. Cada pessoa cadastrada controla seus animais, com saúde (vacinas, medicamentos, consultas e histórico veterinário). O módulo **Pet Finanças**, em desenvolvimento, acrescenta o controle de receitas e despesas.

O sistema tem três camadas:

| Camada | O que é | Onde está |
|---|---|---|
| Banco de dados | MySQL 8.4 hospedado no Aiven | fora do repositório; mudanças registradas em `database/migrations/` |
| Back-end | Python/Flask: regras de negócio, acesso ao banco, segurança | `app.py`, `config.py`, `routes/`, `utils/`, `database/` |
| Telas | HTML (Jinja2) com Bootstrap e JavaScript | `templates/`, `static/` |

A aplicação publicada roda no Render e é atualizada automaticamente a cada alteração na branch `main` do GitHub.

## 2. Estrutura de pastas

```
app.py                  cria a aplicação, registra os blueprints e a página pública (/)
config.py               lê o arquivo .env e valida as variáveis obrigatórias
.env                    segredos locais (NUNCA vai para o GitHub)
.env.example            lista os nomes das variáveis, com valores fictícios
database/
  connection.py         função conectar_banco()
  migrations/           mudanças no banco, em arquivos numerados
routes/
  auth.py               login, cadastro, logout e edição do perfil
  animais.py            painel e cadastro, edição e exclusão de animais
  saude.py              vacinas, medicamentos, consultas e histórico veterinário
  financas.py           Pet Finanças (API em JSON)
utils/
  auth.py               controle de acesso (login e dono do registro)
templates/              páginas HTML
static/                 JavaScript e dados da página pública
tests/                  testes automatizados (pytest)
docs/                   documentação do projeto
pytest.ini              configuração do pytest
requirements-dev.txt    dependências de desenvolvimento (inclui o pytest)
```

Um **blueprint** é um grupo de rotas de um mesmo assunto. Em vez de manter todas as rotas num único arquivo, cada assunto tem o seu arquivo, e o `app.py` apenas os registra.

## 3. Como rodar localmente

1. Ative o ambiente virtual (`venv`) e instale as dependências com `pip install -r requirements.txt`.
2. Crie o arquivo `.env` a partir do `.env.example`, com os valores reais: `SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `DB_PORT`. Se alguma estiver faltando, o `config.py` interrompe a inicialização e lista quais faltam.
3. Rode `python app.py` e abra `http://127.0.0.1:5001`.

O modo de depuração (`debug`) fica **desligado** por padrão. Só liga com `FLASK_DEBUG=1`.

## 4. O que foi feito, em ordem

### 4.1 Segurança do back-end
- **Senhas com hash.** As senhas deixaram de ser guardadas em texto puro e passaram a usar `generate_password_hash`/`check_password_hash` (Werkzeug, algoritmo scrypt). Contas antigas, que ainda tinham senha em texto puro, são convertidas para hash no primeiro login bem-sucedido.
- **Controle de acesso.** Toda rota de dados exige login (`login_required`). Além disso, cada acesso a um animal ou a um registro de saúde confere se ele pertence à pessoa logada (`animal_do_usuario` e `registro_do_usuario`). Quando não pertence, a resposta é 404 ("não encontrado") e não 403 ("proibido"), para não revelar que o registro existe.
- **Erros.** Os detalhes técnicos dos erros vão para o log do servidor e não aparecem para a pessoa usuária.
- **Segredos fora do código.** A `SECRET_KEY` e os dados do banco ficam no `.env` (local) e nas variáveis de ambiente do Render (produção).

### 4.2 Refatoração do `app.py`
O arquivo tinha cerca de mil linhas. Foi dividido em módulos (seção 2) e hoje tem cerca de 25 linhas. Os endereços do site não mudaram. Mudaram só os nomes internos usados nos templates, que agora levam o prefixo do blueprint (`url_for('animais.pagina_animal', ...)`).

Correções feitas durante a refatoração:
- a frequência do medicamento passou a ser salva também na edição;
- a data de castração só é gravada quando o animal está marcado como castrado;
- o aviso de chip duplicado foi mantido;
- os redirecionamentos para a tela de login passaram a apontar para `/login`, porque `/` agora é a página pública.

As mudanças foram publicadas por Pull Requests, uma branch por assunto, até o PR #16.

### 4.3 Migração do banco para um novo serviço
O serviço antigo do Aiven rodava MySQL 8.0, que chegou ao fim do suporte em 31/10/2026, e não pôde mais ser ligado. Foi criado um serviço novo com MySQL 8.4, os dados foram restaurados a partir de um backup (17 usuários conferidos) e o `.env` local e as variáveis do Render foram atualizados. O trial do Aiven termina por volta de 30/11/2026, e há um lembrete agendado para 20/11 para decidir o plano.

Um backup do banco, feito em 31/10/2026 antes da migração 001, existe fora da pasta do projeto.

### 4.4 Pet Finanças: banco de dados (migração 001, PR #17)
O arquivo `database/migrations/001_pet_financas.sql` fez três mudanças:
1. Acrescentou a coluna `valor` (`DECIMAL(10,2)`, padrão 0.00) em `vacinas`, `medicamentos` e `consultas`.
2. Criou a tabela `categorias`, com 14 categorias fixas: 11 de despesa (Vacina, Consulta, Medicamento, Castração, Exame, Cirurgia, Alimentação, Higiene e limpeza, Aluguel e contas, Transporte, Outros) e 3 de receita (Doação via Pix, Doação direta, Outras receitas).
3. Recriou a tabela `transacoes`, que estava vazia.

Estrutura da tabela `transacoes`:

| Coluna | Para que serve |
|---|---|
| `usuario_id` | quem registrou o lançamento |
| `animal_id` | animal ao qual o gasto pertence; vazio significa lançamento geral |
| `categoria_id` | categoria (ligada à tabela `categorias`) |
| `tipo` | RECEITA ou DESPESA |
| `valor` | valor positivo, em reais |
| `descricao` | texto livre opcional, até 255 caracteres |
| `data_transacao` | data do lançamento |
| `origem_tipo`, `origem_id` | de onde veio o lançamento: MANUAL ou o registro de saúde que o gerou |

### 4.5 Pet Finanças: back-end (em andamento, branch `pet-financas-backend`)

| Endpoint | O que faz | Situação |
|---|---|---|
| `GET /api/categorias` | lista as categorias | feito e testado |
| `POST /api/financas/transacoes` | registra um lançamento manual | feito e testado |
| `GET /api/financas/transacoes` | lista os lançamentos da pessoa logada, com filtros | feito e testado |
| `GET /api/financas/resumo` | totais de receitas, despesas e saldo, e total por categoria | feito e testado |

Os endpoints dessa API exigem login e respondem JSON. Sem login, respondem 401 (em vez de redirecionar para a tela de login, o que atrapalharia o JavaScript).

O lançamento manual valida tudo no servidor:
- aceita valor como `25.5` ou `"25,50"`, maior que zero e até 99.999.999,99;
- a categoria precisa existir; o `tipo` do lançamento é definido pela categoria, nunca pelo que o navegador enviar;
- o animal, se informado, precisa ser da pessoa logada (senão, 404);
- a data é opcional (padrão: hoje) e a descrição, opcional.

A listagem e o resumo aceitam os mesmos filtros na URL, lidos por uma única função (`_montar_filtros`):

| Filtro | Exemplo | Efeito |
|---|---|---|
| `inicio`, `fim` | `inicio=2026-10-01&fim=2026-10-31` | período (formato AAAA-MM-DD) |
| `tipo` | `tipo=DESPESA` | só receitas ou só despesas |
| `categoria_id` | `categoria_id=7` | uma categoria |
| `animal_id` | `animal_id=7` ou `animal_id=geral` | um animal, ou só os lançamentos gerais |
| `limite` | `limite=50` | só na listagem; de 1 a 500 (padrão 100) |

Todas as consultas filtram pela pessoa logada, então ninguém vê os lançamentos de outra conta. O resumo devolve `receitas`, `despesas`, `saldo` e `por_categoria` (categoria, tipo, total e quantidade).

### 4.6 Pet Finanças: tela de finanças (branch `pet-financas-painel`)

A página `/financas` (rota `pagina_financas`, que exige login) mostra o painel financeiro geral. O botão **Finanças** do painel leva até ela. Os arquivos são `templates/financas.html` e `static/js/financas.js`.

| Parte da tela | De onde vêm os dados |
|---|---|
| Cartões de receitas, despesas e saldo | `GET /api/financas/resumo` |
| Tabela com os últimos lançamentos | `GET /api/financas/transacoes?limite=20` |
| Lista de categorias do formulário | `GET /api/categorias` |
| Lista de animais do formulário | consulta feita pelo servidor ao montar a página |
| Botão **Registrar** | `POST /api/financas/transacoes` |

O JavaScript chama a API com `fetch` e atualiza a página sem recarregá-la: depois de registrar um lançamento, os cartões e a tabela são recarregados. Pontos de cuidado:

- os textos vindos do banco entram na tela com `textContent`, e não com `innerHTML`, para que um texto digitado pela pessoa (por exemplo, `<b>oi</b>`) apareça como texto e nunca seja executado como código;
- se a sessão expirar (resposta 401), a página volta para a tela de login;
- as mensagens de erro da API aparecem acima do formulário;
- acessibilidade: campos com `label`, tabela com cabeçalhos (`th scope`), regiões com `aria-live` e erro anunciado por `role="status"`;
- responsividade: a tela usa a grade do Bootstrap (mobile-first), e a tabela ganha rolagem horizontal em telas estreitas.

### 4.7 Pet Finanças: painel na página do animal (branch `pet-financas-animal`)

A Página Pet de cada animal ganhou o cartão **Finanças**, com os totais de receitas, despesas e saldo daquele animal, o botão **+ Registrar** (que abre o formulário de lançamento) e a lista dos lançamentos dele.

O mesmo arquivo `static/js/financas.js` atende as duas telas. O cartão tem o atributo `data-animal-id`, e é por ele que o JavaScript sabe que está na página de um animal: nesse caso, todas as chamadas à API recebem `animal_id`, a tabela passa a ter três colunas (data, categoria com a descrição em letra pequena abaixo, e valor), sem a coluna "Animal", para caber em telas de celular, e o lançamento registrado já fica ligado àquele animal (campo escondido no formulário). Na página geral, esse atributo não existe e o comportamento é o de antes.

A conferência de dono continua no servidor: o painel só aparece para quem é dono do animal (a própria rota da Página Pet responde 404 para os demais), e a API só devolve lançamentos da pessoa logada.

### 4.8 Página do animal: link para voltar ao painel (branch `pagina-animal-voltar`)

O teste da Página Pet em celular real mostrou uma lacuna de navegação que já existia: a barra de topo usa `navbar-expand-lg`, que em telas com menos de 992 px esconde o menu dentro de um bloco recolhido, e a página não tem o botão de menu (hambúrguer) que o abriria. Por isso o link "Voltar ao Painel" só aparecia no computador.

A correção foi acrescentar, logo depois do nome do sistema, um segundo link para `/painel` com a classe `d-lg-none` (visível apenas em telas pequenas). Em telas largas continua aparecendo um único link, o do menu. Nada foi removido da barra.

### 4.9 Exclusão de animal que tem lançamentos (branch `animal-exclusao-com-financas`)

As tabelas financeiras usam `ON DELETE RESTRICT`, então o banco recusa apagar um animal que tenha lançamentos. Antes desta etapa, a rota `deletar_animal` tentava o `DELETE` direto e, ao falhar, mostrava "Erro ao excluir o animal. Tente novamente.", uma mensagem enganosa, já que tentar de novo nunca resolveria.

Agora a rota confere antes, com um `SELECT COUNT(*)` em `transacoes`. Se o animal tem lançamentos, ela não tenta apagar: responde com o código 409 (conflito) e uma página explicando que o animal não pode ser apagado porque o histórico de dinheiro é preservado, com um link de volta à página do animal. Animais sem lançamentos continuam sendo apagados normalmente, e a conferência de dono (o animal precisa ser do usuário logado) continua valendo.

A regra do banco foi mantida de propósito: ela protege o histórico financeiro. A consequência é que, por enquanto, um animal com lançamentos não pode ser removido, nem os lançamentos podem ser corrigidos ou apagados. Isso está nos próximos passos (seção 7).

### 4.10 Página pública: preparo do banco (migração 002)

A página pública vai mostrar os animais que protetores e ONGs escolherem divulgar para adoção ou apadrinhamento. O arquivo `database/migrations/002_perfil_e_divulgacao.sql` prepara o banco para isso, com quatro colunas novas:

| Tabela | Coluna | Função |
|---|---|---|
| `usuarios` | `tipo` (`PROTETOR` ou `ONG`, padrão `PROTETOR`) | diferenciar o perfil da conta |
| `usuarios` | `cidade` (texto, opcional) | mostrar a cidade de quem divulga |
| `animais` | `visivel_publico` (0 ou 1, padrão 0) | só os animais marcados aparecem na página pública |
| `animais` | `info_saude` (texto de até 500 caracteres, opcional) | informações gerais escritas livremente, como "vermifugado, FIV/FELV negativo" |

Decisões:
- **Qualquer conta pode divulgar animais**, protetor individual ou ONG; o tipo é só o perfil, com dados extras.
- **`visivel_publico` começa em 0**: nenhum animal já cadastrado se torna público sem que a pessoa marque. É uma decisão de privacidade.
- **Informações de saúde em texto livre**, em vez de campos fixos (vermifugado, FIV, FELV...), porque esses campos ainda não existem e o texto é mais rápido e flexível. Pode ser trocado por campos específicos no futuro. O "vacinado" será calculado a partir das vacinas com status aplicada.
- **Código e rótulo são coisas diferentes**: o banco guarda `PROTETOR`, e o rótulo "Protetor(a)" aparece só no formulário.
- **Adoção e apadrinhamento** levam a um formulário externo único (Google Forms), com as perguntas de triagem (moradia, tela de proteção, outros animais etc.). O sistema não guarda nenhum dado pessoal de quem quer adotar, o que é bom para a LGPD. A limitação é que as respostas ficam todas em um só lugar, e não na ONG de cada animal.
- **A idade continua sendo texto** (`varchar`), para aceitar "3 meses" ou "10 anos".

As contas e os animais que já existiam ficaram com os valores padrão (todas `PROTETOR`, nenhum animal público). A migração deve ser aplicada uma única vez. Um backup do banco foi feito antes.

### 4.11 Cadastro com perfil, cidade e estado (migração 003, branch `cadastro-perfil-ong`)

Para a divulgação de animais, quem adota precisa saber **onde** está o animal, e cidade sem estado não basta. A migração `database/migrations/003_uf_do_usuario.sql` acrescentou `usuarios.uf` (`CHAR(2)`, a sigla do estado), logo depois de `cidade`. As migrações já aplicadas não são editadas: toda mudança nova vira um arquivo novo.

O cadastro (`/cadastro` e `/cadastrar`, em `routes/auth.py` e `templates/cadastro.html`) passou a pedir:
- **Perfil**: "Protetor(a) independente" ou "ONG". O banco guarda o código (`PROTETOR` ou `ONG`) e a tela mostra o rótulo. Nenhuma opção vem marcada, para a pessoa escolher de propósito.
- **Cidade** (texto, até 100 caracteres) e **Estado** (lista com as 27 siglas). Os dois são obrigatórios no cadastro. No banco continuam aceitando vazio, porque as contas antigas não têm esses dados.
- Um pequeno JavaScript (`static/js/cadastro.js`) troca o rótulo do campo de nome para "Nome da ONG" ou "Seu nome completo", conforme a escolha, para evitar que uma ONG cadastre o nome de uma pessoa.

A validação é feita **no servidor** (o HTML também exige os campos, mas ele pode ser contornado): nome, e-mail e senha preenchidos; perfil dentro dos dois valores permitidos; cidade preenchida e com até 100 caracteres; estado dentro das 27 siglas. Dados inválidos recebem uma página de erro com o código 400 e nada é gravado. O formulário também passou a usar `min-height` em vez de `height` na tela inteira, para que a página não seja cortada em celulares, já que tem mais campos.

Decisões e limitações:
- **Uma conta por e-mail**, como já era. Isso não impede que uma ONG tenha duas contas com e-mails diferentes, nem prova que quem escolhe "ONG" realmente é uma. A orientação é que cada ONG use **um e-mail institucional compartilhado pela equipe**. A verificação de ONGs (CNPJ e aprovação manual) fica como melhoria futura, e é relevante para adoção, porque evita perfis falsos.
- **Cidade e estado de quem divulga** só vão aparecer na página pública para os animais que a pessoa marcar para divulgação.
- A edição do perfil, da cidade e do estado depois do cadastro foi feita na etapa seguinte (seção 4.12).

### 4.12 Edição do perfil (branch `editar-perfil`)

A tela "Meu perfil" (`/editar_usuario`, em `routes/auth.py` e `templates/editarUsuario.html`) passou a permitir alterar também o **perfil** (protetor ou ONG), a **cidade** e o **estado**, além do nome e do telefone. Isso serve às contas que já existiam, que não têm cidade nem estado, e a quem escolheu o perfil errado no cadastro. O e-mail continua sem poder ser alterado.

O que mudou por dentro:
- As regras do perfil ficaram em **uma função só**, `_validar_perfil`, usada pelo cadastro e pela edição. Assim as duas telas seguem exatamente as mesmas regras (nome de 1 a 100 caracteres, perfil dentro dos dois valores permitidos, cidade preenchida e de até 100 caracteres, estado dentro das 27 siglas), em vez de a regra ser escrita duas vezes e divergir com o tempo.
- Antes, a edição só tinha o `required` do HTML. Agora ela também **valida no servidor**: dado inválido recebe uma página de erro com o código 400, com link de volta, e nada é gravado.
- A busca dos dados para preencher a tela deixou de usar `SELECT *` e traz só as colunas necessárias, **sem a senha** (o hash não chega mais ao template).
- O mesmo `static/js/cadastro.js` serve às duas telas e ajusta o rótulo do nome ("Nome da ONG" ou "Seu nome completo") também quando a tela abre com um perfil já marcado.
- Cidade e estado são obrigatórios na edição. Quem tem conta antiga precisa preenchê-los para salvar qualquer alteração.

A pessoa só consegue editar a **própria** conta, porque a rota usa o `id_usuario` da sessão e não aceita id nenhum pela tela.

## 5. Decisões de projeto e motivos

| Decisão | Motivo |
|---|---|
| Chaves `INT` e não `BIGINT` | o banco inteiro já usa `INT`; chaves estrangeiras precisam ter o mesmo tipo da chave que referenciam |
| `RECEITA`/`DESPESA` e não `ENTRADA`/`SAIDA` | é o vocabulário que a tabela `transacoes` original já usava |
| `categoria_id` (tabela) e não texto livre | evita variações de escrita ("Ração" e "racao") e permite filtros e gráficos confiáveis |
| `ON DELETE RESTRICT` nas tabelas financeiras | impede apagar sem querer um animal, usuário ou categoria que tenha histórico de dinheiro |
| `origem_tipo` e `origem_id` com chave única | garantem que a mesma vacina, por exemplo, nunca gere dois lançamentos, evitando contar o gasto em dobro |
| Animal vazio = lançamento geral | quem diz se o gasto é do animal ou da organização é o `animal_id`, e não a categoria |
| 404 em vez de 403 | não revelar a existência de registros de outras pessoas |

Pontos que diferem do relatório parcial e devem ser corrigidos no relatório final: `BIGINT` para `INT`; `ENTRADA`/`SAIDA` para `RECEITA`/`DESPESA`; categoria como tabela; `ON DELETE RESTRICT`; campos de Pix e status de pagamento movidos para uma migração futura (a migração 002 ficou com o perfil e a divulgação de animais).

## 6. Como testar

Os testes estão descritos em [TESTES.md](TESTES.md). Resumo: existem testes manuais (feitos a cada etapa, com duas contas) e 69 testes automatizados com `pytest`, que cobrem a API, a página de finanças, o painel da Página Pet, o link de volta ao painel, a exclusão de animais, o cadastro de contas e a edição do perfil.

Para rodar os automatizados, com a venv ativa e o `.env` configurado:

```
pip install -r requirements-dev.txt
pytest -v
```

Como só existe um banco, cada teste cria os próprios registros (com e-mail iniciado em `pytest_`) e apaga apenas o que criou.

## 7. Próximos passos

**Em andamento (prioridade, prazo de entrega em 06/11/2026):** divulgação de animais na página pública.
Já feitos nesta frente: o preparo do banco (seção 4.10), o cadastro com perfil, cidade e estado (4.11) e a edição do perfil (4.12).

1. Formulário do animal com "divulgar na página pública" e informações de saúde em texto livre. Só deve deixar divulgar quem já tiver cidade e estado no perfil.
2. API pública (`GET /api/publico/animais`, sem login) que devolve apenas os animais divulgados e uma lista fixa de campos, sem dados pessoais, chip, histórico clínico ou financeiro.
3. Página pública (feita por outra integrante do grupo) usando essa API, com o botão "Entrar" para protetores e ONGs e o botão de adoção/apadrinhamento levando a um formulário externo.

**Depois, se houver tempo:**
4. Lançamentos automáticos a partir de vacinas, medicamentos e consultas com valor.
5. Tela de finanças: filtros e gráfico de despesas por categoria.
6. Testes não funcionais: responsividade, acessibilidade e latência do banco.
7. Campanhas, chave Pix e a integração com o Pix (Mercado Pago, em Sandbox), em uma migração futura.
8. Avisos de erro e sucesso padronizados em JavaScript.
9. Regenerar o `schema.sql` do repositório a partir do banco real, que hoje está desatualizado.
10. Permitir editar e apagar lançamentos e/ou "arquivar" um animal. Hoje, um animal que tenha lançamentos não pode ser apagado (seção 4.9), e ainda não existe como corrigir ou remover um lançamento.
11. Verificação de ONGs (CNPJ e aprovação manual), para evitar perfis falsos (seção 4.11).

## 8. Pendências conhecidas de segurança

- As exclusões usam links (GET); o ideal é POST com proteção contra CSRF.
- Verificação do certificado SSL na conexão com o banco.
- Limite de tentativas de login.
- Recuperação de senha.
- Banco separado para desenvolvimento e produção.
- A página pública lê dados com `innerHTML`; trocar por `textContent` onde o conteúdo vier do banco.

## 9. Glossário rápido

- **Rota (route):** um endereço do site ligado a uma função Python.
- **Decorador:** a linha com `@` acima de uma função, que acrescenta um comportamento (por exemplo, exigir login).
- **Sessão:** o que o servidor guarda para lembrar quem está logado entre uma página e outra.
- **Hash de senha:** transformação que não pode ser revertida; o sistema guarda o hash, nunca a senha.
- **API e endpoint:** endereço do servidor que responde com dados (JSON) em vez de uma página.
- **JSON:** formato de texto para trocar dados entre servidor e JavaScript.
- **`fetch`:** comando do JavaScript que chama o servidor sem recarregar a página.
- **Migração:** arquivo `.sql` guardado no repositório que descreve uma mudança no banco.
- **Chave estrangeira:** coluna que aponta para o registro de outra tabela e garante que o vínculo seja válido.
- **Branch, commit, push e Pull Request:** ramo de trabalho, registro de uma mudança, envio para o GitHub e pedido para juntar a branch com a `main`.

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
| `GET /api/categorias` | lista as categorias | feito, commitado |
| `POST /api/financas/transacoes` | registra um lançamento manual | feito e testado |

Os endpoints dessa API exigem login e respondem JSON. Sem login, respondem 401 (em vez de redirecionar para a tela de login, o que atrapalharia o JavaScript).

O lançamento manual valida tudo no servidor:
- aceita valor como `25.5` ou `"25,50"`, maior que zero e até 99.999.999,99;
- a categoria precisa existir; o `tipo` do lançamento é definido pela categoria, nunca pelo que o navegador enviar;
- o animal, se informado, precisa ser da pessoa logada (senão, 404);
- a data é opcional (padrão: hoje) e a descrição, opcional.

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

Pontos que diferem do relatório parcial e devem ser corrigidos no relatório final: `BIGINT` para `INT`; `ENTRADA`/`SAIDA` para `RECEITA`/`DESPESA`; categoria como tabela; `ON DELETE RESTRICT`; campos de Pix e status de pagamento movidos para a migração 002.

## 6. Como testar

Os testes manuais feitos até agora para o Pet Finanças usaram o console do navegador (F12), com a pessoa logada, chamando a API com `fetch`:

| Teste | Resultado esperado |
|---|---|
| Despesa geral, de animal e receita | 201 |
| Valor zero ou texto | 400 |
| Categoria inexistente | 400 |
| Animal de outra conta | 404 |
| Sem login | 401 |

Os testes automatizados (`pytest`) serão criados junto com a API. Como só existe um banco, eles devem criar os próprios registros e apagar apenas o que criaram.

## 7. Próximos passos

1. Listagem e resumo: `GET /api/financas/transacoes` (com filtros por período, categoria, tipo e animal) e `GET /api/financas/resumo`.
2. Lançamentos automáticos a partir de vacinas, medicamentos e consultas com valor.
3. Telas e JavaScript: painel do animal e painel geral, com formulário, resumo e gráfico atualizados por `fetch`.
4. Testes automatizados com `pytest`.
5. Migração 002: campanhas, tipo de perfil (protetor ou ONG) e chave Pix; depois, a integração com o Pix (Mercado Pago, em Sandbox).
6. Avisos de erro e sucesso padronizados em JavaScript.
7. Regenerar o `schema.sql` do repositório a partir do banco real, que hoje está desatualizado.

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

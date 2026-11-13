# Patinhas Protegidas: documentação de desenvolvimento

Este documento registra como o sistema está organizado, o que foi feito desde a refatoração do back-end e quais decisões foram tomadas. Ele deve ser atualizado a cada etapa concluída.

Última atualização: 12/11/2026.

## 1. Visão geral

O Patinhas Protegidas é uma aplicação web em Flask (Python) para protetoras e ONGs de animais. Cada pessoa cadastrada controla seus animais, com saúde (vacinas, medicamentos, consultas e histórico veterinário). O módulo **Pet Finanças** controla receitas e despesas, com lançamentos automáticos a partir dos registros de saúde, gráficos de acompanhamento e campanhas de arrecadação com doação via Pix.

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
  publico.py            API pública dos animais divulgados (sem login)
utils/
  auth.py               controle de acesso (login e dono do registro)
  financeiro.py         lê valores digitados e cria a despesa ligada a vacinas, medicamentos e consultas
  pix.py                valida e padroniza a chave Pix do perfil
templates/              páginas HTML
static/                 JavaScript e dados da página pública
  js/doacao_pix.js      janela de doação via Pix (QR Code, copia e cola e aviso de doação)
  js/doacoes_pendentes.js  seção "Confirmar doações recebidas" em Finanças
  js/graficos_financas.js  gráficos de Finanças
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

### 4.13 API pública dos animais divulgados (branch `api-publica`)

Para a página pública mostrar animais reais, e não mais um arquivo de exemplo, foi criado o endereço `GET /api/publico/dados` (em `routes/publico.py`, blueprint `publico_bp`). Ele **não exige login**, porque quem adota não tem conta. Devolve em JSON os animais marcados como divulgados (`visivel_publico = 1`), já agrupados do jeito que a página pública espera.

Como os dados são agrupados:
- Cada conta do tipo **ONG** vira um cartão próprio, com o nome da ONG, cidade e estado.
- As contas do tipo **protetor independente** vão todas para **um único cartão**, "Protetores independentes", sem nenhum nome de pessoa e com a região "Vários locais". Isso protege a privacidade de quem cuida sozinho (LGPD) e já funciona sem precisar mudar o desenho da página.
- O cartão dos protetores independentes só aparece se tiver ao menos um animal. A lista de valores de doação e o link do formulário de adoção (formulário externo do Google, o mesmo para todos) também vêm na resposta.

O que cada animal traz: `id`, `nome`, `especie`, `raca`, `idade`, `foto`, `castrado`, `temChip`, `vacinado`, `infoSaude`, `cidade` e `estado`.
- `temChip` é apenas sim ou não. O **número do chip nunca sai** do servidor.
- `vacinado` é calculado: vale "sim" se o animal tem ao menos uma vacina com status `aplicada`. Vacina só agendada não conta.
- `infoSaude` é o texto livre digitado por quem cuida (por exemplo, "vermifugado, FIV/FELV negativo"). Foi escolhido um campo livre porque as situações são variadas e não cabem em campos fixos.
- Animal sem foto recebe uma imagem padrão ("Sem foto").

Privacidade e segurança:
- A resposta usa uma **lista fixa de campos** (a consulta SQL escolhe uma a uma as colunas). Telefone, e-mail, número do chip, histórico clínico, vacinas detalhadas e finanças **nunca** entram. Um teste automatizado compara as chaves da resposta com a lista permitida, e quebra se alguém acrescentar um campo por engano.
- Em caso de erro no banco, a rota registra o problema no log do servidor e responde 500 com uma mensagem genérica, sem detalhes técnicos.

Atenção para a página pública (parte da outra integrante do grupo): como esses textos agora são **digitados por usuários**, o JavaScript não pode mais montar a página com `innerHTML` sem tratar o conteúdo, porque alguém poderia digitar código HTML ou JavaScript no nome ou na informação de saúde (ataque XSS). Os textos devem ser inseridos com `textContent` ou ter os caracteres especiais escapados.

Limitações conhecidas:
- A divulgação pela tela foi feita na etapa seguinte (seção 4.14).
- A API devolve todos os animais divulgados de uma vez, sem paginação, o que é suficiente para o volume do projeto.
- O cartão de cada ONG não tinha descrição própria nem campanhas (ficavam vazios). Isso mudou depois: o perfil ganhou logo, missão e formulário de adoção, e as campanhas passaram a vir na resposta (seções 4.16 e 4.17). A revisão dessa API está na seção 4.23.

### 4.14 Formulário do animal: divulgação e informações de saúde (branch `animal-divulgacao`)

As telas de **cadastro** e de **edição** do animal (`templates/cadastroAnimal.html`, `templates/editar_animal.html`, rotas em `routes/animais.py`) ganharam dois campos, que alimentam a API pública da seção 4.13:
- **Informações de saúde** (`info_saude`): texto livre de até 500 caracteres, opcional, com um aviso para não escrever telefone, e-mail ou outros dados pessoais, já que o texto fica público.
- **Divulgar na página pública para adoção** (`visivel_publico`): caixa de marcação, desligada por padrão. Um texto abaixo explica o que os visitantes passam a ver: nome, espécie, raça, idade, foto, se é castrado, se tem chip (sem o número), se está vacinado, as informações de saúde, a cidade e o estado. Se a conta for de ONG, o nome da ONG aparece; se for de protetor(a), o nome da pessoa não aparece.

Regras:
- **Só divulga quem tem cidade e estado no perfil**, porque quem quer adotar precisa saber onde o animal está. Sem eles, a opção aparece desabilitada, com um link para "Meu perfil".
- A regra é conferida **também no servidor**, e não só na tela, porque o HTML pode ser contornado: divulgar sem cidade e estado, ou enviar um texto de saúde com mais de 500 caracteres, recebe uma página de erro (400) e nada é gravado.
- **Salvar sem marcar a opção** tira o animal da página pública. Só o dono do animal consegue alterar a divulgação, porque a atualização exige o id do usuário da sessão.
- O texto digitado é escapado pelo Jinja ao reaparecer na tela de edição.
- Para não repetir regras, a leitura dos campos e a validação ficaram em funções únicas (`_ler_divulgacao`, `_erro_de_divulgacao` e `_conta_tem_cidade_e_uf`), usadas pelo cadastro e pela edição.

Limitações:
- O resultado na página pública depende de a página (feita por outra integrante do grupo) passar a usar a API, o que ainda não aconteceu.
- Não há aviso na tela do painel de quais animais estão divulgados; isso só aparece na tela de edição.

### 4.15 Valor em vacinas, medicamentos e consultas (PR #33, branch `vacina-com-valor`)

Os formulários de cadastro de vacina, medicação e consulta ganharam o campo **Valor (R$)**, opcional. Quando preenchido, o registro de saúde e a despesa são gravados no mesmo `commit`: se um falhar, nenhum dos dois fica salvo.

- A despesa entra na categoria correspondente (Vacina, Medicamento ou Consulta), ligada ao animal, com `origem_tipo` e `origem_id` apontando para o registro de saúde.
- A data da despesa é a da vacina, a do início do tratamento ou a da consulta.
- A função `sincronizar_lancamento` (`utils/financeiro.py`) cria ou atualiza a despesa, mas **nunca apaga**. Valor vazio ou zero não gera lançamento.
- A função `ler_valor` aceita "120", "120,50", "1.200" e "1.200,50".
- Ainda falta: a edição desses registros não atualiza a despesa.

### 4.16 Campanhas no painel (PR #34, branch `campanhas-no-painel`)

O painel passou a mostrar as campanhas ativas do usuário em cards com foto, animal vinculado e barra de progresso (arrecadado/meta). Depois de publicar uma campanha, o usuário volta ao painel, e não mais à tela de Finanças.

### 4.17 Chave Pix e janela de doação (migração 006, PR #35, branch `chave-pix`)

- **Banco:** coluna `usuarios.chave_pix` (`VARCHAR(77)`, opcional).
- **Perfil:** campo "Chave Pix para doações". A função `normalizar_chave_pix` (`utils/pix.py`) aceita CPF, CNPJ, e-mail, telefone e chave aleatória, confere o dígito verificador de CPF e CNPJ e grava a chave no formato que os bancos usam (por exemplo, `(11) 91234-5678` vira `+5511912345678`).
- **Todas as campanhas do usuário usam a chave do perfil.** Trocar a chave no perfil muda a de todas as campanhas.
- **API pública:** cada campanha passa a trazer `chavePix`, `recebedor` (nome da ONG, ou "Protetor(a) independente") e `cidade`.
- **Janela de doação** (`static/js/doacao_pix.js`): valores sugeridos, valor livre, QR Code e "Pix copia e cola" com o valor escolhido embutido, no padrão BR Code do Banco Central. O QR Code é gerado no navegador, com a biblioteca qrcodejs.
- O Pix vai **direto** para quem criou a campanha: o site não recebe nem repassa dinheiro.

### 4.18 Aviso e confirmação de doações (migração 007, PR #36, branch `confirmar-doacao`)

Como o Pix não passa pelo site, o sistema não sabe quando uma doação acontece. O fluxo é em duas etapas:

1. **O doador avisa.** Na janela de doação, o botão "Confirmo que a doação foi concluída" abre a confirmação "Confirmo que doei R$ X". Isso grava um aviso **pendente** na tabela `doacoes_informadas`. Nada entra em Finanças.
2. **O dono da campanha confirma.** Em Finanças, a seção "Confirmar doações recebidas" lista os avisos. "Confirmar recebimento" lança o valor em Receitas > Doação via Campanha e soma no `arrecadado` da campanha. "Não recebi" descarta o aviso.

Proteções: a rota do aviso é aberta (sem login), mas aceita no máximo 30 avisos pendentes por campanha. A confirmação trava o aviso (`SELECT ... FOR UPDATE`) para não lançar o mesmo valor duas vezes. Só o dono da campanha vê, confirma ou descarta os avisos dela.

Rotas: `POST /api/publico/campanhas/<id>/doacao-informada`, `GET /api/financas/doacoes-pendentes`, `POST /api/financas/doacoes-pendentes/<id>/confirmar` e `POST /api/financas/doacoes-pendentes/<id>/recusar`.

### 4.19 Gráficos em Finanças (PR #37, branch `graficos-financas`)

Dois gráficos dos últimos 6 meses, abaixo da seção de doações: **Gastos por categoria** (rosca, com total e percentuais) e **Gastos vs Recebimentos** (barras mês a mês). A nova rota `GET /api/financas/mensal` devolve os totais por mês, com os meses sem lançamento zerados. Os gráficos usam Chart.js.

### 4.20 Jornadas concluídas (migração 008, PR #38, branch `jornadas-concluidas`)

O painel ganhou os títulos "Meus animais", "Minhas campanhas" e "Jornadas concluídas". Cada card tem um menu ••• para mover o animal ou a campanha para "Jornadas concluídas", e para trazê-los de volta.

- **Animal:** a coluna `animais.jornada_concluida_em` guarda a data. Animal concluído sai da página de adoção, mas a opção de divulgação não é apagada: se voltar, ele reaparece.
- **Campanha:** usa o status `concluida`, que já existia. Campanha concluída sai da página pública e para de aceitar avisos de doação.

Isso resolve, em parte, o "arquivar animal" da seção 7.

### 4.23 Revisão da API pública depois das campanhas e do Pix (branch `teste-publico-logo`)

Com as campanhas, o Pix e o perfil de ONG (seções 4.16 a 4.22), a resposta de `GET /api/publico/dados` ganhou campos novos: `logoUrl` em cada cartão e, em cada campanha, `chavePix`, `recebedor` e `cidade`. Ao rodar a suíte depois de juntar as alterações do grupo, 89 dos 90 testes passaram. O que falhou foi o teste que trava a lista de campos do cartão, por causa do `logoUrl`. Esse campo é público por natureza (é o logo da ONG), então o teste foi atualizado, e a falha cumpriu o papel para o qual o teste existe: obrigar uma decisão consciente antes de um campo novo ficar público.

A leitura de `routes/publico.py` mostrou três inconsistências, corrigidas nesta etapa:

1. **Cartão "Protetores independentes".** Ele pegava o formulário de adoção e o logo do primeiro protetor que tivesse, entre todos. Quem quisesse adotar o animal de uma pessoa podia cair no formulário de outra, e o cartão, que deveria ser anônimo, mostrava o logo e o link escolhidos por alguém. Agora esse cartão usa só o formulário único do grupo (`LINK_FORMULARIO`) e não tem logo.
2. **ONG sem link de formulário no perfil.** A API devolvia `null`, e o botão de adoção ficava sem destino. Agora o padrão é o formulário único do grupo.
3. **ONG com campanha ativa e sem animal divulgado.** A campanha não aparecia. Agora a ONG aparece, com a campanha. O cartão da ONG passou a ser montado por uma função só (`_cartao_da_ong`), usada tanto para quem tem animais quanto para quem só tem campanha, e os cartões saem em ordem de nome.

Uma quarta correção, pequena: o aviso de doação (`POST /api/publico/campanhas/<id>/doacao-informada`) respondia com erro 500 quando o corpo da requisição era um JSON que não é um objeto (por exemplo, uma lista ou um texto). Agora responde 400, como nos demais valores inválidos.

Decisões de privacidade que foram **mantidas** e merecem registro no relatório:
- **A chave Pix é pública**, porque sem ela ninguém consegue doar. Como pode ser CPF, telefone ou e-mail (dado pessoal), a tela do perfil avisa que ela fica visível e recomenda a chave aleatória. Nas campanhas de protetores independentes o nome é escondido ("Protetor(a) independente"), mas a chave, se for um CPF, pode identificar a pessoa; por isso a recomendação.
- **O cartão dos independentes não mostra nome, telefone nem e-mail de ninguém**, e a chave Pix só aparece dentro da campanha. Os testes novos conferem os dois pontos.

O que foi acrescentado de testes: 21 testes automatizados em `tests/test_publico_campanhas.py`, que cobrem as campanhas na API pública, o formulário e o logo dos cartões e o aviso de doação (descrição na seção 3.3 do `TESTES.md`).

### 4.21 Rolagem nos últimos lançamentos (PR #39, branch `ajuste-lancamentos`)

A tabela de Finanças mostra no máximo 10 linhas, com rolagem e cabeçalho fixo. A tela passou a carregar os 250 lançamentos mais recentes (antes eram 20). O `static/js/financas.js` também é usado na página do animal, onde a lista cresce sem rolagem.

### 4.22 Corrigir o valor de uma doação (PR #40, branch `corrigir-valor-doacao`)

Nos avisos de doação, o botão **Corrigir valor** permite confirmar com o valor que realmente caiu na conta. O valor informado pelo doador continua guardado no aviso, e a descrição do lançamento registra a correção, por exemplo: "(valor corrigido; informado: R$ 15,00)".

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
| Despesa de saúde nunca é apagada automaticamente | evita sumir dinheiro do histórico sem ninguém perceber; correções são feitas à mão |
| Chave Pix no perfil, e não em cada campanha | a pessoa cadastra uma vez só, e todas as campanhas ficam consistentes |
| Pix direto para quem criou a campanha | o site não intermedia dinheiro: sem taxa, sem conta do projeto e sem responsabilidade de repasse |
| Doação em duas etapas (aviso + confirmação) | o site não sabe quando um Pix acontece; só quem recebe pode confirmar, o que impede lançamentos falsos |
| Doação confirmada com `origem_id` vazio | a chave única (`origem_tipo`, `origem_id`) impediria mais de uma doação por campanha; a ligação com o aviso fica em `doacoes_informadas.transacao_id` |
| Jornada concluída retira da página pública | animal adotado não deve continuar aparecendo para adoção, nem campanha encerrada recebendo doações |

Pontos que diferem do relatório parcial e devem ser corrigidos no relatório final: `BIGINT` para `INT`; `ENTRADA`/`SAIDA` para `RECEITA`/`DESPESA`; categoria como tabela; `ON DELETE RESTRICT`; campos de Pix e status de pagamento movidos para uma migração futura (a migração 002 ficou com o perfil e a divulgação de animais).

## 6. Como testar

Os testes estão descritos em [TESTES.md](TESTES.md). Resumo: existem testes manuais (feitos a cada etapa, com duas contas) e 111 testes automatizados com `pytest`, que cobrem a API, a página de finanças, o painel da Página Pet, o link de volta ao painel, a exclusão de animais, o cadastro de contas, a edição do perfil, a API pública (animais, campanhas e aviso de doação) e a divulgação pelo formulário do animal.

Para rodar os automatizados, com a venv ativa e o `.env` configurado:

```
pip install -r requirements-dev.txt
pytest -v
```

Como só existe um banco, cada teste cria os próprios registros (com e-mail iniciado em `pytest_`) e apaga apenas o que criou.

As funcionalidades das seções 4.15 a 4.22 foram testadas manualmente. Dessas, só a parte pública das campanhas (campanhas na API pública e o aviso de doação) tem testes automatizados, descritos na seção 4.23. Ainda só têm teste manual: os lançamentos automáticos de saúde, a validação da chave Pix, a janela de doação, a confirmação e a recusa de avisos em Finanças, os gráficos e as jornadas concluídas.

## 7. Próximos passos

**Feito desde a última atualização:** lançamentos automáticos a partir da saúde (4.15), gráficos em Finanças (4.19), campanhas com chave Pix e doação (4.17, 4.18 e 4.22) e "arquivar" animais e campanhas (4.20).

**Em andamento (prioridade, prazo de entrega em 06/11/2026):** divulgação de animais na página pública.
Já feitos nesta frente: o preparo do banco (seção 4.10), o cadastro com perfil, cidade e estado (4.11), a edição do perfil (4.12), a API pública (4.13) e o formulário do animal com a divulgação (4.14).

1. Página pública (feita por outra integrante do grupo) passar a usar `/api/publico/dados` no lugar do arquivo de exemplo, escapar os textos, mostrar os novos campos, ganhar o botão "Entrar" para protetores e ONGs e o botão de adoção/apadrinhamento levando ao formulário externo.

**Depois, se houver tempo:**
2. Lançamentos automáticos a partir de vacinas, medicamentos e consultas com valor. - OK 
3. Tela de finanças: filtros e gráfico de despesas por categoria. - OK
4. Testes não funcionais: responsividade, acessibilidade e latência do banco.
5. Campanhas, chave Pix e a integração com o Pix (Mercado Pago, em Sandbox), em uma migração futura. - OK (campanhas e pix)
6. Avisos de erro e sucesso padronizados em JavaScript.
7. Regenerar o `schema.sql` do repositório a partir do banco real, que hoje está desatualizado.
8. Permitir editar e apagar lançamentos e/ou "arquivar" um animal. Hoje, um animal que tenha lançamentos não pode ser apagado (seção 4.9), e ainda não existe como corrigir ou remover um lançamento. - OK função "arquivar" animais e campanhas (4.20)
9. Verificação de ONGs (CNPJ e aprovação manual), para evitar perfis falsos (seção 4.11).

## 8. Pendências conhecidas de segurança

- As exclusões usam links (GET); o ideal é POST com proteção contra CSRF.
- Verificação do certificado SSL na conexão com o banco.
- Limite de tentativas de login.
- Recuperação de senha.
- Banco separado para desenvolvimento e produção.
- A página pública lê dados com `innerHTML`; trocar por `textContent` (ou escapar) onde o conteúdo vier do banco, agora que a API pública entrega textos digitados por usuários (seção 4.13).
- A API pública não tem limite de requisições; para o porte do projeto é aceitável.
- O aviso de doação é uma rota aberta, sem login. O limite de 30 avisos pendentes por campanha impede que a lista seja enchida sem fim, mas alguém mal-intencionado poderia ocupar as 30 vagas e bloquear os avisos de doadores de verdade. Não há limite por origem (endereço de IP).
- A chave Pix é pública (necessário para doar) e pode ser um dado pessoal (CPF, telefone ou e-mail). A tela do perfil recomenda a chave aleatória, mas o sistema não impede o uso de outros tipos (seção 4.23).

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

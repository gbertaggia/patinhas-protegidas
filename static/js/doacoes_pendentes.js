// Seção "Confirmar doações recebidas" da tela de Finanças.
// Mostra os avisos de doação feitos pelos visitantes nas campanhas do usuário logado.
(function () {
  "use strict";

  const secao = document.getElementById("secao-doacoes-pendentes");
  if (!secao) return;
  const lista = document.getElementById("lista-doacoes-pendentes");
  const areaErro = document.getElementById("erro-doacoes-pendentes");

  function formatarMoeda(valor) {
    return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  function formatarDataHora(segundos) {
    return new Date(segundos * 1000).toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  // Aceita "15", "15,50", "1.200,00" e "15.50"
  function lerValor(texto) {
    let limpo = String(texto || "").trim().replace(/\s|R\$/g, "");
    if (limpo.includes(",")) limpo = limpo.replace(/\./g, "").replace(",", ".");
    const numero = Number(limpo);
    return Number.isFinite(numero) && numero > 0 ? Math.round(numero * 100) / 100 : 0;
  }

  function mostrarErro(texto) {
    areaErro.textContent = texto;
    areaErro.hidden = !texto;
  }

  async function analisar(doacao, acao, linha, valorCorrigido) {
    if (acao === "recusar" &&
        !window.confirm(`Marcar a doação de ${formatarMoeda(doacao.valor)} como não recebida?`)) {
      return;
    }
    mostrarErro("");
    linha.querySelectorAll("button").forEach((b) => { b.disabled = true; });
    try {
      const opcoes = { method: "POST" };
      if (valorCorrigido) {
        opcoes.headers = { "Content-Type": "application/json" };
        opcoes.body = JSON.stringify({ valor: valorCorrigido });
      }
      const resposta = await fetch(`/api/financas/doacoes-pendentes/${doacao.id}/${acao}`, opcoes);
      if (resposta.status === 401) {
        window.location.href = "/login";
        return;
      }
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(dados.erro || "Não foi possível atualizar a doação.");

      if (acao === "confirmar") {
        // Recarrega para atualizar os totais e a lista de lançamentos
        window.location.reload();
        return;
      }
      linha.remove();
      if (!lista.children.length) secao.hidden = true;
    } catch (erro) {
      mostrarErro(erro.message);
      linha.querySelectorAll("button").forEach((b) => { b.disabled = false; });
    }
  }

  // Troca os botões da linha por um campo para digitar o valor que realmente caiu na conta
  function abrirCorrecao(doacao, linha, acoes) {
    const area = document.createElement("div");
    area.className = "d-flex flex-wrap align-items-center gap-2";

    const grupo = document.createElement("div");
    grupo.className = "input-group input-group-sm";
    grupo.style.width = "150px";
    const prefixo = document.createElement("span");
    prefixo.className = "input-group-text";
    prefixo.textContent = "R$";
    const campo = document.createElement("input");
    campo.type = "text";
    campo.inputMode = "decimal";
    campo.className = "form-control";
    campo.setAttribute("aria-label", "Valor recebido");
    campo.value = Number(doacao.valor).toLocaleString("pt-BR", { minimumFractionDigits: 2 });
    grupo.append(prefixo, campo);

    const salvar = document.createElement("button");
    salvar.type = "button";
    salvar.className = "btn btn-success btn-sm";
    salvar.textContent = "Confirmar com este valor";

    const cancelar = document.createElement("button");
    cancelar.type = "button";
    cancelar.className = "btn btn-link btn-sm text-secondary";
    cancelar.textContent = "Cancelar";

    function confirmarCorrecao() {
      const valor = lerValor(campo.value);
      if (!valor) {
        mostrarErro("Digite o valor recebido, por exemplo 15,00.");
        campo.focus();
        return;
      }
      analisar(doacao, "confirmar", linha, valor);
    }

    salvar.addEventListener("click", confirmarCorrecao);
    campo.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") confirmarCorrecao();
      if (evento.key === "Escape") cancelar.click();
    });
    cancelar.addEventListener("click", () => {
      mostrarErro("");
      area.replaceWith(acoes);
    });

    area.append(grupo, salvar, cancelar);
    acoes.replaceWith(area);
    campo.focus();
    campo.select();
  }

  function montarLinha(doacao) {
    const linha = document.createElement("li");
    linha.className = "list-group-item d-flex flex-wrap align-items-center gap-3";

    const texto = document.createElement("div");
    texto.className = "flex-grow-1";
    const valor = document.createElement("strong");
    valor.className = "fs-5 text-success d-block";
    valor.textContent = formatarMoeda(doacao.valor);
    const detalhe = document.createElement("span");
    detalhe.className = "text-muted small";
    // textContent: o título da campanha é texto digitado por usuário
    detalhe.textContent = `${doacao.campanha} · informado em ${formatarDataHora(doacao.informado_em)}`;
    texto.append(valor, detalhe);

    const confirmar = document.createElement("button");
    confirmar.type = "button";
    confirmar.className = "btn btn-success btn-sm";
    confirmar.textContent = "Confirmar recebimento";
    confirmar.addEventListener("click", () => analisar(doacao, "confirmar", linha));

    const corrigir = document.createElement("button");
    corrigir.type = "button";
    corrigir.className = "btn btn-outline-primary btn-sm";
    corrigir.textContent = "Corrigir valor";

    const recusar = document.createElement("button");
    recusar.type = "button";
    recusar.className = "btn btn-outline-secondary btn-sm";
    recusar.textContent = "Não recebi";
    recusar.addEventListener("click", () => analisar(doacao, "recusar", linha));

    const acoes = document.createElement("div");
    acoes.className = "d-flex flex-wrap gap-2";
    acoes.append(confirmar, corrigir, recusar);
    corrigir.addEventListener("click", () => abrirCorrecao(doacao, linha, acoes));

    linha.append(texto, acoes);
    return linha;
  }

  async function carregar() {
    try {
      const resposta = await fetch("/api/financas/doacoes-pendentes", { headers: { Accept: "application/json" } });
      if (!resposta.ok) return;
      const doacoes = await resposta.json();
      lista.replaceChildren(...doacoes.map(montarLinha));
      secao.hidden = doacoes.length === 0;
    } catch (erro) {
      // Se falhar, a seção simplesmente não aparece; o resto da tela segue funcionando
    }
  }

  carregar();
})();
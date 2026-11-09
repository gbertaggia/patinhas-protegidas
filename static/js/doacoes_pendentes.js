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

  function mostrarErro(texto) {
    areaErro.textContent = texto;
    areaErro.hidden = !texto;
  }

  async function analisar(doacao, acao, linha) {
    if (acao === "recusar" &&
        !window.confirm(`Marcar a doação de ${formatarMoeda(doacao.valor)} como não recebida?`)) {
      return;
    }
    mostrarErro("");
    linha.querySelectorAll("button").forEach((b) => { b.disabled = true; });
    try {
      const resposta = await fetch(`/api/financas/doacoes-pendentes/${doacao.id}/${acao}`, { method: "POST" });
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

    const recusar = document.createElement("button");
    recusar.type = "button";
    recusar.className = "btn btn-outline-secondary btn-sm";
    recusar.textContent = "Não recebi";
    recusar.addEventListener("click", () => analisar(doacao, "recusar", linha));

    linha.append(texto, confirmar, recusar);
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
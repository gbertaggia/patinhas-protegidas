// Gráficos da tela de Finanças: gastos por categoria (rosca) e gastos x recebimentos por mês (barras).
// Usa Chart.js, carregado antes deste arquivo no financas.html.
(function () {
  "use strict";

  const secao = document.getElementById("secao-graficos");
  if (!secao || typeof Chart === "undefined") return;

  const MESES_NO_GRAFICO = 6;
  const COR_GASTO = "#f2678f";
  const COR_RECEBIDO = "#4cc28a";

  // Cor de cada categoria de despesa
  const CORES_CATEGORIA = {
    "Medicamento": "#f2678f",
    "Vacina": "#5aaef2",
    "Exame": "#f5c94e",
    "Cirurgia": "#c792f2",
    "Alimentação": "#4cc28a",
    "Castração": "#f59a4a",
    "Consulta": "#45c3db",
    "Higiene e limpeza": "#8c8ff0",
    "Aluguel e contas": "#b98a68",
    "Transporte": "#7a8899",
    "Outros": "#9aa0a8",
  };
  const CORES_EXTRAS = ["#e57373", "#64b5f6", "#81c784", "#ffb74d", "#ba68c8", "#4db6ac"];

  function corDaCategoria(nome, indice) {
    return CORES_CATEGORIA[nome] || CORES_EXTRAS[indice % CORES_EXTRAS.length];
  }

  function formatarMoeda(valor) {
    return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  function isoLocal(data) {
    return data.toLocaleDateString("en-CA"); // AAAA-MM-DD
  }

  function nomeDoMes(anoMes) {
    const [ano, mes] = anoMes.split("-").map(Number);
    const nome = new Date(ano, mes - 1, 1).toLocaleDateString("pt-BR", { month: "short" }).replace(".", "");
    return `${nome.charAt(0).toUpperCase()}${nome.slice(1)}/${ano}`;
  }

  // Últimos 6 meses, do primeiro dia do mês mais antigo até o último dia do mês atual
  function periodo() {
    const hoje = new Date();
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth() - (MESES_NO_GRAFICO - 1), 1);
    const fim = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
    return `inicio=${isoLocal(inicio)}&fim=${isoLocal(fim)}`;
  }

  async function buscar(url) {
    const resposta = await fetch(url, { headers: { Accept: "application/json" } });
    if (!resposta.ok) throw new Error("Falha ao carregar os gráficos.");
    return resposta.json();
  }

  function desenharCategorias(resumo) {
    const despesas = resumo.por_categoria
      .filter((c) => c.tipo === "DESPESA")
      .sort((a, b) => Number(b.total) - Number(a.total));
    const total = Number(resumo.despesas);

    const vazio = despesas.length === 0;
    document.getElementById("categorias-vazio").hidden = !vazio;
    document.getElementById("categorias-conteudo").hidden = vazio;
    if (vazio) return;

    document.getElementById("categorias-total").textContent = formatarMoeda(total);

    const legenda = document.getElementById("categorias-legenda");
    legenda.replaceChildren();
    despesas.forEach((item, indice) => {
      const linha = document.createElement("li");
      const ponto = document.createElement("span");
      ponto.className = "grafico-ponto";
      ponto.style.background = corDaCategoria(item.categoria, indice);
      const nome = document.createElement("span");
      nome.className = "grafico-nome";
      nome.textContent = item.categoria;
      const valor = document.createElement("span");
      valor.textContent = formatarMoeda(item.total);
      const percentual = document.createElement("span");
      percentual.className = "grafico-percentual";
      percentual.textContent = `${Math.round((Number(item.total) / total) * 100)}%`;
      linha.append(ponto, nome, valor, percentual);
      legenda.appendChild(linha);
    });

    new Chart(document.getElementById("grafico-categorias"), {
      type: "doughnut",
      data: {
        labels: despesas.map((c) => c.categoria),
        datasets: [{
          data: despesas.map((c) => Number(c.total)),
          backgroundColor: despesas.map((c, i) => corDaCategoria(c.categoria, i)),
          borderColor: "#ffffff",
          borderWidth: 2,
        }],
      },
      options: {
        cutout: "60%",
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${formatarMoeda(ctx.parsed)}` } },
        },
      },
    });
  }

  function desenharMensal(meses) {
    const vazio = meses.every((m) => Number(m.receitas) === 0 && Number(m.despesas) === 0);
    document.getElementById("mensal-vazio").hidden = !vazio;
    document.getElementById("mensal-conteudo").hidden = vazio;
    if (vazio) return;

    new Chart(document.getElementById("grafico-mensal"), {
      type: "bar",
      data: {
        labels: meses.map((m) => nomeDoMes(m.mes)),
        datasets: [
          { label: "Gastos", data: meses.map((m) => Number(m.despesas)),
            backgroundColor: COR_GASTO, borderRadius: 4, maxBarThickness: 28 },
          { label: "Recebimentos", data: meses.map((m) => Number(m.receitas)),
            backgroundColor: COR_RECEBIDO, borderRadius: 4, maxBarThickness: 28 },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${formatarMoeda(ctx.parsed.y)}` } },
        },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { maxTicksLimit: 5, callback: (v) => `R$ ${Number(v).toLocaleString("pt-BR")}` } },
        },
      },
    });
  }

  async function carregar() {
    const filtro = periodo();
    try {
      const [resumo, meses] = await Promise.all([
        buscar(`/api/financas/resumo?${filtro}`),
        buscar(`/api/financas/mensal?${filtro}`),
      ]);
      desenharCategorias(resumo);
      desenharMensal(meses);
    } catch (erro) {
      document.getElementById("erro-graficos").hidden = false;
    }
  }

  carregar();
})();
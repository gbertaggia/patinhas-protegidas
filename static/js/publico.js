document.addEventListener("DOMContentLoaded", () => {
  let dadosApp = { valoresDoacao: [], ongs: [] };
  let ongSelecionada = null;
  let limiteAnimaisExibidos = 6;
  const PASSO_PAGINACAO = 6;
  const FOTO_PADRAO = "https://dummyimage.com/600x400/e9ecef/6c757d.png&text=Sem+foto";

  const elementos = {
    telaOngs: document.getElementById("tela-ongs"),
    telaOng: document.getElementById("tela-ong"),
    buscaOng: document.getElementById("busca-ong"),
    contadorOngs: document.getElementById("contador-ongs"),
    listaOngs: document.getElementById("lista-ongs"),
    estadoOngs: document.getElementById("estado-ongs"),
    voltarOngs: document.getElementById("voltar-ongs"),

    ongAvatar: document.getElementById("ong-avatar"),
    ongNome: document.getElementById("ong-nome"),
    ongLocal: document.getElementById("ong-local"),
    ongDescricao: document.getElementById("ong-descricao"),

    contadorAnimais: document.getElementById("contador-animais"),
    listaAnimais: document.getElementById("lista-animais"),
    sentinelaAnimais: document.getElementById("sentinela-animais"),
    fimAnimais: document.getElementById("fim-animais"),
    listaCampanhas: document.getElementById("lista-campanhas"),
    semCampanhas: document.getElementById("sem-campanhas"),

    barraDoacao: document.getElementById("barra-doacao"),
    valoresDoacao: document.getElementById("valores-doacao"),
    doarValorLivre: document.getElementById("doar-valor-livre"),
    toast: document.getElementById("toast")
  };

  // ---------- Segurança: texto do servidor nunca entra como HTML ----------
  // Nomes, descrições e links vêm de quem se cadastrou. Por isso esta página
  // só monta elementos com createElement + textContent (que tratam tudo como
  // texto) e nunca com innerHTML. Veja também urlSegura() para endereços.

  function criar(tag, classe, texto) {
    const elemento = document.createElement(tag);
    if (classe) elemento.className = classe;
    if (texto !== undefined && texto !== null) elemento.textContent = texto;
    return elemento;
  }

  // Só aceita endereços http(s). Qualquer outra coisa (javascript:, data:...) vira null.
  function urlSegura(url) {
    if (typeof url !== "string" || !url.trim()) return null;
    try {
      const endereco = new URL(url.trim(), window.location.origin);
      return endereco.protocol === "http:" || endereco.protocol === "https:" ? endereco.href : null;
    } catch (erro) {
      return null;
    }
  }

  function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  // Foto com texto alternativo; se o link estiver quebrado, usa a foto padrão
  function criarImagem(classe, url, textoAlternativo) {
    const imagem = criar("img", classe);
    imagem.alt = textoAlternativo || "";
    imagem.src = urlSegura(url) || FOTO_PADRAO;
    imagem.addEventListener("error", () => { imagem.src = FOTO_PADRAO; }, { once: true });
    return imagem;
  }

  // Logo da organização, com o ícone de patinha como alternativa
  function preencherAvatar(recipiente, logoUrl, icone) {
    recipiente.replaceChildren();
    const url = urlSegura(logoUrl);
    if (!url) {
      recipiente.textContent = icone;
      return;
    }
    const imagem = criar("img", "avatar-img");
    imagem.alt = "";
    imagem.src = url;
    imagem.addEventListener("error", () => { recipiente.textContent = icone; }, { once: true });
    recipiente.appendChild(imagem);
  }

  // ---------- Carregamento ----------

  async function carregarDados() {
    try {
      const resposta = await fetch("/api/publico/dados");
      if (!resposta.ok) {
        throw new Error(`Erro na requisição: ${resposta.statusText}`);
      }
      dadosApp = await resposta.json();

      renderizarListaOngs(dadosApp.ongs);
      renderizarValoresDoacao(dadosApp.valoresDoacao || []);
    } catch (erro) {
      console.error("Erro ao carregar os dados:", erro);
      elementos.estadoOngs.textContent = "Não foi possível carregar as organizações agora. Tente novamente em instantes.";
      elementos.estadoOngs.classList.remove("hidden");
      mostrarToast("Erro ao carregar informações das organizações.");
    }
  }

  function renderizarListaOngs(ongs) {
    elementos.listaOngs.replaceChildren();

    if (!ongs || ongs.length === 0) {
      elementos.estadoOngs.classList.remove("hidden");
      elementos.contadorOngs.textContent = "0 organizações encontradas";
      return;
    }

    elementos.estadoOngs.classList.add("hidden");
    elementos.contadorOngs.textContent = `${ongs.length} ${ongs.length === 1 ? "organização encontrada" : "organizações encontradas"}`;

    ongs.forEach((ong) => {
      const card = criar("article", "ong-card");
      card.tabIndex = 0;

      const icone = criar("div", "ong-icon");
      preencherAvatar(icone, ong.logoUrl, ong.icone || "🐾");

      const regiao = criar("p");
      regiao.appendChild(criar("strong", null, ong.regiao || ""));

      const corpo = criar("div");
      corpo.append(
        criar("h3", null, ong.nome),
        regiao,
        criar("p", null, ong.resumo || ""),
        criar("span", "card-arrow", "Ver animais e apoiar →")
      );

      card.append(icone, corpo);

      card.addEventListener("click", () => abrirPaginaOng(ong));
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          abrirPaginaOng(ong);
        }
      });

      elementos.listaOngs.appendChild(card);
    });
  }

  elementos.buscaOng.addEventListener("input", (e) => {
    const termo = e.target.value.toLowerCase().trim();
    const filtradas = (dadosApp.ongs || []).filter(
      (ong) =>
        (ong.nome && ong.nome.toLowerCase().includes(termo)) ||
        (ong.regiao && ong.regiao.toLowerCase().includes(termo)) ||
        (ong.resumo && ong.resumo.toLowerCase().includes(termo))
    );
    renderizarListaOngs(filtradas);
  });

  function abrirPaginaOng(ong) {
    ongSelecionada = ong;
    limiteAnimaisExibidos = PASSO_PAGINACAO;

    // Avatar da ONG (Logo ou Ícone)
    preencherAvatar(elementos.ongAvatar, ong.logoUrl, ong.icone || "🐾");
    elementos.ongNome.textContent = ong.nome;
    elementos.ongLocal.textContent = ong.regiao;
    elementos.ongDescricao.textContent = ong.descricao || "Nenhuma descrição informada.";

    renderizarAnimais();
    renderizarCampanhas();

    elementos.telaOngs.classList.add("hidden");
    elementos.telaOng.classList.remove("hidden");
    atualizarBarraDoacao();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Volta para a lista de ONGs
  if (elementos.voltarOngs) {
    elementos.voltarOngs.addEventListener("click", () => {
      elementos.telaOng.classList.add("hidden");
      elementos.barraDoacao.classList.add("hidden");
      elementos.telaOngs.classList.remove("hidden");
      ongSelecionada = null;
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function renderizarAnimais() {
    elementos.listaAnimais.replaceChildren();
    const animais = ongSelecionada.animais || [];
    elementos.contadorAnimais.textContent = `${animais.length} ${animais.length === 1 ? "animal" : "animais"}`;

    if (animais.length === 0) {
      elementos.listaAnimais.appendChild(
        criar("p", "empty-state", "Nenhum animal disponível para adoção no momento.")
      );
      elementos.sentinelaAnimais.classList.add("hidden");
      elementos.fimAnimais.classList.add("hidden");
      return;
    }

    const animaisParaExibir = animais.slice(0, limiteAnimaisExibidos);
    const linkAdocao = urlSegura(ongSelecionada.linkFormulario);

    animaisParaExibir.forEach((animal) => {
      const card = criar("article", "animal-card");

      const detalhesSaude = [
        animal.castrado ? "Castrado" : null,
        animal.vacinado ? "Vacinado" : null,
        animal.temChip ? "Microchipado" : null
      ].filter(Boolean).join(" • ");

      // Botão habilitado ou desabilitado conforme a presença de link de formulário
      const botaoAdocao = criar("button", "outline-button");
      botaoAdocao.type = "button";
      if (linkAdocao) {
        botaoAdocao.classList.add("btn-adotar");
        botaoAdocao.textContent = "Quero Adotar";
        botaoAdocao.addEventListener("click", () => {
          window.open(linkAdocao, "_blank", "noopener,noreferrer");
        });
      } else {
        botaoAdocao.classList.add("btn-desabilitado");
        botaoAdocao.textContent = "Adoção indisponível";
        botaoAdocao.disabled = true;
        botaoAdocao.title = "Esta organização ainda não cadastrou o formulário de adoção";
      }

      const informacoes = criar("div", "animal-info");
      informacoes.append(
        criar("span", "tag", animal.especie),
        criar("h3", null, animal.nome),
        criar("div", "animal-meta", [animal.raca, animal.idade].filter(Boolean).join(" • "))
      );

      if (detalhesSaude) {
        const saude = criar("p", "animal-description");
        saude.style.marginBottom = "6px";
        saude.append(criar("strong", null, "Saúde:"), ` ${detalhesSaude}`);
        informacoes.appendChild(saude);
      }
      if (animal.infoSaude) {
        informacoes.appendChild(criar("p", "animal-description", animal.infoSaude));
      }
      informacoes.appendChild(botaoAdocao);

      card.append(criarImagem("animal-photo", animal.foto, animal.nome), informacoes);
      elementos.listaAnimais.appendChild(card);
    });

    if (limiteAnimaisExibidos >= animais.length) {
      elementos.sentinelaAnimais.classList.add("hidden");
      elementos.fimAnimais.classList.remove("hidden");
    } else {
      elementos.sentinelaAnimais.classList.remove("hidden");
      elementos.fimAnimais.classList.add("hidden");
    }
  }

  const observadorScroll = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && ongSelecionada) {
      const totalAnimais = (ongSelecionada.animais || []).length;
      if (limiteAnimaisExibidos < totalAnimais) {
        limiteAnimaisExibidos += PASSO_PAGINACAO;
        renderizarAnimais();
      }
    }
  }, { rootMargin: "100px" });

  observadorScroll.observe(elementos.sentinelaAnimais);

  function renderizarCampanhas() {
    elementos.listaCampanhas.replaceChildren();
    const campanhas = ongSelecionada.campanhas || [];

    if (campanhas.length === 0) {
      elementos.semCampanhas.classList.remove("hidden");
      return;
    }

    elementos.semCampanhas.classList.add("hidden");

    campanhas.forEach((campanha) => {
      const meta = Number(campanha.meta) || 1;
      const arrecadado = Number(campanha.arrecadado) || 0;
      const percentual = Math.min(100, Math.round((arrecadado / meta) * 100));

      const card = criar("article", "campaign-card");

      const barra = criar("div", "progress-track");
      const preenchimento = criar("div", "progress-fill");
      preenchimento.style.width = `${percentual}%`;
      barra.appendChild(preenchimento);

      const totais = criar("div", "campaign-totals");
      const textoArrecadado = criar("span", null, "Arrecadado: ");
      textoArrecadado.appendChild(criar("strong", null, formatarMoeda(arrecadado)));
      const textoMeta = criar("span", null, "Meta: ");
      textoMeta.appendChild(criar("strong", null, formatarMoeda(meta)));
      totais.append(textoArrecadado, textoMeta);

      const botaoDoar = criar("button", "donate-button", "Ajudar com esta campanha");
      botaoDoar.type = "button";
      botaoDoar.addEventListener("click", () => {
        window.abrirDoacaoPix(campanha);
      });

      const corpo = criar("div", "campaign-body");
      corpo.append(
        criar("h3", null, campanha.titulo),
        criar("p", null, campanha.descricao),
        barra,
        totais,
        botaoDoar
      );

      card.append(criarImagem(null, campanha.foto, campanha.titulo), corpo);
      elementos.listaCampanhas.appendChild(card);
    });
  }

  // ---------- Doação geral (barra fixa) ----------
  // Os botões de valor abrem a tela de Pix da campanha de "despesas gerais"
  // da organização (a que não está ligada a nenhum animal). Se a organização
  // não tem essa campanha, a barra fica escondida: não existe para onde doar.
  // O cartão "Protetores independentes" (id 0) junta várias pessoas, então
  // também não tem doação geral.

  function campanhaGeralDaOng(ong) {
    if (!ong || ong.id === 0) return null;
    return (ong.campanhas || []).find((c) => c.animalId === null || c.animalId === undefined) || null;
  }

  function atualizarBarraDoacao() {
    elementos.barraDoacao.classList.toggle("hidden", !campanhaGeralDaOng(ongSelecionada));
  }

  function doarParaDespesasGerais(valor) {
    const campanha = campanhaGeralDaOng(ongSelecionada);
    if (!campanha) {
      mostrarToast("Esta organização ainda não tem uma campanha de despesas gerais.");
      return;
    }
    window.abrirDoacaoPix(campanha, valor);
  }

  function renderizarValoresDoacao(valores) {
    elementos.valoresDoacao.replaceChildren();
    valores.forEach((valor) => {
      const botao = criar("button", "amount-button", `R$ ${valor}`);
      botao.type = "button";
      botao.addEventListener("click", () => doarParaDespesasGerais(valor));
      elementos.valoresDoacao.appendChild(botao);
    });
  }

  elementos.doarValorLivre.addEventListener("click", () => doarParaDespesasGerais());

  function mostrarToast(mensagem) {
    elementos.toast.textContent = mensagem;
    elementos.toast.classList.remove("hidden");
    setTimeout(() => {
      elementos.toast.classList.add("hidden");
    }, 3500);
  }

  carregarDados();
});

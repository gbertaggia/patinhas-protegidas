document.addEventListener("DOMContentLoaded", () => {
  let dadosApp = { valoresDoacao: [], ongs: [] };
  let ongSelecionada = null;
  let limiteAnimaisExibidos = 6;
  const PASSO_PAGINACAO = 6;

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
    ongLinkHero: document.getElementById("ong-link-formulario"),
    
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

  // Helper para renderizar logo com fallback para ícone
  function gerarHtmlAvatar(logoUrl, iconePadrao = "🐾") {
    if (logoUrl) {
      return `<img src="${logoUrl}" alt="Logo" class="avatar-img" onerror="this.parentElement.textContent='${iconePadrao}'">`;
    }
    return iconePadrao;
  }

  // Carrega os dados direto da API do banco de dados
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
      mostrarToast("Erro ao carregar informações das ONGs.");
    }
  }

  function renderizarListaOngs(ongs) {
    elementos.listaOngs.innerHTML = "";

    if (!ongs || ongs.length === 0) {
      elementos.estadoOngs.classList.remove("hidden");
      elementos.contadorOngs.textContent = "0 ONGs encontradas";
      return;
    }

    elementos.estadoOngs.classList.add("hidden");
    elementos.contadorOngs.textContent = `${ongs.length} ${ongs.length === 1 ? "organização encontrada" : "organizações encontradas"}`;

    ongs.forEach((ong) => {
      const card = document.createElement("article");
      card.className = "ong-card";
      card.tabIndex = 0;
      card.innerHTML = `
        <div class="ong-icon">${gerarHtmlAvatar(ong.logoUrl, ong.icone || "🐾")}</div>
        <div>
          <h3>${ong.nome}</h3>
          <p><strong>${ong.regiao || ""}</strong></p>
          <p>${ong.resumo || ""}</p>
          <span class="card-arrow">Ver animais e apoiar →</span>
        </div>
      `;

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
    elementos.ongAvatar.innerHTML = gerarHtmlAvatar(ong.logoUrl, ong.icone || "🐾");
    elementos.ongNome.textContent = ong.nome;
    elementos.ongLocal.textContent = ong.regiao;
    elementos.ongDescricao.textContent = ong.descricao || "Nenhuma descrição informada.";
  
    // Botão de formulário geral no banner superior
    if (elementos.ongLinkHero) {
      if (ong.linkFormulario) {
        elementos.ongLinkHero.href = ong.linkFormulario;
        elementos.ongLinkHero.classList.remove("hidden");
      } else {
        elementos.ongLinkHero.classList.add("hidden");
      }
    }
  
    renderizarAnimais();
    renderizarCampanhas();
  
    elementos.telaOngs.classList.add("hidden");
    elementos.telaOng.classList.remove("hidden");
    elementos.barraDoacao.classList.remove("hidden");
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
    elementos.listaAnimais.innerHTML = "";
    const animais = ongSelecionada.animais || [];
    elementos.contadorAnimais.textContent = `${animais.length} ${animais.length === 1 ? "animal" : "animais"}`;

    if (animais.length === 0) {
      elementos.listaAnimais.innerHTML = '<p class="empty-state">Nenhum animal disponível para adoção no momento.</p>';
      elementos.sentinelaAnimais.classList.add("hidden");
      elementos.fimAnimais.classList.add("hidden");
      return;
    }

    const animaisParaExibir = animais.slice(0, limiteAnimaisExibidos);
    const temFormulario = Boolean(ongSelecionada && ongSelecionada.linkFormulario);

    animaisParaExibir.forEach((animal) => {
      const card = document.createElement("article");
      card.className = "animal-card";
      
      const detalhesSaude = [
        animal.castrado ? "Castrado" : null,
        animal.vacinado ? "Vacinado" : null,
        animal.temChip ? "Microchipado" : null
      ].filter(Boolean).join(" • ");

      // Botão habilitado ou desabilitado conforme a presença de link de formulário
      const botaoAdocaoHtml = temFormulario
        ? `<button class="outline-button btn-adotar" type="button">Quero Adotar</button>`
        : `<button class="outline-button btn-desabilitado" type="button" disabled title="Esta organização ainda não cadastrou o formulário de adoção">Adoção indisponível</button>`;

      card.innerHTML = `
        <img class="animal-photo" src="${animal.foto}" alt="${animal.nome}">
        <div class="animal-info">
          <span class="tag">${animal.especie}</span>
          <h3>${animal.nome}</h3>
          <div class="animal-meta">${animal.raca ? animal.raca + ' • ' : ''}${animal.idade}</div>
          ${detalhesSaude ? `<p class="animal-description" style="margin-bottom: 6px;"><strong>Saúde:</strong> ${detalhesSaude}</p>` : ''}
          ${animal.infoSaude ? `<p class="animal-description">${animal.infoSaude}</p>` : ''}
          ${botaoAdocaoHtml}
        </div>
      `;

      if (temFormulario) {
        card.querySelector(".btn-adotar").addEventListener("click", () => {
          window.open(ongSelecionada.linkFormulario, "_blank", "noopener,noreferrer");
        });
      }

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
    elementos.listaCampanhas.innerHTML = "";
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

      const card = document.createElement("article");
      card.className = "campaign-card";
      card.innerHTML = `
        <img src="${campanha.foto}" alt="${campanha.titulo}">
        <div class="campaign-body">
          <h3>${campanha.titulo}</h3>
          <p>${campanha.descricao}</p>
          <div class="progress-track">
            <div class="progress-fill" style="width: ${percentual}%"></div>
          </div>
          <div class="campaign-totals">
            <span>Arrecadado: <strong>R$ ${arrecadado}</strong></span>
            <span>Meta: <strong>R$ ${meta}</strong></span>
          </div>
          <button class="donate-button" type="button">Ajudar com esta campanha</button>
        </div>
      `;

      card.querySelector(".donate-button").addEventListener("click", () => {
        window.abrirDoacaoPix(campanha);
      });

      elementos.listaCampanhas.appendChild(card);
    });
  }

  function renderizarValoresDoacao(valores) {
    elementos.valoresDoacao.innerHTML = "";
    valores.forEach((valor) => {
      const botao = document.createElement("button");
      botao.className = "amount-button";
      botao.type = "button";
      botao.textContent = `R$ ${valor}`;
      botao.addEventListener("click", () => {
        const nomeOng = ongSelecionada ? ongSelecionada.nome : "a organização";
        mostrarToast(`Obrigado pela doação de R$ ${valor} para ${nomeOng}! ❤️`);
      });
      elementos.valoresDoacao.appendChild(botao);
    });
  }

  elementos.doarValorLivre.addEventListener("click", () => {
    const valorDigitado = prompt("Digite o valor que deseja doar (R$):");
    if (valorDigitado && !isNaN(valorDigitado) && Number(valorDigitado) > 0) {
      const nomeOng = ongSelecionada ? ongSelecionada.nome : "a organização";
      mostrarToast(`Obrigado pela doação de R$ ${Number(valorDigitado).toFixed(2)} para ${nomeOng}! ❤️`);
    } else if (valorDigitado !== null) {
      mostrarToast("Por favor, informe um valor válido.");
    }
  });

  function mostrarToast(mensagem) {
    elementos.toast.textContent = mensagem;
    elementos.toast.classList.remove("hidden");
    setTimeout(() => {
      elementos.toast.classList.add("hidden");
    }, 3500);
  }

  carregarDados();
});
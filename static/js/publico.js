document.addEventListener("DOMContentLoaded", () => {
  // Variáveis de estado global
  let dadosApp = { valoresDoacao: [], ongs: [] };
  let ongSelecionada = null;
  let limiteAnimaisExibidos = 3;
  const PASSO_PAGINACAO = 3;

  // Mapeamento dos elementos do DOM
  const elementos = {
    telaOngs: document.getElementById("tela-ongs"),
    telaOng: document.getElementById("tela-ong"),
    buscaOng: document.getElementById("busca-ong"),
    contadorOngs: document.getElementById("contador-ongs"),
    listaOngs: document.getElementById("lista-ongs"),
    estadoOngs: document.getElementById("estado-ongs"),
    voltarOngs: document.getElementById("voltar-ongs"),
    
    // Detalhes da ONG
    ongAvatar: document.getElementById("ong-avatar"),
    ongNome: document.getElementById("ong-nome"),
    ongLocal: document.getElementById("ong-local"),
    ongDescricao: document.getElementById("ong-descricao"),
    
    // Listas de animais e campanhas
    contadorAnimais: document.getElementById("contador-animais"),
    listaAnimais: document.getElementById("lista-animais"),
    sentinelaAnimais: document.getElementById("sentinela-animais"),
    fimAnimais: document.getElementById("fim-animais"),
    listaCampanhas: document.getElementById("lista-campanhas"),
    semCampanhas: document.getElementById("sem-campanhas"),
    
    // Barra de doação
    barraDoacao: document.getElementById("barra-doacao"),
    valoresDoacao: document.getElementById("valores-doacao"),
    doarValorLivre: document.getElementById("doar-valor-livre"),
    toast: document.getElementById("toast")
  };

  // Carrega o JSON da pasta static/data/
  async function carregarDados() {
    try {
      const resposta = await fetch("/static/data/dados.json");
      if (!resposta.ok) {
        throw new Error(`Erro na requisição: ${resposta.statusText}`);
      }
      dadosApp = await resposta.json();
      
      // Renderizações iniciais
      renderizarListaOngs(dadosApp.ongs);
      renderizarValoresDoacao(dadosApp.valoresDoacao);
    } catch (erro) {
      console.error("Erro ao carregar os dados:", erro);
      mostrarToast("Erro ao carregar informações das ONGs.");
    }
  }

  // Renderiza o grid de ONGs
  function renderizarListaOngs(ongs) {
    elementos.listaOngs.innerHTML = "";

    if (!ongs || ongs.length === 0) {
      elementos.estadoOngs.classList.remove("hidden");
      elementos.contadorOngs.textContent = "0 ONGs encontradas";
      return;
    }

    elementos.estadoOngs.classList.add("hidden");
    elementos.contadorOngs.textContent = `${ongs.length} ${ongs.length === 1 ? "ONG encontrada" : "ONGs encontradas"}`;

    ongs.forEach((ong) => {
      const card = document.createElement("article");
      card.className = "ong-card";
      card.tabIndex = 0;
      card.innerHTML = `
        <div class="ong-icon">${ong.icone || "🐾"}</div>
        <div>
          <h3>${ong.nome}</h3>
          <p><strong>${ong.regiao}</strong></p>
          <p>${ong.resumo}</p>
          <span class="card-arrow">Ver animais e doar →</span>
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

  // Filtra as ONGs no campo de busca
  elementos.buscaOng.addEventListener("input", (e) => {
    const termo = e.target.value.toLowerCase().trim();
    const filtradas = dadosApp.ongs.filter(
      (ong) =>
        ong.nome.toLowerCase().includes(termo) ||
        ong.regiao.toLowerCase().includes(termo) ||
        ong.resumo.toLowerCase().includes(termo)
    );
    renderizarListaOngs(filtradas);
  });

  // Abre a tela detalhada de uma ONG
  function abrirPaginaOng(ong) {
    ongSelecionada = ong;
    limiteAnimaisExibidos = PASSO_PAGINACAO;
  
    elementos.ongAvatar.textContent = ong.icone || "🐾";
    elementos.ongNome.textContent = ong.nome;
    elementos.ongLocal.textContent = ong.regiao;
    elementos.ongDescricao.textContent = ong.descricao;
  
    // Lógica para o link do formulário da ONG
    const linkForm = document.getElementById("ong-link-formulario");
    if (linkForm) {
      if (ong.linkFormulario) {
        linkForm.href = ong.linkFormulario;
        linkForm.classList.remove("hidden");
      } else {
        linkForm.classList.add("hidden");
      }
    }
  
    renderizarAnimais();
    renderizarCampanhas();
  
    elementos.telaOngs.classList.add("hidden");
    elementos.telaOng.classList.remove("hidden");
    elementos.barraDoacao.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Renderiza a lista de animais com suporte a paginação gradual
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

    animaisParaExibir.forEach((animal) => {
      const card = document.createElement("article");
      card.className = "animal-card";
      card.innerHTML = `
        <img class="animal-photo" src="${animal.foto}" alt="${animal.nome}">
        <div class="animal-info">
          <span class="tag">${animal.especie}</span>
          <h3>${animal.nome}</h3>
          <div class="animal-meta">${animal.idade} • Porte ${animal.porte}</div>
          <p class="animal-description">${animal.descricao}</p>
          <button class="outline-button" type="button">Quero Adotar</button>
        </div>
      `;

      card.querySelector(".outline-button").addEventListener("click", () => {
        if (ongSelecionada && ongSelecionada.linkFormulario) {
          window.open(ongSelecionada.linkFormulario, "_blank");
        } else {
          mostrarToast(`Interesse em adotar ${animal.nome} registrado com sucesso!`);
        }
      });

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

  // Configuração da rolagem infinita/gradual para carregar mais animais
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

  // Renderiza as campanhas de arrecadação
  function renderizarCampanhas() {
    elementos.listaCampanhas.innerHTML = "";
    const campanhas = ongSelecionada.campanhas || [];

    if (campanhas.length === 0) {
      elementos.semCampanhas.classList.remove("hidden");
      return;
    }

    elementos.semCampanhas.classList.add("hidden");

    campanhas.forEach((campanha) => {
      const percentual = Math.min(100, Math.round((campanha.arrecadado / campanha.meta) * 100));
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
            <span>Arrecadado: <strong>R$ ${campanha.arrecadado}</strong></span>
            <span>Meta: <strong>R$ ${campanha.meta}</strong></span>
          </div>
          <button class="donate-button" type="button">Ajudar com esta campanha</button>
        </div>
      `;

      card.querySelector(".donate-button").addEventListener("click", () => {
        mostrarToast(`Obrigado por apoiar a campanha "${campanha.titulo}"!`);
      });

      elementos.listaCampanhas.appendChild(card);
    });
  }

  // Renderiza os botões de doação da barra inferior
  function renderizarValoresDoacao(valores) {
    elementos.valoresDoacao.innerHTML = "";
    valores.forEach((valor) => {
      const botao = document.createElement("button");
      botao.className = "amount-button";
      botao.type = "button";
      botao.textContent = `R$ ${valor}`;
      botao.addEventListener("click", () => {
        const nomeOng = ongSelecionada ? ongSelecionada.nome : "a ONG";
        mostrarToast(`Obrigado pela doação de R$ ${valor} para ${nomeOng}! ❤️`);
      });
      elementos.valoresDoacao.appendChild(botao);
    });
  }

  // Ação para doação com valor customizado
  elementos.doarValorLivre.addEventListener("click", () => {
    const valorDigitado = prompt("Digite o valor que deseja doar (R$):");
    if (valorDigitado && !isNaN(valorDigitado) && Number(valorDigitado) > 0) {
      const nomeOng = ongSelecionada ? ongSelecionada.nome : "a ONG";
      mostrarToast(`Obrigado pela doação de R$ ${Number(valorDigitado).toFixed(2)} para ${nomeOng}! ❤️`);
    } else if (valorDigitado !== null) {
      mostrarToast("Por favor, informe um valor válido.");
    }
  });

  // Exibe mensagens de notificação (Toast)
  function mostrarToast(mensagem) {
    elementos.toast.textContent = mensagem;
    elementos.toast.classList.remove("hidden");
    setTimeout(() => {
      elementos.toast.classList.add("hidden");
    }, 3500);
  }

  // Inicializa o carregamento dos dados
  carregarDados();
});
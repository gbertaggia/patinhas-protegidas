// Janela de doação via Pix das campanhas (página pública).
// Usa a biblioteca QRCode (qrcodejs), carregada antes deste arquivo no publico.html.
(function () {
  "use strict";

  const VALORES = [10, 20, 50, 100, 200];

  // ---------- Pix "copia e cola" (padrão BR Code do Banco Central) ----------

  // Tira acentos e caracteres especiais: o padrão só aceita texto simples.
  function textoSimples(texto, limite) {
    return (texto || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^A-Za-z0-9 ]/g, "")
      .trim()
      .toUpperCase()
      .slice(0, limite);
  }

  function campo(id, valor) {
    return id + String(valor.length).padStart(2, "0") + valor;
  }

  function crc16(texto) {
    let crc = 0xffff;
    for (let i = 0; i < texto.length; i++) {
      crc ^= texto.charCodeAt(i) << 8;
      for (let j = 0; j < 8; j++) {
        crc = crc & 0x8000 ? (crc << 1) ^ 0x1021 : crc << 1;
        crc &= 0xffff;
      }
    }
    return crc.toString(16).toUpperCase().padStart(4, "0");
  }

  function montarPixCopiaECola(chave, valor, recebedor, cidade) {
    const conta = campo("00", "br.gov.bcb.pix") + campo("01", chave);
    let payload =
      campo("00", "01") +
      campo("26", conta) +
      campo("52", "0000") +
      campo("53", "986");
    if (valor > 0) {
      payload += campo("54", valor.toFixed(2));
    }
    payload +=
      campo("58", "BR") +
      campo("59", textoSimples(recebedor, 25) || "PATINHAS PROTEGIDAS") +
      campo("60", textoSimples(cidade, 15) || "BRASIL") +
      campo("62", campo("05", "***")) +
      "6304";
    return payload + crc16(payload);
  }

  // ---------- Estilos da janela ----------

  const CSS = `
    .pix-fundo { position: fixed; inset: 0; background: rgba(30, 20, 50, .55);
      display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 1000; }
    .pix-janela { background: #f7f5fb; border-radius: 18px; width: 100%; max-width: 880px;
      max-height: calc(100vh - 32px); overflow-y: auto; padding: 22px 22px 24px; position: relative;
      box-shadow: 0 24px 60px rgba(0, 0, 0, .28); font-family: inherit; color: #1e1b2e; }
    .pix-topo { display: flex; align-items: center; gap: 12px; margin: 0 0 16px; padding-right: 40px; }
    .pix-topo svg { width: 30px; height: 30px; flex-shrink: 0; }
    .pix-titulo { font-size: 1.35rem; font-weight: 800; margin: 0; color: #5b21b6; }
    .pix-fechar { position: absolute; top: 14px; right: 16px; border: 0; background: none;
      width: 36px; height: 36px; border-radius: 8px; cursor: pointer; color: #4b4560;
      display: grid; place-items: center; }
    .pix-fechar:hover { background: #ece7f6; }
    .pix-fechar svg { width: 22px; height: 22px; }
    .pix-grade { display: grid; grid-template-columns: 1.35fr 1fr; gap: 20px; align-items: start; }
    .pix-coluna { display: flex; flex-direction: column; gap: 14px; }
    .pix-cartao { background: #fff; border: 1px solid #ebe6f3; border-radius: 14px; padding: 18px; }
    .pix-campanha { display: flex; gap: 16px; align-items: center; }
    .pix-campanha img { width: 120px; height: 100px; object-fit: cover; border-radius: 10px;
      flex-shrink: 0; background: #ece7f6; }
    .pix-campanha h3 { font-size: 1.1rem; font-weight: 800; margin: 0 0 6px; color: #5b21b6; }
    .pix-campanha p { font-size: .92rem; margin: 0; color: #5f5a70; line-height: 1.45; }
    .pix-rotulo { font-weight: 700; margin: 0 0 12px; display: block; }
    .pix-rotulo-leve { font-weight: 500; color: #4b4560; margin: 16px 0 8px; display: block; }
    .pix-valores { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .pix-valor { border: 1px solid #e3ddee; background: #fff; border-radius: 10px; padding: 14px 4px;
      font-weight: 700; font-size: 1rem; cursor: pointer; color: #1e1b2e; font-family: inherit; }
    .pix-valor:hover { border-color: #b9a6e6; }
    .pix-valor.ativo { border-color: #a78bfa; background: #f1ebff; color: #4c1d95; }
    .pix-outro { display: flex; align-items: stretch; border: 1px solid #e3ddee; border-radius: 10px;
      overflow: hidden; background: #fff; }
    .pix-outro span { padding: 12px 14px; background: #f4f2f8; color: #5f5a70; border-right: 1px solid #e3ddee; }
    .pix-outro input { border: 0; padding: 12px; flex: 1; font: inherit; min-width: 0; }
    .pix-aviso { display: flex; gap: 10px; font-size: .85rem; color: #4b4560; background: #f1ebff;
      border-radius: 10px; padding: 12px 14px; margin-top: 16px; line-height: 1.45; }
    .pix-aviso svg { width: 20px; height: 20px; flex-shrink: 0; color: #5b21b6; margin-top: 1px; }
    .pix-lado-topo { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
    .pix-selo { width: 30px; height: 30px; flex-shrink: 0; display: grid; place-items: center; }
    .pix-selo i { width: 20px; height: 20px; background: #32bcad; border-radius: 4px; transform: rotate(45deg); }
    .pix-lado-topo strong { font-size: 1.05rem; }
    .pix-instrucao { font-size: .9rem; color: #5f5a70; margin: 0 0 16px; line-height: 1.45; }
    .pix-qr-area { text-align: center; }
    .pix-qr { display: inline-block; padding: 14px; background: #fff; border: 1px solid #ebe6f3;
      border-radius: 12px; }
    .pix-qr img, .pix-qr canvas { display: block; }
    .pix-legenda { font-size: .85rem; color: #5f5a70; margin: 8px 0 18px; text-align: center; }
    .pix-chave { display: flex; border: 1px solid #e3ddee; border-radius: 10px; overflow: hidden;
      margin-bottom: 14px; background: #fff; }
    .pix-chave input { border: 0; padding: 12px; flex: 1; font: inherit; min-width: 0; color: #4b4560; background: #fff; }
    .pix-icone-copiar { border: 0; border-left: 1px solid #e3ddee; background: #f4f2f8; width: 48px;
      cursor: pointer; color: #4b4560; display: grid; place-items: center; }
    .pix-icone-copiar:hover { background: #ece7f6; }
    .pix-icone-copiar svg { width: 20px; height: 20px; }
    .pix-botao { width: 100%; border: 0; border-radius: 10px; padding: 14px; background: #6d28d9;
      color: #fff; font-weight: 700; font-size: 1rem; cursor: pointer; font-family: inherit;
      display: flex; align-items: center; justify-content: center; gap: 10px; }
    .pix-botao:hover { background: #5b21b6; }
    .pix-botao svg { width: 20px; height: 20px; }
    .pix-link { display: block; margin: 12px auto 0; background: none; border: 0; color: #6d28d9;
      font: inherit; font-size: .88rem; font-weight: 600; cursor: pointer; text-decoration: underline; }
    .pix-sem-chave { color: #5f5a70; padding: 12px 0; line-height: 1.5; }
    .pix-fundo button:focus-visible, .pix-fundo input:focus-visible { outline: 3px solid #a78bfa; outline-offset: 2px; }
    @media (max-width: 720px) {
      .pix-grade { grid-template-columns: 1fr; }
      .pix-campanha img { width: 88px; height: 76px; }
    }
  `;

  function garantirEstilos() {
    if (document.getElementById("pix-estilos")) return;
    const estilo = document.createElement("style");
    estilo.id = "pix-estilos";
    estilo.textContent = CSS;
    document.head.appendChild(estilo);
  }

  // ---------- Ícones ----------

  const ICONE_CORACAO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#ec4d6e" d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.8 4.5c2.1 0 3.6 1.2 5.2 3 1.6-1.8 3.1-3 5.2-3 3.8 0 5.9 3.9 4.4 7.3C19.5 16.4 12 21 12 21z"/></svg>';
  const ICONE_FECHAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  const ICONE_INFO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.5"/></svg>';
  const ICONE_COPIAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>';

  // ---------- Tipo e exibição da chave ----------

  function tipoDaChave(chave) {
    if (chave.includes("@")) return "e-mail";
    if (chave.startsWith("+")) return "telefone";
    if (/^\d{14}$/.test(chave)) return "CNPJ";
    if (/^\d{11}$/.test(chave)) return "CPF";
    return "chave aleatória";
  }

  function chaveFormatada(chave) {
    if (/^\d{14}$/.test(chave)) return chave.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");
    if (/^\d{11}$/.test(chave)) return chave.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
    const telefone = chave.match(/^\+55(\d{2})(\d{4,5})(\d{4})$/);
    if (telefone) return `+55 (${telefone[1]}) ${telefone[2]}-${telefone[3]}`;
    return chave;
  }

  // ---------- Janela ----------

  function lerValor(texto) {
    const limpo = String(texto || "").replace(/\s/g, "").replace(/\./g, "").replace(",", ".");
    const numero = Number(limpo);
    return Number.isFinite(numero) && numero > 0 ? Math.round(numero * 100) / 100 : 0;
  }

  async function copiar(texto, botao, rotuloOriginal) {
    try {
      await navigator.clipboard.writeText(texto);
      botao.textContent = "Copiado!";
    } catch (erro) {
      botao.textContent = "Não foi possível copiar";
    }
    setTimeout(() => { botao.textContent = rotuloOriginal; }, 2000);
  }

  function abrirDoacaoPix(campanha) {
    garantirEstilos();

    const fundo = document.createElement("div");
    fundo.className = "pix-fundo";
    fundo.innerHTML = `
      <div class="pix-janela" role="dialog" aria-modal="true" aria-labelledby="pix-titulo">
        <div class="pix-topo">${ICONE_CORACAO}<h2 class="pix-titulo" id="pix-titulo">Doar para a campanha</h2></div>
        <button type="button" class="pix-fechar" aria-label="Fechar">${ICONE_FECHAR}</button>
        <div class="pix-grade">
          <div class="pix-coluna">
            <div class="pix-cartao pix-campanha">
              <img alt="">
              <div><h3></h3><p></p></div>
            </div>
            <div class="pix-cartao pix-escolha">
              <p class="pix-rotulo">Escolha um valor</p>
              <div class="pix-valores"></div>
              <label class="pix-rotulo-leve" for="pix-valor-livre">Ou insira um valor personalizado</label>
              <div class="pix-outro">
                <span>R$</span>
                <input id="pix-valor-livre" type="text" inputmode="decimal" placeholder="0,00" autocomplete="off">
              </div>
              <div class="pix-aviso">${ICONE_INFO}
                <span>Toda contribuição faz a diferença! O Pix vai direto para quem organizou a campanha:
                confira o nome do recebedor no app do seu banco antes de confirmar.</span>
              </div>
            </div>
          </div>
          <div class="pix-cartao pix-lado">
            <div class="pix-lado-topo"><span class="pix-selo" aria-hidden="true"><i></i></span><strong>Pagamento via PIX</strong></div>
          </div>
        </div>
      </div>
    `;

    // Textos da campanha entram com textContent (nunca como HTML)
    const imagem = fundo.querySelector(".pix-campanha img");
    if (campanha.foto) imagem.src = campanha.foto;
    fundo.querySelector(".pix-campanha h3").textContent = campanha.titulo;
    fundo.querySelector(".pix-campanha p").textContent = campanha.descricao;

    const lado = fundo.querySelector(".pix-lado");
    const areaValores = fundo.querySelector(".pix-valores");
    const campoLivre = fundo.querySelector("#pix-valor-livre");
    let valorEscolhido = 0;

    function fechar() {
      document.removeEventListener("keydown", aoTeclar);
      fundo.remove();
    }
    function aoTeclar(evento) {
      if (evento.key === "Escape") fechar();
    }
    fundo.querySelector(".pix-fechar").addEventListener("click", fechar);
    fundo.addEventListener("click", (evento) => { if (evento.target === fundo) fechar(); });
    document.addEventListener("keydown", aoTeclar);

    if (!campanha.chavePix) {
      fundo.querySelector(".pix-escolha").remove();
      const aviso = document.createElement("p");
      aviso.className = "pix-sem-chave";
      aviso.textContent = "Esta campanha ainda não tem chave Pix cadastrada. Volte mais tarde ou entre em contato com quem organizou.";
      lado.appendChild(aviso);
      document.body.appendChild(fundo);
      fundo.querySelector(".pix-fechar").focus();
      return;
    }

    lado.insertAdjacentHTML("beforeend", `
      <p class="pix-instrucao">Escaneie o QR Code ou copie a chave PIX para realizar a doação.</p>
      <div class="pix-qr-area"><div class="pix-qr" aria-label="QR Code do Pix" role="img"></div></div>
      <p class="pix-legenda"></p>
      <label class="pix-rotulo" for="pix-chave"></label>
      <div class="pix-chave">
        <input id="pix-chave" type="text" readonly>
        <button type="button" class="pix-icone-copiar" aria-label="Copiar chave Pix" title="Copiar chave Pix">${ICONE_COPIAR}</button>
      </div>
      <button type="button" class="pix-botao" data-acao="chave">${ICONE_COPIAR}<span>Copiar Chave PIX</span></button>
      <button type="button" class="pix-link" data-acao="copia-e-cola">Copiar Pix copia e cola</button>
    `);
    lado.querySelector('label[for="pix-chave"]').textContent = `Chave PIX (${tipoDaChave(campanha.chavePix)})`;
    lado.querySelector("#pix-chave").value = chaveFormatada(campanha.chavePix);
    const areaQr = lado.querySelector(".pix-qr");

    // Os dois botões de copiar levam a chave sem formatação, como os bancos esperam
    const botaoPrincipal = lado.querySelector('[data-acao="chave"]');
    botaoPrincipal.addEventListener("click", async () => {
      const rotulo = botaoPrincipal.querySelector("span");
      await copiar(campanha.chavePix, rotulo, "Copiar Chave PIX");
    });
    const botaoIcone = lado.querySelector(".pix-icone-copiar");
    botaoIcone.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(campanha.chavePix);
        botaoIcone.setAttribute("title", "Copiado!");
      } catch (erro) {
        botaoIcone.setAttribute("title", "Não foi possível copiar");
      }
    });

    function atualizarPix() {
      const codigo = montarPixCopiaECola(campanha.chavePix, valorEscolhido, campanha.recebedor, campanha.cidade);
      areaQr.innerHTML = "";
      new QRCode(areaQr, { text: codigo, width: 170, height: 170, correctLevel: QRCode.CorrectLevel.M });
      lado.querySelector('[data-acao="copia-e-cola"]').onclick = (evento) =>
        copiar(codigo, evento.currentTarget, "Copiar Pix copia e cola");
      lado.querySelector(".pix-legenda").textContent = valorEscolhido > 0
        ? `Valor: ${valorEscolhido.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}`
        : "Escolha um valor ou digite no app do banco";
    }

    function marcar(botao) {
      areaValores.querySelectorAll(".pix-valor").forEach((b) => b.classList.remove("ativo"));
      if (botao) botao.classList.add("ativo");
    }

    VALORES.forEach((valor) => {
      const botao = document.createElement("button");
      botao.type = "button";
      botao.className = "pix-valor";
      botao.textContent = `R$ ${valor}`;
      botao.addEventListener("click", () => {
        marcar(botao);
        campoLivre.value = "";
        valorEscolhido = valor;
        atualizarPix();
      });
      areaValores.appendChild(botao);
    });

    const botaoOutro = document.createElement("button");
    botaoOutro.type = "button";
    botaoOutro.className = "pix-valor";
    botaoOutro.textContent = "Outro";
    botaoOutro.addEventListener("click", () => {
      marcar(botaoOutro);
      campoLivre.focus();
      valorEscolhido = lerValor(campoLivre.value);
      atualizarPix();
    });
    areaValores.appendChild(botaoOutro);

    campoLivre.addEventListener("input", () => {
      marcar(botaoOutro);
      valorEscolhido = lerValor(campoLivre.value);
      atualizarPix();
    });

    // Começa com o primeiro valor já escolhido, como no modelo
    document.body.appendChild(fundo);
    areaValores.querySelector(".pix-valor").click();
    fundo.querySelector(".pix-fechar").focus();
  }

  window.abrirDoacaoPix = abrirDoacaoPix;
  window.montarPixCopiaECola = montarPixCopiaECola;
})();
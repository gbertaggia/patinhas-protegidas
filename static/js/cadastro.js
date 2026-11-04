const rotulosDoNome = {
  PROTETOR: 'Seu nome completo',
  ONG: 'Nome da ONG',
};

const rotulosMissao = {
  PROTETOR: 'Sobre você e seus resgates',
  ONG: 'Missão da ONG',
};

const placeholdersMissao = {
  PROTETOR: 'Conte um pouco sobre como você resgata e cuida dos animais...',
  ONG: 'Conte brevemente o propósito, histórico e missão da organização...',
};

const rotulosLogo = {
  PROTETOR: 'Sua Foto de Perfil (URL)',
  ONG: 'Logo da ONG (URL)',
};

function atualizarTextosFormulario() {
  const radioSelecionado = document.querySelector('input[name="tipo"]:checked');
  if (!radioSelecionado) return;

  const tipo = radioSelecionado.value;

  // Atualiza nome
  const rotuloNome = document.querySelector('label[for="nome"]');
  if (rotuloNome) {
    rotuloNome.textContent = rotulosDoNome[tipo] || 'Nome';
  }

  // Atualiza missão/sobre
  const rotuloMissao = document.getElementById('label-missao');
  const inputMissao = document.getElementById('missao');
  if (rotuloMissao && inputMissao) {
    rotuloMissao.textContent = rotulosMissao[tipo];
    inputMissao.placeholder = placeholdersMissao[tipo];
  }

  // Atualiza foto/logo
  const rotuloLogo = document.getElementById('label-logo');
  if (rotuloLogo) {
    rotuloLogo.textContent = rotulosLogo[tipo];
  }
}

document.querySelectorAll('input[name="tipo"]').forEach((opcao) => {
  opcao.addEventListener('change', atualizarTextosFormulario);
});

// Executa uma vez ao carregar
atualizarTextosFormulario();
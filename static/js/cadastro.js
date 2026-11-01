// Ajusta o texto do campo de nome conforme o perfil escolhido (protetor ou ONG).
const rotulosDoNome = {
  PROTETOR: 'Seu nome completo',
  ONG: 'Nome da ONG',
};

function atualizarRotuloDoNome() {
  const escolhido = document.querySelector('input[name="tipo"]:checked');
  const rotulo = document.querySelector('label[for="nome"]');
  rotulo.textContent = escolhido ? rotulosDoNome[escolhido.value] : 'Nome';
}

document.querySelectorAll('input[name="tipo"]').forEach((opcao) => {
  opcao.addEventListener('change', atualizarRotuloDoNome);
});

atualizarRotuloDoNome();
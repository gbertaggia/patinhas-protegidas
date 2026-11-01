'use strict';

// Na página do animal, o painel tem data-animal-id; na página geral, não.
const raiz = document.querySelector('[data-animal-id]');
const ANIMAL_ID = raiz ? raiz.dataset.animalId : null;

function montarUrl(caminho, parametros = {}) {
  const consulta = new URLSearchParams(parametros);
  if (ANIMAL_ID) {
    consulta.set('animal_id', ANIMAL_ID);
  }
  const texto = consulta.toString();
  return texto ? `${caminho}?${texto}` : caminho;
}

function formatarMoeda(texto) {
  return Number(texto).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarData(iso) {
  const [ano, mes, dia] = iso.split('-');
  return `${dia}/${mes}/${ano}`;
}

function dataDeHoje() {
  // 'en-CA' devolve AAAA-MM-DD, o formato que o campo de data e a API usam
  return new Date().toLocaleDateString('en-CA');
}

// Chama a API e devolve o JSON. Se a sessão expirou (401), volta para o login.
async function buscarJson(url) {
  const resposta = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if (resposta.status === 401) {
    window.location.href = '/login';
    throw new Error('Sessão expirada. Entre novamente.');
  }
  const dados = await resposta.json();
  if (!resposta.ok) {
    throw new Error(dados.erro || 'Não foi possível carregar os dados.');
  }
  return dados;
}

async function carregarCategorias() {
  const categorias = await buscarJson('/api/categorias');
  const select = document.getElementById('categoria_id');
  const grupos = { DESPESA: 'Despesas', RECEITA: 'Receitas' };

  for (const [tipo, rotulo] of Object.entries(grupos)) {
    const grupo = document.createElement('optgroup');
    grupo.label = rotulo;
    for (const categoria of categorias.filter((c) => c.tipo === tipo)) {
      const opcao = document.createElement('option');
      opcao.value = categoria.id;
      opcao.textContent = categoria.nome;
      grupo.appendChild(opcao);
    }
    select.appendChild(grupo);
  }
}

async function carregarResumo() {
  const resumo = await buscarJson(montarUrl('/api/financas/resumo'));
  document.getElementById('total-receitas').textContent = formatarMoeda(resumo.receitas);
  document.getElementById('total-despesas').textContent = formatarMoeda(resumo.despesas);

  const saldo = document.getElementById('total-saldo');
  saldo.textContent = formatarMoeda(resumo.saldo);
  saldo.classList.remove('text-danger', 'text-success');
  saldo.classList.add(Number(resumo.saldo) < 0 ? 'text-danger' : 'text-success');
}

async function carregarLancamentos() {
  const lancamentos = await buscarJson(montarUrl('/api/financas/transacoes', { limite: 20 }));
  const corpo = document.getElementById('lancamentos');
  corpo.replaceChildren();
  document.getElementById('sem-lancamentos').hidden = lancamentos.length > 0;

  for (const item of lancamentos) {
    const ehDespesa = item.tipo === 'DESPESA';
    const celulas = [formatarData(item.data_transacao), item.categoria];
    if (!ANIMAL_ID) {
      celulas.push(item.animal || 'Geral');
    }
    celulas.push(item.descricao || '', (ehDespesa ? '− ' : '+ ') + formatarMoeda(item.valor));
    const ultima = celulas.length - 1;

    const linha = document.createElement('tr');
    celulas.forEach((texto, posicao) => {
      const celula = document.createElement('td');
      celula.textContent = texto;
        if (posicao === 0) {
        celula.className = 'text-nowrap';
        } else if (posicao === ultima) {
        celula.className = 'text-end text-nowrap ' + (ehDespesa ? 'text-danger' : 'text-success');
        }
      linha.appendChild(celula);
    });
    corpo.appendChild(linha);
  }
}

function mostrarMensagem(texto, tipo) {
  const area = document.getElementById('mensagem-formulario');
  area.textContent = texto;
  area.className = `alert alert-${tipo} mt-3 mb-0`;
  area.hidden = false;
}

async function enviarLancamento(evento) {
  evento.preventDefault();
  const formulario = evento.currentTarget;
  const botao = formulario.querySelector('button[type="submit"]');
  document.getElementById('mensagem-formulario').hidden = true;

  const dados = {
    categoria_id: formulario.elements['categoria_id'].value,
    valor: formulario.elements['valor'].value,
    data_transacao: formulario.elements['data_transacao'].value,
    animal_id: formulario.elements['animal_id'].value,
    descricao: formulario.elements['descricao'].value,
  };

  botao.disabled = true;
  try {
    const resposta = await fetch('/api/financas/transacoes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    if (resposta.status === 401) {
      window.location.href = '/login';
      return;
    }
    const resultado = await resposta.json();
    if (!resposta.ok) {
      throw new Error(resultado.erro || 'Não foi possível registrar o lançamento.');
    }

    formulario.reset();
    formulario.elements['data_transacao'].value = dataDeHoje();
    mostrarMensagem('Lançamento registrado.', 'success');
    await Promise.all([carregarResumo(), carregarLancamentos()]);
  } catch (erro) {
    mostrarMensagem(erro.message, 'danger');
  } finally {
    botao.disabled = false;
  }
}

async function iniciar() {
  const aviso = document.getElementById('aviso-erro');
  const formulario = document.getElementById('form-lancamento');
  formulario.elements['data_transacao'].value = dataDeHoje();
  formulario.addEventListener('submit', enviarLancamento);

  try {
    await Promise.all([carregarCategorias(), carregarResumo(), carregarLancamentos()]);
  } catch (erro) {
    aviso.textContent = erro.message;
    aviso.hidden = false;
  }
}

document.addEventListener('DOMContentLoaded', iniciar);
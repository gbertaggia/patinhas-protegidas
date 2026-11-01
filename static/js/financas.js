'use strict';

function formatarMoeda(texto) {
  return Number(texto).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarData(iso) {
  const [ano, mes, dia] = iso.split('-');
  return `${dia}/${mes}/${ano}`;
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

async function carregarResumo() {
  const resumo = await buscarJson('/api/financas/resumo');
  document.getElementById('total-receitas').textContent = formatarMoeda(resumo.receitas);
  document.getElementById('total-despesas').textContent = formatarMoeda(resumo.despesas);

  const saldo = document.getElementById('total-saldo');
  saldo.textContent = formatarMoeda(resumo.saldo);
  saldo.className = 'h4 mb-0 ' + (Number(resumo.saldo) < 0 ? 'text-danger' : 'text-success');
}

async function carregarLancamentos() {
  const lancamentos = await buscarJson('/api/financas/transacoes?limite=20');
  const corpo = document.getElementById('lancamentos');
  corpo.replaceChildren();
  document.getElementById('sem-lancamentos').hidden = lancamentos.length > 0;

  for (const item of lancamentos) {
    const ehDespesa = item.tipo === 'DESPESA';
    const celulas = [
      formatarData(item.data_transacao),
      item.categoria,
      item.animal || 'Geral',
      item.descricao || '',
      (ehDespesa ? '− ' : '+ ') + formatarMoeda(item.valor),
    ];

    const linha = document.createElement('tr');
    celulas.forEach((texto, posicao) => {
      const celula = document.createElement('td');
      celula.textContent = texto;
      if (posicao === 4) {
        celula.className = 'text-end ' + (ehDespesa ? 'text-danger' : 'text-success');
      }
      linha.appendChild(celula);
    });
    corpo.appendChild(linha);
  }
}

async function iniciar() {
  const aviso = document.getElementById('aviso-erro');
  try {
    await Promise.all([carregarResumo(), carregarLancamentos()]);
  } catch (erro) {
    aviso.textContent = erro.message;
    aviso.hidden = false;
  }
}

document.addEventListener('DOMContentLoaded', iniciar);
// Teste de navegacao na WebView da Harumi: percurso simulado (assets/debug, gerado por make_trip.py) do inicio ao destino.
// Uso: node cdp-eval.js -e "var NAV_MODE='';$(cat nav-test.js)"   (NAV_MODE='desvio' usa o percurso com saida da rota)
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const t0 = Date.now(), at = () => Math.round((Date.now() - t0) / 1000);
  const falas = [], rotas = [], hud = [];
  const send = window.harumiSend;
  window.harumiSend = (a, m) => { if (a === 'nav.say') falas.push(at() + 's ' + m); return send(a, m); };
  const fetch0 = window.fetch;
  window.fetch = (u, o) => { if (String(u).indexOf('map-api/route') === 0) rotas.push(at() + 's'); return fetch0(u, o); };
  const $ = id => document.getElementById(id);
  try {
    window.harumiRoadMap.navigatePoint('Destino de teste', -23.3040, -51.1561);
    await sleep(1500);
    HarumiNative.dispatch('nav.replay', typeof NAV_MODE === 'string' ? NAV_MODE : '');
    let last = '';
    while (Date.now() - t0 < 400000) {
      await sleep(1000);
      const s = [$('nav-arrow').textContent, $('nav-dist').textContent, $('nav-street').textContent, $('nav-rem').textContent, $('nav-speed').textContent + ' km/h'].join(' | ');
      if (s !== last) { hud.push(at() + 's ' + s); last = s; }
      if ($('nav-dist').textContent === 'Chegou' || $('nav-hud').hidden) break;
      if (falas.length && falas[falas.length - 1].endsWith('arrive')) break;
    }
    return { modo: NAV_MODE || 'direto', duracao_s: at(), chegou: falas.some(f => f.endsWith('arrive')), pedidos_de_rota: rotas, falas, mensagem: $('nav-msg').hidden ? '' : $('nav-msg-text').textContent, painel: hud.slice(0, 60) };
  } finally { window.harumiSend = send; window.fetch = fetch0; }
})()

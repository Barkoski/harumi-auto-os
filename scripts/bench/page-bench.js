// Benchmark executado dentro da WebView da Harumi (via DevTools). Mede pela interface, como o usuario ve.
// Uso: node cdp-eval.js "$(cat page-bench.js)" -> devolve JSON.
(async () => {
  const conv = document.getElementById('conversation'), st = document.getElementById('assistant-status');
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const status = () => st.textContent.replace(/ · \d+ s$/, '');
  const idle = () => /^Pronta/.test(status()) || /parcial/.test(status());
  async function waitIdle(limit) { const t0 = Date.now(); while (Date.now() - t0 < limit) { if (idle()) return true; await sleep(100); } return false; }
  async function ask(q, limit) {
    await waitIdle(30000);
    const n0 = conv.children.length, t0 = Date.now(); let first = null, speakStart = null, done = null, text = '';
    HarumiNative.dispatch('assistant.ask', q);
    while (Date.now() - t0 < limit) {
      await sleep(100);
      const kids = [...conv.children].slice(n0);
      const last = kids.length >= 2 ? kids[kids.length - 1].innerText.replace(/^Harumi\s*/, '').trim() : '';
      if (first === null && last.length > 0) first = Date.now() - t0;
      if (speakStart === null && /^Harumi falando/.test(status())) speakStart = Date.now() - t0;
      if (first !== null && idle()) { done = Date.now() - t0; text = last; break; }
    }
    return { pergunta: q, primeira_palavra_ms: first, voz_comeca_ms: speakStart, fim_ms: done, caracteres: text.length, status_final: status(), resposta: text.slice(0, 160) };
  }
  const out = { quando: new Date().toISOString(), comandos_locais: [], ia: [], outros: {} };
  document.getElementById('talk').click(); await sleep(500);
  for (const q of ['Abra o Spotify', 'Como está o carro?', 'Por favor, tudo bem?']) out.comandos_locais.push(await ask(q, 30000));
  for (const q of ['Qual a capital do Paraná?', 'Me dê uma dica para economizar combustível.', 'Explique em poucas palavras o que é um motor boxer.', 'Quanto é 15 vezes 12?', 'Obrigado, Harumi.'])
    out.ia.push(await ask(q, 300000));
  // "Oi Harumi" simulado: do disparo ate comecar a ouvir
  await waitIdle(30000); let t0 = Date.now(), wakeSpeak = null, wakeListen = null;
  HarumiNative.dispatch('wake.test', 'oi a rumi');
  while (Date.now() - t0 < 30000) { await sleep(50); if (wakeSpeak === null && /^Harumi falando/.test(status())) wakeSpeak = Date.now() - t0; if (/^Ouvindo/.test(status())) { wakeListen = Date.now() - t0; break; } }
  out.outros.oi_harumi = { voz_comeca_ms: wakeSpeak, ouvindo_ms: wakeListen };
  HarumiNative.dispatch('assistant.cancel.quiet', ''); await sleep(1500);
  // Paineis
  document.getElementById('close-assistant').click(); await sleep(300);
  t0 = performance.now(); window.harumiRoadMap.open(false); await sleep(0);
  while (!document.querySelector('#road-map-panel .leaflet-tile-loaded, .leaflet-tile-loaded') && performance.now() - t0 < 20000) await sleep(50);
  out.outros.mapa_abre_com_tiles_ms = Math.round(performance.now() - t0);
  window.harumiRoadMap.close(); await sleep(300);
  t0 = performance.now(); document.getElementById('open-atlas').click();
  while (!document.querySelector('#atlas-photo img, .atlas-photo img, img[id*=atlas]')?.complete && performance.now() - t0 < 10000) await sleep(30);
  out.outros.atlas_abre_ms = Math.round(performance.now() - t0);
  if (window.harumiAtlas) window.harumiAtlas.close(false); await sleep(300);
  t0 = performance.now(); document.getElementById('open-apps').click();
  while (document.querySelectorAll('#apps-grid .app-card').length === 0 && performance.now() - t0 < 10000) await sleep(20);
  out.outros.painel_apps_ms = Math.round(performance.now() - t0);
  window.harumiApps.close();
  // Navegacao propria: busca de endereco e rota com manobras (rede real, via gateway da Harumi). 3 rodadas cada.
  async function timed(url) { const t = performance.now(); try { const r = await fetch(url); const body = await r.text(); return { ms: Math.round(performance.now() - t), status: r.status, bytes: body.length, body: body }; } catch (e) { return { ms: Math.round(performance.now() - t), erro: String(e) }; } }
  out.navegacao = { busca_endereco: [], rota_com_manobras: [] };
  const queries = ['Avenida Higienópolis, Londrina', 'Catedral de Londrina', 'Aeroporto de Londrina'];
  for (const q of queries) { const r = await timed('map-api/geocode?q=' + encodeURIComponent(q) + '&lat=-23.31&lon=-51.16'); let n = null; try { n = JSON.parse(r.body).length; } catch (e) { } out.navegacao.busca_endereco.push({ q: q, ms: r.ms, status: r.status, resultados: n }); await sleep(1200); }
  const pts = ['-51.1630,-23.3105,-51.1561,-23.3040', '-51.1630,-23.3105,-51.1300,-23.3290', '-51.1630,-23.3105,-51.4600,-23.4200'];
  for (const p of pts) { const r = await timed('map-api/route?points=' + p + '&bearing=90'); let info = null; try { const j = JSON.parse(r.body); const rt = j.routes[0]; info = { km: Math.round(rt.distance / 100) / 10, min: Math.round(rt.duration / 60), manobras: rt.legs[0].steps.length }; } catch (e) { } out.navegacao.rota_com_manobras.push(Object.assign({ pontos: p, ms: r.ms, status: r.status }, info || {})); await sleep(1200); }
  // Rota repetida (deve vir do cache de 5 min)
  const again = await timed('map-api/route?points=' + pts[0] + '&bearing=90'); out.navegacao.rota_repetida_cache_ms = again.ms;
  // Abrir o painel de navegacao
  t0 = performance.now(); window.harumiRoadMap.open(false); while (!document.querySelector('.leaflet-tile-loaded') && performance.now() - t0 < 20000) await sleep(30);
  out.navegacao.painel_abre_ms = Math.round(performance.now() - t0); window.harumiRoadMap.close();
  return out;
})()

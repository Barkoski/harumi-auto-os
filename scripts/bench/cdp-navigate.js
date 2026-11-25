// Navega a WebView da Harumi via DevTools (Page.navigate); o app bloqueia navegacao iniciada pela propria pagina.
// Uso: node cdp-navigate.js <arquivo.html>   (relativo a pagina atual; porta 9222 ja encaminhada pelo adb)
const alvo = process.argv[2];
(async () => {
  const page = (await (await fetch('http://127.0.0.1:9222/json')).json()).find(p => p.type === 'page');
  const url = new URL(alvo, page.url).href;
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'Page.navigate', params: { url } }));
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id !== 1) return; console.log(d.error ? 'ERRO: ' + d.error.message : 'ok ' + url); ws.close(); };
})();

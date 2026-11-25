// Avalia um arquivo JS na WebView da Harumi (porta DevTools 9222 ja encaminhada pelo adb).
// Uso: node cdp-eval.js arquivo.js   ou   node cdp-eval.js -e "expressao"
const fs = require('fs');
const expr = process.argv[2] === '-e' ? process.argv[3] : fs.readFileSync(process.argv[2], 'utf8');
(async () => {
  const page = (await (await fetch('http://127.0.0.1:9222/json')).json()).find(p => p.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: { expression: expr, awaitPromise: true, returnByValue: true } }));
  ws.onmessage = m => {
    const d = JSON.parse(m.data); if (d.id !== 1) return;
    const r = d.result;
    console.log(r.exceptionDetails ? 'ERRO: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text) : JSON.stringify(r.result.value, null, 1));
    ws.close();
  };
})();

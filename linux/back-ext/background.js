/* Recebe o pedido do botao e avisa o servidor da Harumi (so 127.0.0.1), que fecha esta janela.
   O servidor aceita porque a origem e chrome-extension:// (pagina web nao consegue forjar). */
chrome.runtime.onMessage.addListener(function (msg) {
  if (!msg || msg.type !== 'harumi-close') return;
  fetch('http://127.0.0.1:8765/linux/close-app', { method: 'POST' })
    .catch(function () { /* servidor fora: nada a fazer */ });
});

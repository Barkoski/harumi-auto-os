/* Botao "Harumi" fixo no canto, grande o bastante para o dedo no carro. */
(function () {
  if (document.getElementById('harumi-back')) return;
  var b = document.createElement('button');
  b.id = 'harumi-back';
  b.type = 'button';
  b.textContent = '← Harumi';
  b.setAttribute('aria-label', 'Fechar e voltar para a Harumi');
  b.style.cssText = 'position:fixed;left:16px;bottom:16px;z-index:2147483647;min-width:120px;height:56px;padding:0 20px;' +
    'border:0;border-radius:28px;background:#d5a0c0;color:#2a1f2c;font:600 20px system-ui,sans-serif;' +
    'box-shadow:0 4px 16px rgba(0,0,0,.35);cursor:pointer';
  b.addEventListener('click', function () { chrome.runtime.sendMessage({ type: 'harumi-close' }); });
  (document.body || document.documentElement).appendChild(b);
})();

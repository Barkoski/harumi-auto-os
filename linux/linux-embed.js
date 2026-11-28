/* Card de app embutido (YouTube, navegador, Claude, ChatGPT) DENTRO da Harumi: card no canto ou tela cheia acima do dock.
   A moldura Electron desenha o app na area do corpo do card (window.harumiHost). O app e uma camada nativa por cima
   da pagina: quando outra tela da Harumi abre por cima, o app e "suspenso" (area zero) e volta ao fechar. */
(function () {
  'use strict';
  var TITLES = { youtube: 'YouTube', browser: 'Navegador', claude: 'Claude', chatgpt: 'ChatGPT', waze: 'Waze' };
  var card, body, title, urlForm, urlInput, modeBtn, current = null, full = false, raf = 0, suspended = false;
  /* Seguranca ("teatro" so parado): acima de LOCK_KMH o app some e o video pausa; libera abaixo de UNLOCK_KMH por UNLOCK_MS. */
  var LOCK_KMH = 8, UNLOCK_KMH = 3, UNLOCK_MS = 5000, locked = false, slowSince = 0, lockMsg;

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text) e.textContent = text; return e; }
  function btn(label, aria, fn) { var b = el('button', 'hl-embed-btn', label); b.type = 'button'; b.setAttribute('aria-label', aria); b.addEventListener('click', fn); return b; }

  function build() {
    card = el('section'); card.id = 'hl-embed'; card.className = 'card'; card.hidden = true;
    card.setAttribute('role', 'region'); card.setAttribute('aria-label', 'App dentro da Harumi');
    var bar = el('div', 'hl-embed-bar');
    title = el('span', 'hl-embed-title');
    urlForm = el('form', 'hl-embed-url'); urlForm.hidden = true;
    urlInput = el('input'); urlInput.type = 'text'; urlInput.inputMode = 'url'; urlInput.autocomplete = 'off';
    urlInput.setAttribute('aria-label', 'Endereço ou busca'); urlInput.placeholder = 'Endereço ou busca';
    urlForm.appendChild(urlInput);
    urlForm.addEventListener('submit', function (e) { e.preventDefault(); window.harumiHost.embedGo(urlInput.value); urlInput.blur(); });
    modeBtn = btn('Tela cheia', 'Alternar entre card e tela cheia', function () { setFull(!full); });
    bar.appendChild(btn('Voltar', 'Voltar página no app', function () { window.harumiHost.embedBack(); }));
    bar.appendChild(title);
    bar.appendChild(urlForm);
    bar.appendChild(btn('Teclado', 'Abrir o teclado para digitar no app', function () { if (window.harumiHost.embedFocus) window.harumiHost.embedFocus(); if (window.harumiKeyboard) window.harumiKeyboard.openForEmbed(); }));
    bar.appendChild(modeBtn);
    var close = btn('Fechar', 'Fechar o app', function () { hide(true); }); close.classList.add('close');
    bar.appendChild(close);
    body = el('div', 'hl-embed-body', 'Carregando…');
    lockMsg = el('div', 'hl-embed-lock', 'Vídeo e apps pausados com o carro em movimento. Voltam quando você parar.');
    lockMsg.setAttribute('role', 'status'); lockMsg.hidden = true; body.appendChild(lockMsg);
    card.appendChild(bar); card.appendChild(body);
    document.body.appendChild(card);
    window.addEventListener('resize', sync);
    new ResizeObserver(sync).observe(card);
    // so esconde se o aviso for do app que esta aberto agora (um "fechado" atrasado nao derruba o app novo)
    window.harumiHost.onEmbedClosed(function (id) {
      if (id && ownClose[id]) { ownClose[id]--; return; }   // eco de um fechamento pedido pela propria tela
      if (!id || id === current) hide(false);
    });
    if (window.harumiHost.onEmbedUrl) window.harumiHost.onEmbedUrl(function (url) { if (document.activeElement !== urlInput) urlInput.value = url; });
  }

  function zero() { return { x: 0, y: 0, width: 0, height: 0 }; }
  function rect() { if (suspended || locked) return zero(); var r = body.getBoundingClientRect(); return { x: r.left, y: r.top, width: r.width, height: r.height }; }
  function sync() { if (!current) return; cancelAnimationFrame(raf); raf = requestAnimationFrame(function () { window.harumiHost.embedBounds(rect()); }); }
  function setFull(on) { full = on; card.className = on ? 'full' : 'card'; modeBtn.textContent = on ? 'Card' : 'Tela cheia'; sync(); }

  function show(id) {
    if (!card) build();
    current = id; title.textContent = TITLES[id] || id; card.hidden = false;
    var isBrowser = id === 'browser';
    urlForm.hidden = !isBrowser; title.hidden = isBrowser; urlInput.value = '';
    if (isBrowser && !full) setFull(true);
    requestAnimationFrame(function () { window.harumiHost.embedOpen(id, rect()); });
  }
  var ownClose = {};
  function hide(tellHost) {
    if (!card) return;
    if (tellHost && current) ownClose[current] = (ownClose[current] || 0) + 1;
    current = null; card.hidden = true; if (tellHost) window.harumiHost.embedClose();
  }
  function setLocked(on) {
    if (locked === on) return;
    locked = on;
    if (lockMsg) lockMsg.hidden = !on;
    if (on && current && window.harumiHost.embedPause) window.harumiHost.embedPause();
    sync();
  }
  function moving(kmh) {
    if (!Number.isFinite(kmh)) return;
    // Waze e navegacao: precisa funcionar andando (so video e outros apps travam)
    if (current === 'waze') { slowSince = 0; if (locked) setLocked(false); return; }
    if (kmh > LOCK_KMH) { slowSince = 0; setLocked(true); return; }
    if (kmh < UNLOCK_KMH) { if (!slowSince) slowSince = Date.now(); if (Date.now() - slowSince >= UNLOCK_MS) setLocked(false); }
    else slowSince = 0;
  }
  function suspend(on) { if (suspended === !!on) return; suspended = !!on; if (card) card.classList.toggle('suspended', suspended); sync(); }

  window.harumiEmbed = {
    open: show, close: function () { hide(true); }, suspend: suspend, moving: moving,
    isLocked: function () { return locked; },
    isOpen: function () { return !!current; }, current: function () { return current; }
  };
  window.addEventListener('keydown', function (e) { if (e.key === 'Escape' && current) hide(true); });
})();

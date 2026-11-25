/* Teclado na tela da Harumi OS (pt-BR), para a tela touch sem teclado fisico.
   Abre ao tocar num campo de texto da Harumi; no app embutido (YouTube, navegador...) abre pelo botao "Teclado" do card
   e digita no app pela moldura (window.harumiHost.embedType/embedKey). Layout inspirado no kit
   "Tesla Dashboard UI Component Library" de Nami (CC BY 4.0), com a identidade da Harumi. */
(function () {
  'use strict';
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  var ROWS = {
    abc: [['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'], ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ç'], ['⇧', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '⌫'], ['?123', 'acento', ' ', '.', 'OK']],
    num: [['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'], ['-', '/', ':', ';', '(', ')', '$', '&', '@', '"'], ['#', '%', '+', '=', '*', ',', '?', '!', '⌫'], ['ABC', "'", ' ', '.', 'OK']],
    ace: [['á', 'à', 'â', 'ã', 'é', 'ê', 'í', 'ó', 'ô', 'õ'], ['ú', 'ü', 'ç', 'ñ', '°', 'º', 'ª', '€', '£', '¿'], ['⇧', '·', '«', '»', '–', '—', '…', '¡', '⌫'], ['ABC', '?123', ' ', '.', 'OK']]
  };
  var kb, keysBox, mode = 'abc', shift = false, target = null, embedMode = false;
  // Campos sem <form>: o OK aciona o botao de enviar da propria tela.
  var SUBMIT = { question: 'send-question' };

  function build() {
    kb = el('section'); kb.id = 'hl-kb'; kb.hidden = true; kb.setAttribute('aria-label', 'Teclado na tela');
    var bar = el('div', 'hl-kb-bar');
    var where = el('span', 'hl-kb-where', 'Teclado'); bar.appendChild(where);
    var hide = el('button', 'hl-kb-hide', 'Fechar teclado'); hide.type = 'button';
    hide.addEventListener('pointerdown', function (e) { e.preventDefault(); close(); });
    bar.appendChild(hide);
    keysBox = el('div', 'hl-kb-keys');
    kb.appendChild(bar); kb.appendChild(keysBox);
    document.body.appendChild(kb);
    kb.__where = where;
    render();
  }
  function label(k) {
    if (k === ' ') return 'espaço';
    if (k === 'acento') return 'á é ã';
    return shift && k.length === 1 ? k.toUpperCase() : k;
  }
  function render() {
    keysBox.textContent = '';
    ROWS[mode].forEach(function (row) {
      var r = el('div', 'hl-kb-row');
      row.forEach(function (k) {
        var b = el('button', 'hl-kb-key', label(k)); b.type = 'button';
        if (k === ' ') b.classList.add('space');
        if (k.length > 1 || k === '⇧' || k === '⌫') b.classList.add('fn');
        if (k === 'OK') b.classList.add('ok');
        if (k === '⇧' && shift) b.setAttribute('aria-pressed', 'true');
        b.setAttribute('aria-label', k === '⌫' ? 'Apagar' : k === '⇧' ? 'Maiúsculas' : k === 'OK' ? 'Confirmar' : label(k));
        // pointerdown + preventDefault: o campo nao perde o foco ao tocar na tecla
        b.addEventListener('pointerdown', function (e) { e.preventDefault(); press(k); });
        r.appendChild(b);
      });
      keysBox.appendChild(r);
    });
  }
  function press(k) {
    if (k === '⇧') { shift = !shift; render(); return; }
    if (k === '?123') { mode = 'num'; render(); return; }
    if (k === 'ABC') { mode = 'abc'; render(); return; }
    if (k === 'acento') { mode = 'ace'; render(); return; }
    if (k === '⌫') { key('Backspace'); return; }
    if (k === 'OK') { key('Enter'); return; }
    var ch = shift ? k.toUpperCase() : k;
    type(ch);
    if (shift) { shift = false; render(); }
  }
  function type(text) {
    if (embedMode) { if (window.harumiHost && window.harumiHost.embedType) window.harumiHost.embedType(text); return; }
    if (!target) return;
    var s = target.selectionStart != null ? target.selectionStart : target.value.length;
    var e = target.selectionEnd != null ? target.selectionEnd : s;
    target.setRangeText(text, s, e, 'end');
    target.dispatchEvent(new Event('input', { bubbles: true }));
  }
  function key(name) {
    if (embedMode) { if (window.harumiHost && window.harumiHost.embedKey) window.harumiHost.embedKey(name); return; }
    if (!target) return;
    if (name === 'Backspace') {
      var s = target.selectionStart, e = target.selectionEnd;
      if (s == null) { target.value = target.value.slice(0, -1); }
      else if (s !== e) target.setRangeText('', s, e, 'end');
      else if (s > 0) target.setRangeText('', s - 1, s, 'end');
      target.dispatchEvent(new Event('input', { bubbles: true }));
      return;
    }
    if (name === 'Enter') {
      var ev = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true });
      var handled = !target.dispatchEvent(ev);
      target.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
      if (!handled && target.form) { if (target.form.requestSubmit) target.form.requestSubmit(); else target.form.submit(); }
      else if (!handled && SUBMIT[target.id]) { var sb = document.getElementById(SUBMIT[target.id]); if (sb && !sb.disabled) sb.click(); }
      close();
    }
  }
  function placeholderOf(t) { return (t && (t.getAttribute('aria-label') || t.placeholder)) || 'Teclado'; }
  function open(t, forEmbed) {
    if (!kb) build();
    embedMode = !!forEmbed; target = forEmbed ? null : t; mode = 'abc'; shift = false; render();
    kb.__where.textContent = forEmbed ? 'Digitando no app' : placeholderOf(t);
    kb.hidden = false; document.body.classList.add('hl-kb-open');
    window.dispatchEvent(new Event('resize'));
  }
  function close() {
    if (!kb || kb.hidden) return;
    kb.hidden = true; document.body.classList.remove('hl-kb-open'); target = null; embedMode = false;
    window.dispatchEvent(new Event('resize'));
  }
  function isText(t) {
    if (!t || t.disabled || t.readOnly) return false;
    if (t.tagName === 'TEXTAREA') return true;
    return t.tagName === 'INPUT' && /^(text|search|url|email|tel|number|)$/i.test(t.type || '');
  }
  document.addEventListener('focusin', function (e) { if (isText(e.target)) open(e.target, false); });
  // Tocar de novo num campo que ja tem o foco (ex.: depois de "Fechar teclado") tambem reabre o teclado.
  document.addEventListener('pointerup', function (e) { if (isText(e.target) && (!kb || kb.hidden || target !== e.target)) open(e.target, false); });
  document.addEventListener('focusout', function (e) {
    if (embedMode || e.target !== target) return;
    setTimeout(function () { if (!isText(document.activeElement)) close(); }, 150);
  });
  window.harumiKeyboard = { open: open, openForEmbed: function () { open(null, true); }, close: close, isOpen: function () { return !!kb && !kb.hidden; } };
})();

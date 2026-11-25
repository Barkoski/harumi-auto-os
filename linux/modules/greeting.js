/* Saudacao ao ligar: jingle japones + "Irasshaimase! Seja bem-vindo!" + "Pra onde a gente vai hoje?".
   O servidor (plugins/greeting.py) decide quando: uma vez por partida, ou quando o sensor da porta pedir. */
(function () {
  'use strict';
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function post(path, body) { return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }).then(function (r) { return r.json(); }); }
  var box = null, timer = 0, playing = [];

  function stopAudio() { playing.forEach(function (a) { try { a.pause(); } catch (e) { /* ja parou */ } }); playing = []; }
  function close() { if (!box) return; box.hidden = true; clearTimeout(timer); stopAudio(); }
  function play(src) {
    var a = new Audio(src); playing.push(a);
    return new Promise(function (ok) { a.addEventListener('ended', ok); a.addEventListener('error', ok); a.play().catch(ok); });
  }
  function show(t, voz) {
    if (!box) {
      box = el('section', 'hl-greet'); box.id = 'hl-greet'; box.setAttribute('role', 'dialog'); box.setAttribute('aria-label', 'Boas-vindas');
      document.body.appendChild(box);
    }
    box.textContent = '';
    // cada frase japonesa num bloco inteiro: a quebra so acontece entre frases (o japones nao tem espacos)
    var ja = el('p', 'hl-greet-ja');
    (t.ja.match(/[^！。]+[！。]?/g) || [t.ja]).forEach(function (f) { ja.appendChild(el('span', '', f)); });
    box.appendChild(ja);
    box.appendChild(el('p', 'hl-greet-romaji', t.romaji));
    box.appendChild(el('h2', 'hl-greet-pt', t.pt));
    box.appendChild(el('p', 'hl-greet-q', t.pergunta));
    var row = el('div', 'hl-greet-actions');
    var nav = el('button', 'hl-greet-btn primary', 'Escolher destino'); nav.type = 'button';
    nav.addEventListener('click', function () {
      close();
      var b = document.querySelector('.hl-navcard-search') || document.getElementById('nav-dest');
      if (b) { b.focus(); if (b.click) b.click(); }
    });
    var talk = el('button', 'hl-greet-btn', 'Falar com a Harumi'); talk.type = 'button';
    talk.addEventListener('click', function () { close(); var d = document.querySelector('#hl-dock [data-dock=harumi]'); if (d) d.click(); });
    var later = el('button', 'hl-greet-btn', 'Agora não'); later.type = 'button'; later.addEventListener('click', close);
    row.appendChild(nav); row.appendChild(talk); row.appendChild(later); box.appendChild(row);
    box.hidden = false; nav.focus();
    clearTimeout(timer); timer = setTimeout(close, 25000);
    play('/linux/greeting-jingle').then(function () { if (voz && !box.hidden) return play('/linux/greeting-voice'); });
  }
  function check() {
    fetch('/linux/greeting').then(function (r) { return r.json(); }).then(function (j) {
      if (!j.ok || !j.due) return;
      post('/linux/greeting-done');
      show(j.texto, j.voz);
    }).catch(function () {});
  }
  function settings() {
    if (!window.harumiLinux || !window.harumiLinux.addSettingsSection) return;
    var wrap = el('div', 'hl-greet-settings');
    var test = el('button', 'hl-greet-btn', 'Tocar saudação agora'); test.type = 'button';
    test.addEventListener('click', function () { post('/linux/greeting-test').then(check); });
    var tog = el('button', 'hl-greet-btn'); tog.type = 'button'; tog.setAttribute('role', 'switch');
    function paint(off) { tog.textContent = off ? 'Saudação ao ligar: desligada' : 'Saudação ao ligar: ligada'; tog.setAttribute('aria-checked', off ? 'false' : 'true'); }
    fetch('/linux/greeting').then(function (r) { return r.json(); }).then(function (j) { paint(j.off); });
    tog.addEventListener('click', function () {
      var off = tog.getAttribute('aria-checked') === 'true';
      post('/linux/greeting-test', { off: off }).then(function (j) { paint(j.off); });
    });
    var note = el('p', 'hl-greet-note', 'Toca o jingle e a boas-vindas uma vez cada vez que a Harumi liga com o carro. A voz em japonês aparece quando um sintetizador de voz for instalado.');
    wrap.appendChild(test); wrap.appendChild(tog); wrap.appendChild(note);
    window.harumiLinux.addSettingsSection('Saudação', wrap);
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  function start() { settings(); setTimeout(check, 2500); setInterval(check, 5000); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

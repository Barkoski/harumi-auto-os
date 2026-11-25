/* Tela dividida: o mapa (navegacao) fica sempre na area principal e a coluna da direita tem espacos que o motorista
   escolhe: Musica, Carro, App (YouTube, Waze, navegador, Claude, ChatGPT), Relogio, Atalhos ou Harumi.
   Layouts: "dividida" (2 espacos), "dividida1" (1 espaco grande), "painel" (painel lateral, sem divisao) e "mapa".
   A escolha fica salva neste aparelho (localStorage). Padrao: dividida com Musica + Carro. */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg', KEY = 'hl.split.v1';
  var WIDGETS = [
    ['musica', 'Música'], ['carro', 'Carro'], ['app', 'App'], ['relogio', 'Relógio'], ['atalhos', 'Atalhos'], ['harumi', 'Harumi']
  ];
  var APPS = [['youtube', 'YouTube'], ['waze', 'Waze'], ['browser', 'Navegador'], ['claude', 'Claude'], ['chatgpt', 'ChatGPT']];
  var LAYOUTS = [['dividida', 'Mapa + 2 telas'], ['dividida1', 'Mapa + 1 tela'], ['painel', 'Painel lateral'], ['mapa', 'Só o mapa']];
  var DEFAULT = { layout: 'dividida', slots: ['musica', 'carro'], app: 'youtube', focus: null };
  // telas que abrem em tela cheia propria (o App usa a tela cheia do proprio app; o Carro abre o painel do carro)
  var FOCUSABLE = ['musica', 'relogio', 'atalhos', 'harumi'];

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function icon(id) {
    var s = document.createElementNS(NS, 'svg'), u = document.createElementNS(NS, 'use');
    s.setAttribute('class', 'ck-ico'); s.setAttribute('aria-hidden', 'true'); s.setAttribute('focusable', 'false');
    u.setAttribute('href', '#' + id); s.appendChild(u); return s;
  }
  function button(cls, text, aria, fn) {
    var b = el('button', cls, text); b.type = 'button'; if (aria) b.setAttribute('aria-label', aria);
    b.addEventListener('click', fn); return b;
  }
  function load() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (c && LAYOUTS.some(function (l) { return l[0] === c.layout; }) && Array.isArray(c.slots)) {
        return { layout: c.layout, slots: [valid(c.slots[0], 'musica'), valid(c.slots[1], 'carro')], app: validApp(c.app),
                 focus: FOCUSABLE.indexOf(c.focus) >= 0 ? c.focus : null };
      }
    } catch (e) { /* sem armazenamento: usa o padrao */ }
    return JSON.parse(JSON.stringify(DEFAULT));
  }
  function valid(w, d) { return WIDGETS.some(function (x) { return x[0] === w; }) ? w : d; }
  function validApp(a) { return APPS.some(function (x) { return x[0] === a; }) ? a : 'youtube'; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(cfg)); } catch (e) { /* ignora */ } }

  var cfg = load(), col, slotEls = [], menu, focusEl = null, focusSlot = null, appSlot = null, slotOpening = false, ticker = 0;
  var spot = null, veh = null, speed = null, fixAt = 0;
  var SPLIT_MQ = window.matchMedia('(min-width:900px)');

  /* ---------------- Widgets ---------------- */
  var W = {
    musica: function (box) {
      var art = el('div', 'hl-w-art'); art.appendChild(icon('ck-music'));
      var img = el('img'); img.alt = ''; img.hidden = true; art.appendChild(img);
      var meta = el('div', 'hl-w-meta');
      var kick = el('span', 'hl-w-kick', 'Música'), ttl = el('strong', 'hl-w-title', 'Nada tocando'), sub = el('span', 'hl-w-sub', '');
      meta.appendChild(kick); meta.appendChild(ttl); meta.appendChild(sub);
      var bar = el('div', 'hl-w-progress'); var fill = el('span'); bar.appendChild(fill);
      var btns = el('div', 'hl-w-media');
      [['ck-prev', 'Anterior', 0], ['ck-play', 'Tocar ou pausar', 1], ['ck-next', 'Próxima', 2]].forEach(function (b) {
        var x = button('hl-w-mbtn', null, b[1], function () {
          var real = document.querySelectorAll('#hl-mini .hl-mini-btn')[b[2]]; if (real) real.click();
        });
        x.appendChild(icon(b[0])); btns.appendChild(x);
      });
      var top = el('div', 'hl-w-music-top'); top.appendChild(art); top.appendChild(meta);
      box.appendChild(top); box.appendChild(bar); box.appendChild(btns);
      var lastCover = '';
      return function () {
        var mt = document.querySelector('#hl-mini strong'), mk = document.querySelector('#hl-mini .hl-kicker');
        kick.textContent = mk ? mk.textContent : 'Música';
        var s = spot && spot.name ? spot : null;
        ttl.textContent = s ? s.name : (mt ? mt.textContent : 'Nada tocando');
        sub.textContent = s ? (s.artists || '') : '';
        var cover = s && s.cover ? s.trackId || s.cover : '';
        if (cover !== lastCover) {
          lastCover = cover; img.hidden = true;
          if (cover) { img.onload = function () { img.hidden = false; }; img.onerror = function () { img.hidden = true; }; img.src = '/linux/spotify-cover?t=' + encodeURIComponent(cover); }
        }
        var pct = 0;
        if (s && s.durationMs > 0) {
          var pos = (s.positionMs || 0) + (s.state === 'playing' && s.at ? Date.now() - s.at * 1000 : 0);
          pct = Math.max(0, Math.min(1, pos / s.durationMs));
        }
        bar.hidden = !(s && s.durationMs > 0); fill.style.width = (pct * 100).toFixed(1) + '%';
      };
    },
    carro: function (box) {
      var hero = el('div', 'hl-w-speed'); var v = el('b', '', '--'); hero.appendChild(v); hero.appendChild(el('span', '', 'km/h'));
      var src = el('span', 'hl-w-sub', 'sem GPS'); hero.appendChild(src);
      var grid = el('div', 'hl-w-kv'), cells = {};
      [['agua', 'Água'], ['rpm', 'Rotação'], ['bat', 'Bateria'], ['pneus', 'Pneus']].forEach(function (k) {
        var c = el('div', 'hl-w-cell'); c.appendChild(el('span', '', k[1])); var b = el('b', '', '—'); c.appendChild(b); grid.appendChild(c); cells[k[0]] = b;
      });
      var open = button('hl-w-link', 'Ver painel do carro', null, function () { var b = document.querySelector('.hl-dock-car'); if (b) b.click(); });
      box.appendChild(hero); box.appendChild(grid); box.appendChild(open);
      return function () {
        var ok = Date.now() - fixAt < 15000;
        v.textContent = ok && speed != null ? Math.round(speed) : '--'; v.classList.toggle('none', !(ok && speed != null));
        src.textContent = ok ? 'GPS' : 'sem GPS';
        var m = (veh && veh.motor) || {}, bat = (veh && veh.bateria) || {}, pn = (veh && veh.pneus) || {};
        cells.agua.textContent = m.aguaC != null ? m.aguaC + ' °C' : '—';
        cells.rpm.textContent = m.rpm != null ? m.rpm + '' : '—';
        cells.bat.textContent = bat.volts != null ? bat.volts.toFixed(1) + ' V' : '—';
        cells.pneus.textContent = pn.pneus ? 'ok' : '—';
      };
    },
    relogio: function (box) {
      var t = el('b', 'hl-w-clock'), d = el('span', 'hl-w-date');
      box.appendChild(t); box.appendChild(d);
      return function () {
        var now = new Date();
        t.textContent = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
        var ds = now.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
        d.textContent = ds.charAt(0).toUpperCase() + ds.slice(1); // so a primeira letra ("Segunda-feira, 16 de novembro")
      };
    },
    atalhos: function (box) {
      var g = el('div', 'hl-w-shortcuts');
      g.appendChild(button('hl-w-sc', 'Buscar destino', null, function () { var i = document.getElementById('nav-dest'); if (i) { i.focus(); i.dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); } }));
      [['casa', 'Casa'], ['trabalho', 'Trabalho']].forEach(function (f) {
        g.appendChild(button('hl-w-sc', f[1], 'Ir para ' + f[1], function () { var b = document.querySelector('.hl-fav[data-fav="' + f[0] + '"]'); if (b) b.click(); }));
      });
      g.appendChild(button('hl-w-sc', 'Postos perto', null, function () {
        var t = [].slice.call(document.querySelectorAll('.hl-tile')).filter(function (x) { return /Postos|Combust/.test(x.textContent); })[0];
        if (t) t.click(); else { var i = document.getElementById('nav-dest'); if (i) { i.value = 'posto de combustível'; i.focus(); } }
      }));
      box.appendChild(g);
      return function () {};
    },
    harumi: function (box) {
      var last = el('p', 'hl-w-last', 'Pergunte sobre o carro, a estrada ou peça uma rota.');
      var talk = button('hl-w-talk', null, 'Falar com a Harumi', function () { var d = document.querySelector('#hl-dock [data-dock=harumi]'); if (d) d.click(); });
      talk.appendChild(icon('ck-mic')); talk.appendChild(el('span', '', 'Falar com a Harumi'));
      box.appendChild(last); box.appendChild(talk);
      return function () {
        var ps = document.querySelectorAll('#conversation p'); var p = ps[ps.length - 1];
        if (p && p.innerText) last.textContent = p.innerText.replace(/^Harumi\s*/, '').slice(0, 220);
      };
    },
    app: function (box, slot) {
      var bar = el('div', 'hl-w-apps');
      APPS.forEach(function (a) {
        var b = button('hl-w-appbtn', a[1], 'Abrir ' + a[1] + ' nesta tela', function () { cfg.app = a[0]; save(); openAppIn(slot); paintApps(); });
        b.dataset.app = a[0]; bar.appendChild(b);
      });
      var area = el('div', 'hl-w-apparea'); var note = el('p', 'hl-w-sub', 'Toque num app para abrir aqui.'); area.appendChild(note);
      box.appendChild(bar); box.appendChild(area);
      slot.area = area; slot.note = note;
      function paintApps() { [].forEach.call(bar.children, function (b) { b.setAttribute('aria-pressed', b.dataset.app === cfg.app ? 'true' : 'false'); }); }
      paintApps();
      return function () {
        var cur = window.harumiEmbed && window.harumiEmbed.current && window.harumiEmbed.current();
        note.textContent = cur && appSlot === slot ? '' : 'Toque num app para abrir aqui.';
        if (appSlot === slot && cur) placeEmbed(slot);
      };
    }
  };

  /* ---------------- App dentro do espaco ---------------- */
  function embedCard() { return document.getElementById('hl-embed'); }
  function placeEmbed(slot) {
    var card = embedCard(); if (!card || !slot.area || card.classList.contains('full')) return;
    var r = slot.area.getBoundingClientRect();
    if (r.width < 50 || r.height < 50) return;
    var s = card.style, px = function (n) { return Math.round(n) + 'px'; };
    var want = [px(r.left), px(r.top), px(r.width), px(r.height)];
    if (s.left === want[0] && s.top === want[1] && s.width === want[2] && s.height === want[3]) return;
    s.left = want[0]; s.top = want[1]; s.width = want[2]; s.height = want[3]; s.right = 'auto'; s.bottom = 'auto';
    card.classList.add('hl-in-slot');
    window.dispatchEvent(new Event('resize')); // o linux-embed.js recalcula o retangulo do app
  }
  function unplaceEmbed() {
    var card = embedCard(); if (!card) return;
    ['left', 'top', 'width', 'height', 'right', 'bottom'].forEach(function (k) { card.style[k] = ''; });
    card.classList.remove('hl-in-slot');
    window.dispatchEvent(new Event('resize'));
  }
  function openAppIn(slot) {
    if (!window.harumiEmbed) return;
    appSlot = slot; slotOpening = true;
    try { window.harumiEmbed.open(cfg.app); } finally { slotOpening = false; }
    setTimeout(function () { placeEmbed(slot); }, 50);
  }
  function hookEmbed() {
    if (!window.harumiEmbed || window.harumiEmbed.__split) return;
    var orig = window.harumiEmbed.open;
    window.harumiEmbed.open = function (id) {
      if (!slotOpening) { appSlot = null; unplaceEmbed(); } // aberto pelo dock: volta ao card/tela cheia normal
      return orig.apply(this, arguments);
    };
    window.harumiEmbed.__split = true;
  }

  /* ---------------- Coluna e escolha ---------------- */
  function build() {
    col = el('aside', 'hl-split'); col.id = 'hl-split'; col.setAttribute('aria-label', 'Telas ao lado do mapa');
    document.body.appendChild(col);
    menu = el('div', 'hl-split-menu'); menu.hidden = true; menu.setAttribute('role', 'dialog'); menu.setAttribute('aria-label', 'Escolher o que mostrar');
    document.body.appendChild(menu);
    document.addEventListener('pointerdown', function (e) { if (!menu.hidden && !menu.contains(e.target) && !e.target.closest('.hl-slot-pick')) menu.hidden = true; });
  }
  function render() {
    var on = SPLIT_MQ.matches && (cfg.layout === 'dividida' || cfg.layout === 'dividida1');
    document.body.classList.toggle('hl-split-on', on);
    document.body.classList.toggle('hl-split-one', on && cfg.layout === 'dividida1');
    document.body.classList.toggle('hl-layout-mapa', SPLIT_MQ.matches && cfg.layout === 'mapa');
    document.body.classList.toggle('hl-split-music', on && cfg.slots.slice(0, cfg.layout === 'dividida1' ? 1 : 2).indexOf('musica') >= 0);
    var hadApp = appSlot;
    col.textContent = ''; slotEls = [];
    if (!on) { if (hadApp) { appSlot = null; unplaceEmbed(); } col.hidden = true; renderFocus(); return; }
    col.hidden = false;
    var n = cfg.layout === 'dividida1' ? 1 : 2, appIdx = -1;
    for (var i = 0; i < n; i++) {
      var w = cfg.slots[i];
      if (w === 'app') { if (appIdx >= 0) w = cfg.slots[i] = i === 0 ? 'musica' : 'carro'; else appIdx = i; } // so um app por vez
      var slot = { i: i, w: w };
      var box = el('section', 'hl-slot hl-slot-' + w); box.setAttribute('aria-label', label(w));
      var head = el('div', 'hl-slot-head'); head.appendChild(el('h3', '', label(w)));
      var pick = button('hl-slot-pick', 'Trocar', 'Trocar o que aparece nesta tela', (function (idx, btn) { return function (ev) { openMenu(idx, ev.currentTarget); }; })(i));
      var full = button('hl-slot-full', null, 'Abrir ' + label(w) + ' em tela cheia', (function (wid, sl) { return function () { goFull(wid, sl); }; })(w, slot));
      full.appendChild(icon('ck-fit'));
      head.appendChild(full); head.appendChild(pick); box.appendChild(head);
      var body = el('div', 'hl-slot-body'); box.appendChild(body);
      slot.update = W[w](body, slot); slot.el = box;
      col.appendChild(box); slotEls.push(slot);
    }
    var appS = slotEls[appIdx];
    if (appS) {
      var cur = window.harumiEmbed && window.harumiEmbed.current && window.harumiEmbed.current();
      appSlot = appS;
      if (cur) setTimeout(function () { placeEmbed(appS); }, 50);
    } else if (hadApp) {
      appSlot = null;
      if (window.harumiEmbed && window.harumiEmbed.current && window.harumiEmbed.current()) window.harumiEmbed.close();
      unplaceEmbed();
    }
    renderFocus();
    tick();
    window.dispatchEvent(new Event('resize')); // o mapa ajusta a largura
  }
  /* ---------------- Tela cheia focada em um app (como no CarPlay) ---------------- */
  function goFull(w, slot) {
    if (w === 'carro') { var c = document.querySelector('.hl-dock-car'); if (c) c.click(); return; }
    if (w === 'app') {
      var cur = window.harumiEmbed && window.harumiEmbed.current && window.harumiEmbed.current();
      if (!cur) openAppIn(slot);
      setTimeout(function () {
        var card = embedCard(); if (!card || card.classList.contains('full')) return;
        var b = [].slice.call(card.querySelectorAll('.hl-embed-btn')).filter(function (x) { return x.textContent === 'Tela cheia'; })[0];
        if (b) b.click();
      }, cur ? 0 : 400);
      return;
    }
    cfg.focus = w; save(); renderFocus();
  }
  function closeFull() { cfg.focus = null; save(); renderFocus(); }
  function renderFocus() {
    var on = !!cfg.focus && document.body.classList.contains('hl-split-on');
    document.body.classList.toggle('hl-focus-on', on);
    if (!focusEl) {
      focusEl = el('section', 'hl-focus'); focusEl.id = 'hl-focus'; focusEl.hidden = true;
      document.body.appendChild(focusEl);
    }
    focusEl.textContent = ''; focusSlot = null;
    if (!on) { focusEl.hidden = true; return; }
    var w = cfg.focus;
    focusEl.setAttribute('aria-label', label(w) + ' em tela cheia');
    var head = el('div', 'hl-focus-head'); head.appendChild(el('h2', '', label(w)));
    var back = button('hl-focus-back', null, 'Voltar para a tela dividida', closeFull);
    back.appendChild(icon('ck-apps')); back.appendChild(el('span', '', 'Tela dividida'));
    head.appendChild(back); focusEl.appendChild(head);
    var body = el('div', 'hl-slot-body hl-focus-body hl-slot-' + w); focusEl.appendChild(body);
    focusSlot = { w: w, update: W[w](body, {}) };
    focusEl.hidden = false; back.focus(); tick();
  }

  function label(w) { var f = WIDGETS.filter(function (x) { return x[0] === w; })[0]; return f ? f[1] : w; }
  function openMenu(idx, anchor) {
    menu.textContent = '';
    menu.appendChild(el('p', 'hl-split-menu-title', 'Mostrar nesta tela'));
    var used = cfg.slots.slice(0, cfg.layout === 'dividida1' ? 1 : 2);
    WIDGETS.forEach(function (w) {
      var b = button('hl-split-opt', w[1], null, function () {
        var other = used.indexOf(w[0]);
        if (other >= 0 && other !== idx) cfg.slots[other] = cfg.slots[idx]; // troca de lugar em vez de repetir
        cfg.slots[idx] = w[0]; save(); menu.hidden = true; render();
      });
      b.setAttribute('aria-pressed', cfg.slots[idx] === w[0] ? 'true' : 'false');
      menu.appendChild(b);
    });
    menu.appendChild(el('p', 'hl-split-menu-title', 'Layout'));
    LAYOUTS.forEach(function (l) {
      var b = button('hl-split-opt', l[1], null, function () { setLayout(l[0]); menu.hidden = true; });
      b.setAttribute('aria-pressed', cfg.layout === l[0] ? 'true' : 'false'); menu.appendChild(b);
    });
    var r = anchor.getBoundingClientRect();
    menu.hidden = false;
    var mw = menu.offsetWidth, mh = menu.offsetHeight;
    menu.style.left = Math.max(8, Math.min(window.innerWidth - mw - 8, r.right - mw)) + 'px';
    menu.style.top = Math.max(8, Math.min(window.innerHeight - mh - 8, r.bottom + 6)) + 'px';
    var first = menu.querySelector('button'); if (first) first.focus();
  }
  function setLayout(l) { cfg.layout = l; save(); render(); paintSettings(); }

  /* ---------------- Ajustes ---------------- */
  var setBtns = [];
  function settings() {
    if (!window.harumiLinux || !window.harumiLinux.addSettingsSection) return;
    var wrap = el('div', 'hl-split-settings');
    LAYOUTS.forEach(function (l) {
      var b = button('hl-split-opt', l[1], null, function () { setLayout(l[0]); }); b.dataset.layout = l[0]; setBtns.push(b); wrap.appendChild(b);
    });
    wrap.appendChild(el('p', 'hl-split-note', 'Nas telas ao lado do mapa, toque em “Trocar” para escolher: Música, Carro, App (YouTube, Waze, navegador, Claude, ChatGPT), Relógio, Atalhos ou Harumi.'));
    window.harumiLinux.addSettingsSection('Tela dividida', wrap);
    paintSettings();
  }
  function paintSettings() { setBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.layout === cfg.layout ? 'true' : 'false'); }); }

  /* ---------------- Dados e atualizacao ---------------- */
  function tick() {
    slotEls.concat(focusSlot ? [focusSlot] : []).forEach(function (s) { try { s.update(); } catch (e) { /* um widget com erro nao derruba os outros */ } });
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && cfg.focus) closeFull(); });
  function start() {
    build(); hookEmbed(); render(); settings();
    var prev = window.harumiSpotifyNow;
    window.harumiSpotifyNow = function (s) { if (prev) prev(s); spot = s || null; tick(); };
    window.addEventListener('hl-vehicle', function (e) { veh = e.detail || null; tick(); });
    window.addEventListener('hl-fix', function (e) {
      var f = e.detail || {}, v = Number.isFinite(f.speedMps) ? f.speedMps : f.speed;
      fixAt = Date.now(); if (Number.isFinite(v)) speed = v * 3.6; tick();
    });
    var card = null;
    (function watchCard(n) {
      card = embedCard(); hookEmbed();
      if (!card) { if (n < 120) setTimeout(function () { watchCard(n + 1); }, 500); return; }
      // "Tela cheia" do app: solta do espaco; "Card": volta para o espaco
      new MutationObserver(function () {
        if (card.classList.contains('full')) { if (card.classList.contains('hl-in-slot')) unplaceEmbed(); }
        else if (appSlot && !card.hidden) placeEmbed(appSlot);
      }).observe(card, { attributes: true, attributeFilter: ['class', 'hidden'] });
    })(0);
    if (SPLIT_MQ.addEventListener) SPLIT_MQ.addEventListener('change', render);
    window.addEventListener('resize', function () { if (appSlot) placeEmbed(appSlot); });
    ticker = setInterval(tick, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

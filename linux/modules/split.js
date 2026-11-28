/* Telas da Harumi: o mapa (navegacao) e as telas escolhidas pelo motorista (Musica, Carro, App, Relogio, Atalhos, Harumi).
   Layouts: "dividida" (mapa + 2 telas), "dividida1" (mapa + 1), "livre" (personalizado: arrastar e redimensionar cada
   tela numa grade), "painel" (painel lateral) e "mapa". Navegador: Harumi (padrao) ou Waze, que assume o lugar do mapa.
   Tudo fica salvo neste aparelho (localStorage). */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg', KEY = 'hl.split.v1';
  var WIDGETS = [
    ['musica', 'Música'], ['carro', 'Carro'], ['app', 'App'], ['relogio', 'Relógio'], ['atalhos', 'Atalhos'], ['harumi', 'Harumi']
  ];
  var APPS = [['youtube', 'YouTube'], ['waze', 'Waze'], ['browser', 'Navegador'], ['claude', 'Claude'], ['chatgpt', 'ChatGPT']];
  var LAYOUTS = [['dividida', 'Mapa + 2 telas'], ['dividida1', 'Mapa + 1 tela'], ['livre', 'Personalizado'], ['painel', 'Painel lateral'], ['mapa', 'Só o mapa']];
  // Grade do layout personalizado (colunas x linhas) e tamanhos minimos
  var GX = 24, GY = 12, MIN = { map: [6, 4], tile: [4, 3] };
  var FREE_DEFAULT = [
    { id: 'map', w: 'map', x: 0, y: 0, cw: 15, ch: 12 },
    { id: 't1', w: 'musica', x: 15, y: 0, cw: 9, ch: 6 },
    { id: 't2', w: 'carro', x: 15, y: 6, cw: 9, ch: 6 }
  ];
  var DEFAULT = { layout: 'dividida', slots: ['musica', 'carro'], app: 'youtube', focus: null, nav: 'harumi', free: FREE_DEFAULT };
  var FOCUSABLE = ['musica', 'relogio', 'atalhos', 'harumi'];
  var WAZE_LIVE = 'https://www.waze.com/pt-BR/live-map/'; // mesmo endereco que a moldura ja usa para o app Waze

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
  function notify(t) { var m = document.getElementById('message'); if (m) { m.textContent = t; m.hidden = false; setTimeout(function () { m.hidden = true; }, 4000); } }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  /* ---------------- Configuracao salva ---------------- */
  function valid(w, d) { return WIDGETS.some(function (x) { return x[0] === w; }) ? w : d; }
  function validApp(a) { return APPS.some(function (x) { return x[0] === a; }) ? a : 'youtube'; }
  function overlaps(a, b) { return a.x < b.x + b.cw && b.x < a.x + a.cw && a.y < b.y + b.ch && b.y < a.y + a.ch; }
  function fits(t, list) {
    var min = t.w === 'map' ? MIN.map : MIN.tile;
    if (!(t.x >= 0 && t.y >= 0 && t.cw >= min[0] && t.ch >= min[1] && t.x + t.cw <= GX && t.y + t.ch <= GY)) return false;
    return list.every(function (o) { return o.id === t.id || !overlaps(t, o); });
  }
  function validFree(list) {
    if (!Array.isArray(list) || list.length > 8) return null;
    var out = [], maps = 0, apps = 0, ids = {};
    for (var i = 0; i < list.length; i++) {
      var t = list[i] || {};
      var w = t.w === 'map' ? 'map' : valid(t.w, null);
      var n = { id: String(t.id || ''), w: w, x: t.x | 0, y: t.y | 0, cw: t.cw | 0, ch: t.ch | 0 };
      if (!w || !/^[a-z0-9]{1,8}$/.test(n.id) || ids[n.id] || !fits(n, out)) return null;
      if (w === 'map') maps++; if (w === 'app') apps++;
      ids[n.id] = 1; out.push(n);
    }
    return maps === 1 && apps <= 1 ? out : null;
  }
  function load() {
    var d = clone(DEFAULT);
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (c && LAYOUTS.some(function (l) { return l[0] === c.layout; }) && Array.isArray(c.slots)) {
        return { layout: c.layout, slots: [valid(c.slots[0], 'musica'), valid(c.slots[1], 'carro')], app: validApp(c.app),
                 focus: FOCUSABLE.indexOf(c.focus) >= 0 ? c.focus : null, nav: c.nav === 'waze' ? 'waze' : 'harumi',
                 free: validFree(c.free) || d.free };
      }
    } catch (e) { /* sem armazenamento: usa o padrao */ }
    return d;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(cfg)); } catch (e) { /* ignora */ } }

  var cfg = load(), col, slotEls = [], menu, focusEl = null, focusSlot = null, appSlot = null, slotOpening = false;
  var freeEl, freeBar, editing = false, navArea, navSwitch, navHost = null, navUserClosed = false, lastWazeTry = 0;
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
      var nodata = el('p', 'hl-w-nodata', 'Sensores do carro ainda não instalados. A velocidade aparece quando o GPS estiver ligado.');
      box.appendChild(hero); box.appendChild(grid); box.appendChild(nodata); box.appendChild(open);
      return function () {
        var ok = Date.now() - fixAt < 15000;
        v.textContent = ok && speed != null ? Math.round(speed) : '--'; v.classList.toggle('none', !(ok && speed != null));
        src.textContent = ok ? 'GPS' : 'sem GPS';
        var m = (veh && veh.motor) || {}, bat = (veh && veh.bateria) || {}, pn = (veh && veh.pneus) || {};
        var any = m.aguaC != null || m.rpm != null || bat.volts != null || !!pn.pneus;
        grid.hidden = !any; nodata.hidden = any;
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
        if (a[0] === 'waze') return; // o Waze tem lugar proprio: o do mapa (botao Harumi | Waze)
        var b = button('hl-w-appbtn', a[1], 'Abrir ' + a[1] + ' nesta tela', function () {
          if (cfg.nav === 'waze') { notify('O Waze está no lugar do mapa. Volte para o mapa da Harumi para abrir outro app aqui.'); return; }
          cfg.app = a[0]; save(); openApp(slot, cfg.app); paintApps();
        });
        b.dataset.app = a[0]; bar.appendChild(b);
      });
      var area = el('div', 'hl-w-apparea'); var note = el('p', 'hl-w-sub', 'Toque num app para abrir aqui.'); area.appendChild(note);
      box.appendChild(bar); box.appendChild(area);
      slot.area = area; slot.note = note;
      function paintApps() { [].forEach.call(bar.children, function (b) { b.setAttribute('aria-pressed', b.dataset.app === cfg.app ? 'true' : 'false'); }); }
      paintApps();
      return function () {
        var cur = window.harumiEmbed && window.harumiEmbed.current && window.harumiEmbed.current();
        note.textContent = cfg.nav === 'waze' ? 'O Waze está no lugar do mapa.' : (cur && appSlot === slot ? '' : 'Toque num app para abrir aqui.');
        if (appSlot === slot && cur) placeEmbed(slot);
      };
    }
  };
  if (cfg.app === 'waze') cfg.app = 'youtube';

  /* ---------------- App dentro de uma area (tela ou lugar do mapa) ---------------- */
  function embedCard() { return document.getElementById('hl-embed'); }
  function current() { return window.harumiEmbed && window.harumiEmbed.current && window.harumiEmbed.current(); }
  function placeEmbed(slot) {
    var card = embedCard(); if (!card || !slot.area || card.classList.contains('full') || editing) return;
    var r = slot.area.getBoundingClientRect();
    if (r.width < 50 || r.height < 50) return;
    var s = card.style, px = function (n) { return Math.round(n) + 'px'; };
    var want = [px(r.left), px(r.top), px(r.width), px(r.height)];
    if (s.left === want[0] && s.top === want[1] && s.width === want[2] && s.height === want[3] && card.classList.contains('hl-in-slot')) return;
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
  function openApp(slot, id) {
    if (!window.harumiEmbed) return;
    appSlot = slot; slotOpening = true;
    try { window.harumiEmbed.open(id); } finally { slotOpening = false; }
    setTimeout(function () { placeEmbed(slot); }, 50);
  }
  function hookEmbed() {
    if (!window.harumiEmbed || window.harumiEmbed.__split) return;
    var orig = window.harumiEmbed.open;
    window.harumiEmbed.open = function (id) {
      if (!slotOpening) {
        appSlot = null; unplaceEmbed(); // aberto pelo dock: volta ao card/tela cheia normal
        if (cfg.nav === 'waze' && id === 'waze') { setTimeout(function () { applyNav(); }, 0); } // Waze pelo dock = Waze no lugar do mapa
      }
      return orig.apply(this, arguments);
    };
    window.harumiEmbed.__split = true;
  }

  /* ---------------- Navegador: Harumi (mapa) ou Waze no lugar do mapa ---------------- */
  function mapRect() {
    var c = document.getElementById('route-canvas'); if (!c) return null;
    var r = c.getBoundingClientRect(), topBar = 48;
    return { left: r.left, top: Math.max(r.top, topBar), right: r.right, bottom: r.bottom };
  }
  function syncNav() {
    var r = mapRect(); if (!r || !navSwitch) return;
    var show = SPLIT_MQ.matches && !editing && r.right - r.left > 200;
    navSwitch.hidden = !show;
    if (!show) return;
    navSwitch.style.left = Math.round(r.right - navSwitch.offsetWidth - 12) + 'px';
    navSwitch.style.top = Math.round(r.top + 8) + 'px';
    // o Waze ocupa o lugar do mapa, abaixo da faixa do seletor
    var a = navArea.style, top = r.top + 64;
    a.left = Math.round(r.left + 8) + 'px'; a.top = Math.round(top) + 'px';
    a.width = Math.max(0, Math.round(r.right - r.left - 16)) + 'px'; a.height = Math.max(0, Math.round(r.bottom - top - 8)) + 'px';
  }
  function paintNav() {
    if (!navSwitch) return;
    [].forEach.call(navSwitch.querySelectorAll('button'), function (b) { b.setAttribute('aria-pressed', b.dataset.nav === cfg.nav ? 'true' : 'false'); });
    document.body.classList.toggle('hl-nav-waze', cfg.nav === 'waze');
    paintSettings();
  }
  function applyNav() {
    paintNav();
    if (cfg.nav === 'waze') {
      if (!SPLIT_MQ.matches) return;
      syncNav();
      navUserClosed = false;
      if (current() === 'waze' && appSlot === navHost) { placeEmbed(navHost); return; }
      if (appSlot && appSlot !== navHost) unplaceEmbed(); // o app de uma tela da lugar ao Waze (so um app por vez)
      lastWazeTry = Date.now();
      openApp(navHost, 'waze');
    } else if (appSlot === navHost) {
      appSlot = null;
      if (current() === 'waze' && window.harumiEmbed) window.harumiEmbed.close();
      unplaceEmbed();
    }
  }
  function setNav(mode) { cfg.nav = mode === 'waze' ? 'waze' : 'harumi'; save(); applyNav(); tick(); }
  function buildNav() {
    navArea = el('div', 'hl-navarea'); navArea.setAttribute('aria-hidden', 'true'); document.body.appendChild(navArea);
    navHost = { area: navArea, nav: true };
    navSwitch = el('div', 'hl-navswitch'); navSwitch.setAttribute('role', 'group'); navSwitch.setAttribute('aria-label', 'Navegador');
    [['harumi', 'Harumi'], ['waze', 'Waze']].forEach(function (n) {
      var b = button('hl-navswitch-btn', n[1], 'Navegar com ' + n[1], function () { setNav(n[0]); });
      b.dataset.nav = n[0]; navSwitch.appendChild(b);
    });
    document.body.appendChild(navSwitch);
  }
  // "Me leva para X" com o Waze ativo: a rota abre no Waze Live Map. O link oficial waze.com/ul, na moldura (Linux),
  // mostra "Ainda não tem o Waze?"; o formato directions?to=ll.LAT,LON abre a rota (testado na placa em 20/11/2026;
  // não consta na documentação oficial). Texto vira coordenada pela busca da propria Harumi.
  function wazeOpenLL(lat, lon) {
    var url = WAZE_LIVE + 'directions?to=ll.' + Number(lat).toFixed(6) + '%2C' + Number(lon).toFixed(6);
    applyNav();
    setTimeout(function () { if (window.harumiHost && window.harumiHost.embedGo) window.harumiHost.embedGo(url); }, current() === 'waze' ? 0 : 2500);
  }
  function wazeText(text) {
    if (cfg.nav !== 'waze') return false;
    fetch('/assets/map-api/geocode?q=' + encodeURIComponent(String(text || '').slice(0, 160)))
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res || !res.length) { notify('Não encontrei “' + text + '”. Tente com o nome da cidade.'); applyNav(); return; }
        wazeOpenLL(res[0].lat, res[0].lon);
      })
      .catch(function () { notify('Sem internet para buscar o destino no Waze.'); });
    return true;
  }
  function hookRoadMap() {
    var rm = window.harumiRoadMap; if (!rm || rm.__split) return !!rm;
    var nav = rm.navigateTo, pt = rm.navigatePoint;
    rm.navigateTo = function (text) { if (wazeText(text)) return; return nav.apply(this, arguments); };
    if (pt) rm.navigatePoint = function (name, lat, lon) {
      if (cfg.nav === 'waze' && isFinite(lat) && isFinite(lon)) { wazeOpenLL(lat, lon); return; }
      return pt.apply(this, arguments);
    };
    rm.__split = true; return true;
  }

  /* ---------------- Coluna (layouts prontos) ---------------- */
  function build() {
    col = el('aside', 'hl-split'); col.id = 'hl-split'; col.setAttribute('aria-label', 'Telas ao lado do mapa');
    document.body.appendChild(col);
    freeEl = el('div', 'hl-free'); freeEl.id = 'hl-free'; freeEl.setAttribute('aria-label', 'Telas personalizadas'); document.body.appendChild(freeEl);
    freeBar = el('div', 'hl-free-bar'); freeBar.hidden = true; freeBar.setAttribute('role', 'toolbar'); freeBar.setAttribute('aria-label', 'Editar layout');
    freeBar.appendChild(el('span', 'hl-free-hint', 'Arraste as telas e puxe o canto para mudar o tamanho'));
    freeBar.appendChild(button('hl-free-btn', 'Adicionar tela', null, addTile));
    freeBar.appendChild(button('hl-free-btn', 'Restaurar', 'Restaurar o layout padrão', function () { cfg.free = clone(FREE_DEFAULT); save(); renderFree(); }));
    freeBar.appendChild(button('hl-free-btn primary', 'Concluir', 'Concluir a edição do layout', function () { setEditing(false); }));
    document.body.appendChild(freeBar);
    menu = el('div', 'hl-split-menu'); menu.hidden = true; menu.setAttribute('role', 'dialog'); menu.setAttribute('aria-label', 'Escolher o que mostrar');
    document.body.appendChild(menu);
    document.addEventListener('pointerdown', function (e) { if (!menu.hidden && !menu.contains(e.target) && !e.target.closest('.hl-slot-pick')) menu.hidden = true; });
    buildNav();
  }
  // Um so botao de opcoes por tela (avaliacao de UX: "Trocar" + tela cheia em todas as telas chamavam atencao o tempo
  // todo). O menu traz "Tela cheia", o que mostrar, o layout e o navegador.
  function slotHead(box, w, slot, pickFn) {
    var head = el('div', 'hl-slot-head'); head.appendChild(el('h3', '', label(w)));
    var pick = button('hl-slot-pick hl-slot-more', null, 'Opções da tela ' + label(w), function (ev) { menuSlot = { w: w, slot: slot }; pickFn(ev); });
    pick.appendChild(el('span', 'hl-dots', '•••'));
    head.appendChild(pick); box.appendChild(head);
  }
  var menuSlot = null;
  function menuFull() {
    var ms = menuSlot; if (!ms) return;
    menuOption('Abrir em tela cheia', false, function () { goFull(ms.w, ms.slot); });
  }
  function render() {
    var big = SPLIT_MQ.matches;
    var on = big && (cfg.layout === 'dividida' || cfg.layout === 'dividida1');
    var free = big && cfg.layout === 'livre';
    document.body.classList.toggle('hl-split-on', on);
    document.body.classList.toggle('hl-split-one', on && cfg.layout === 'dividida1');
    document.body.classList.toggle('hl-free-on', free);
    document.body.classList.toggle('hl-layout-mapa', big && cfg.layout === 'mapa');
    var used = on ? cfg.slots.slice(0, cfg.layout === 'dividida1' ? 1 : 2) : free ? cfg.free.map(function (t) { return t.w; }) : [];
    document.body.classList.toggle('hl-split-music', used.indexOf('musica') >= 0);
    var hadApp = appSlot && appSlot !== navHost ? appSlot : null;
    col.textContent = ''; freeEl.textContent = ''; slotEls = [];
    if (!free && editing) setEditing(false, true);
    if (on) renderColumn();
    else if (free) renderFree();
    col.hidden = !on; freeEl.hidden = !free;
    var appS = slotEls.filter(function (s) { return s.w === 'app'; })[0];
    if (appS && cfg.nav !== 'waze') {
      appSlot = appS;
      if (current()) setTimeout(function () { placeEmbed(appS); }, 50);
    } else if (hadApp) {
      appSlot = null;
      if (current() && current() !== 'waze') window.harumiEmbed.close();
      unplaceEmbed();
    }
    renderFocus();
    tick();
    setTimeout(function () { syncMapRect(); syncNav(); if (cfg.nav === 'waze') applyNav(); }, 0);
    window.dispatchEvent(new Event('resize')); // o mapa ajusta a largura
  }
  function renderColumn() {
    var n = cfg.layout === 'dividida1' ? 1 : 2, appIdx = -1;
    for (var i = 0; i < n; i++) {
      var w = cfg.slots[i];
      if (w === 'app') { if (appIdx >= 0) w = cfg.slots[i] = i === 0 ? 'musica' : 'carro'; else appIdx = i; } // so um app por vez
      var slot = { i: i, w: w };
      var box = el('section', 'hl-slot hl-slot-' + w); box.setAttribute('aria-label', label(w));
      slotHead(box, w, slot, (function (idx) { return function (ev) { openMenu(idx, ev.currentTarget); }; })(i));
      var body = el('div', 'hl-slot-body'); box.appendChild(body);
      slot.update = W[w](body, slot); slot.el = box;
      col.appendChild(box); slotEls.push(slot);
    }
  }

  /* ---------------- Layout personalizado (grade: arrastar e redimensionar) ---------------- */
  function placeTile(box, t) {
    var s = box.style;
    s.left = 'calc(' + (t.x / GX * 100).toFixed(4) + '% + 5px)';
    s.top = 'calc(' + (t.y / GY * 100).toFixed(4) + '% + 5px)';
    s.width = 'calc(' + (t.cw / GX * 100).toFixed(4) + '% - 10px)';
    s.height = 'calc(' + (t.ch / GY * 100).toFixed(4) + '% - 10px)';
  }
  function renderFree() {
    freeEl.textContent = ''; slotEls = slotEls.filter(function (s) { return !s.free; });
    cfg.free.forEach(function (t) {
      var box = el('section', t.w === 'map' ? 'hl-ftile hl-ftile-map' : 'hl-ftile hl-slot hl-slot-' + t.w);
      box.dataset.id = t.id; box.setAttribute('aria-label', t.w === 'map' ? 'Mapa' : label(t.w));
      placeTile(box, t);
      if (t.w === 'map') {
        box.appendChild(el('span', 'hl-ftile-label', 'Mapa · navegação'));
      } else {
        var slot = { w: t.w, free: true, tile: t };
        slotHead(box, t.w, slot, function (ev) { openFreeMenu(t, ev.currentTarget); });
        var body = el('div', 'hl-slot-body'); box.appendChild(body);
        slot.update = W[t.w](body, slot); slot.el = box; slotEls.push(slot);
        var rm = button('hl-ftile-x', '×', 'Remover esta tela', function () { cfg.free = cfg.free.filter(function (o) { return o.id !== t.id; }); save(); renderFree(); });
        box.appendChild(rm);
      }
      var grip = el('span', 'hl-ftile-grip'); grip.setAttribute('aria-hidden', 'true'); box.appendChild(grip);
      box.addEventListener('pointerdown', function (e) { startDrag(e, t, box); });
      freeEl.appendChild(box);
    });
    syncMapRect();
  }
  var drag = null;
  function startDrag(e, t, box) {
    if (!editing || e.button > 0 || e.target.closest('button')) return;
    e.preventDefault();
    var r = freeEl.getBoundingClientRect();
    drag = { t: t, box: box, mode: e.target.classList.contains('hl-ftile-grip') ? 'resize' : 'move', px: e.clientX, py: e.clientY,
             o: { x: t.x, y: t.y, cw: t.cw, ch: t.ch }, cw: r.width / GX, chh: r.height / GY, id: e.pointerId };
    box.classList.add('dragging');
    try { box.setPointerCapture(e.pointerId); } catch (err) { /* sem captura */ }
  }
  function moveDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    var dx = Math.round((e.clientX - drag.px) / drag.cw), dy = Math.round((e.clientY - drag.py) / drag.chh), o = drag.o;
    var cand = drag.mode === 'move' ? { id: drag.t.id, w: drag.t.w, x: o.x + dx, y: o.y + dy, cw: o.cw, ch: o.ch }
                                    : { id: drag.t.id, w: drag.t.w, x: o.x, y: o.y, cw: o.cw + dx, ch: o.ch + dy };
    if (cand.x === drag.t.x && cand.y === drag.t.y && cand.cw === drag.t.cw && cand.ch === drag.t.ch) return;
    if (!fits(cand, cfg.free)) return; // nao sobrepoe outra tela nem sai da grade
    drag.t.x = cand.x; drag.t.y = cand.y; drag.t.cw = cand.cw; drag.t.ch = cand.ch;
    placeTile(drag.box, drag.t);
    if (drag.t.w === 'map') syncMapRect();
  }
  function endDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    drag.box.classList.remove('dragging'); drag = null; save(); syncMapRect();
  }
  function addTile() {
    var taken = cfg.free.map(function (t) { return t.w; });
    var w = (WIDGETS.filter(function (x) { return taken.indexOf(x[0]) < 0 && x[0] !== 'app'; })[0] || ['relogio'])[0];
    for (var ch = 6; ch >= MIN.tile[1]; ch--) {
      for (var cw = 8; cw >= MIN.tile[0]; cw--) {
        for (var y = 0; y + ch <= GY; y++) {
          for (var x = 0; x + cw <= GX; x++) {
            var t = { id: 't' + Date.now().toString(36).slice(-6), w: w, x: x, y: y, cw: cw, ch: ch };
            if (fits(t, cfg.free) && cfg.free.length < 8) { cfg.free.push(t); save(); renderFree(); return; }
          }
        }
      }
    }
    notify('Não há espaço livre. Diminua o mapa ou outra tela e tente de novo.');
  }
  function setEditing(on, silent) {
    editing = !!on;
    document.body.classList.toggle('hl-free-edit', editing);
    freeBar.hidden = !editing;
    // o app embutido fica por cima de tudo: some durante a edicao para nao cobrir as telas
    if (window.harumiEmbed && window.harumiEmbed.suspend) window.harumiEmbed.suspend(editing);
    if (!editing && !silent) { save(); render(); }
    syncNav();
  }
  function editLayout() {
    if (!SPLIT_MQ.matches) { notify('O layout personalizado precisa de uma tela com pelo menos 900 pixels de largura.'); return; }
    if (cfg.layout !== 'livre') { cfg.free = presetToFree(); cfg.layout = 'livre'; cfg.focus = null; save(); render(); }
    setEditing(true);
  }
  function presetToFree() {
    if (cfg.layout === 'dividida1') return [{ id: 'map', w: 'map', x: 0, y: 0, cw: 15, ch: 12 }, { id: 't1', w: cfg.slots[0], x: 15, y: 0, cw: 9, ch: 12 }];
    if (cfg.layout === 'mapa' || cfg.layout === 'painel') return [{ id: 'map', w: 'map', x: 0, y: 0, cw: 24, ch: 12 }];
    var f = clone(FREE_DEFAULT); f[1].w = cfg.slots[0]; f[2].w = cfg.slots[1];
    if (f[1].w === 'app' && f[2].w === 'app') f[2].w = 'carro';
    return f;
  }
  // O mapa de verdade (#route-canvas e os botoes dele) segue o retangulo da tela "Mapa" do layout personalizado
  var lastMapVars = '';
  function syncMapRect() {
    var b = document.body;
    if (!b.classList.contains('hl-free-on')) {
      if (lastMapVars) { ['--map-l', '--map-t', '--map-r', '--map-b'].forEach(function (k) { b.style.removeProperty(k); }); lastMapVars = ''; window.dispatchEvent(new Event('resize')); }
      return;
    }
    var m = freeEl.querySelector('.hl-ftile-map'); if (!m) return;
    var r = m.getBoundingClientRect();
    var vars = [Math.round(r.left), Math.round(r.top), Math.round(window.innerWidth - r.right), Math.round(window.innerHeight - r.bottom)];
    var key = vars.join(',');
    if (key === lastMapVars) return;
    lastMapVars = key;
    b.style.setProperty('--map-l', vars[0] + 'px'); b.style.setProperty('--map-t', vars[1] + 'px');
    b.style.setProperty('--map-r', vars[2] + 'px'); b.style.setProperty('--map-b', vars[3] + 'px');
    window.dispatchEvent(new Event('resize')); // o MapLibre redesenha no novo tamanho
  }

  /* ---------------- Tela cheia focada em um app (como no CarPlay) ---------------- */
  function goFull(w, slot) {
    if (w === 'carro') { var c = document.querySelector('.hl-dock-car'); if (c) c.click(); return; }
    if (w === 'app') {
      var cur = current();
      if (!cur) openApp(slot, cfg.app);
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
    var on = !!cfg.focus && (document.body.classList.contains('hl-split-on') || document.body.classList.contains('hl-free-on')) && !editing;
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

  /* ---------------- Menus ---------------- */
  function label(w) { var f = WIDGETS.filter(function (x) { return x[0] === w; })[0]; return f ? f[1] : w; }
  function showMenu(anchor) {
    var r = anchor.getBoundingClientRect();
    menu.hidden = false;
    var mw = menu.offsetWidth, mh = menu.offsetHeight;
    menu.style.left = Math.max(8, Math.min(window.innerWidth - mw - 8, r.right - mw)) + 'px';
    menu.style.top = Math.max(8, Math.min(window.innerHeight - mh - 8, r.bottom + 6)) + 'px';
    var first = menu.querySelector('button'); if (first) first.focus();
  }
  function menuOption(text, pressed, fn) {
    var b = button('hl-split-opt', text, null, function () { menu.hidden = true; fn(); });
    b.setAttribute('aria-pressed', pressed ? 'true' : 'false'); menu.appendChild(b); return b;
  }
  function menuCommon() {
    menu.appendChild(el('p', 'hl-split-menu-title', 'Layout'));
    LAYOUTS.forEach(function (l) { menuOption(l[1], cfg.layout === l[0], function () { setLayout(l[0]); }); });
    menuOption('Editar layout (arrastar e redimensionar)', false, editLayout);
    menu.appendChild(el('p', 'hl-split-menu-title', 'Navegador'));
    menuOption('Harumi', cfg.nav === 'harumi', function () { setNav('harumi'); });
    menuOption('Waze no lugar do mapa', cfg.nav === 'waze', function () { setNav('waze'); });
  }
  function openMenu(idx, anchor) {
    menu.textContent = '';
    menuFull();
    menu.appendChild(el('p', 'hl-split-menu-title', 'Mostrar nesta tela'));
    var used = cfg.slots.slice(0, cfg.layout === 'dividida1' ? 1 : 2);
    WIDGETS.forEach(function (w) {
      menuOption(w[1], cfg.slots[idx] === w[0], function () {
        var other = used.indexOf(w[0]);
        if (other >= 0 && other !== idx) cfg.slots[other] = cfg.slots[idx]; // troca de lugar em vez de repetir
        cfg.slots[idx] = w[0]; save(); render();
      });
    });
    menuCommon(); showMenu(anchor);
  }
  function openFreeMenu(t, anchor) {
    menu.textContent = '';
    menuFull();
    menu.appendChild(el('p', 'hl-split-menu-title', 'Mostrar nesta tela'));
    WIDGETS.forEach(function (w) {
      menuOption(w[1], t.w === w[0], function () {
        if (w[0] === 'app') cfg.free.forEach(function (o) { if (o.w === 'app' && o.id !== t.id) o.w = t.w; }); // so um app por vez
        t.w = w[0]; save(); render();
      });
    });
    menuOption('Remover esta tela', false, function () { cfg.free = cfg.free.filter(function (o) { return o.id !== t.id; }); save(); render(); });
    menuCommon(); showMenu(anchor);
  }
  function setLayout(l) { cfg.layout = l; save(); render(); paintSettings(); }

  /* ---------------- Ajustes ---------------- */
  var setBtns = [], navBtns = [];
  function settings() {
    if (!window.harumiLinux || !window.harumiLinux.addSettingsSection) return;
    var wrap = el('div', 'hl-split-settings');
    LAYOUTS.forEach(function (l) {
      var b = button('hl-split-opt', l[1], null, function () { setLayout(l[0]); }); b.dataset.layout = l[0]; setBtns.push(b); wrap.appendChild(b);
    });
    wrap.appendChild(button('hl-split-opt', 'Editar layout', 'Editar layout: arrastar e redimensionar as telas', function () {
      if (window.harumiShell && window.harumiShell.closeAll) window.harumiShell.closeAll(); editLayout();
    }));
    wrap.appendChild(el('p', 'hl-split-note', 'Em “Personalizado”, toque em “Editar layout”: arraste cada tela para mudar de lugar, puxe o canto para mudar o tamanho, adicione ou remova telas.'));
    window.harumiLinux.addSettingsSection('Telas', wrap);
    var nav = el('div', 'hl-split-settings');
    [['harumi', 'Harumi (padrão)'], ['waze', 'Waze no lugar do mapa']].forEach(function (n) {
      var b = button('hl-split-opt', n[1], null, function () { setNav(n[0]); }); b.dataset.nav = n[0]; navBtns.push(b); nav.appendChild(b);
    });
    nav.appendChild(el('p', 'hl-split-note', 'Com o Waze, “me leva para…” abre a rota no Waze. O botão Harumi | Waze no canto do mapa alterna a qualquer hora. O Waze precisa de internet.'));
    window.harumiLinux.addSettingsSection('Navegador', nav);
    paintSettings();
  }
  function paintSettings() {
    setBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.layout === cfg.layout ? 'true' : 'false'); });
    navBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.nav === cfg.nav ? 'true' : 'false'); });
  }

  /* ---------------- Atualizacao ---------------- */
  function tick() {
    slotEls.concat(focusSlot ? [focusSlot] : []).forEach(function (s) { try { s.update(); } catch (e) { /* um widget com erro nao derruba os outros */ } });
    syncNav();
    if (cfg.nav === 'waze' && SPLIT_MQ.matches && !editing) {
      var cur = current();
      if (appSlot === navHost && cur === 'waze') placeEmbed(navHost);
      else if (!cur && !navUserClosed && Date.now() - lastWazeTry > 6000) applyNav(); // outro app fechou: o Waze volta
    }
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && editing) { setEditing(false); return; }
    if (e.key === 'Escape' && cfg.focus) closeFull();
  });
  function start() {
    build(); hookEmbed(); render(); settings(); paintNav();
    var prev = window.harumiSpotifyNow;
    window.harumiSpotifyNow = function (s) { if (prev) prev(s); spot = s || null; tick(); };
    window.addEventListener('hl-vehicle', function (e) { veh = e.detail || null; tick(); });
    window.addEventListener('hl-fix', function (e) {
      var f = e.detail || {}, v = Number.isFinite(f.speedMps) ? f.speedMps : f.speed;
      fixAt = Date.now(); if (Number.isFinite(v)) speed = v * 3.6; tick();
    });
    (function waitRoadMap(n) { if (!hookRoadMap() && n < 120) setTimeout(function () { waitRoadMap(n + 1); }, 500); })(0);
    var card = null;
    (function watchCard(n) {
      card = embedCard(); hookEmbed();
      if (!card) { if (n < 120) setTimeout(function () { watchCard(n + 1); }, 500); return; }
      // "Tela cheia" do app: solta da area; "Card": volta para a area
      new MutationObserver(function () {
        if (card.classList.contains('full')) { if (card.classList.contains('hl-in-slot')) unplaceEmbed(); }
        else if (appSlot && !card.hidden) placeEmbed(appSlot);
      }).observe(card, { attributes: true, attributeFilter: ['class', 'hidden'] });
    })(0);
    // Fechar o Waze pelo botao do card = voltar para o mapa da Harumi
    if (window.harumiHost && window.harumiHost.onEmbedClosed) window.harumiHost.onEmbedClosed(function (id) {
      if (id === 'waze' && appSlot === navHost && cfg.nav === 'waze') { navUserClosed = true; appSlot = null; setNav('harumi'); }
    });
    document.addEventListener('pointermove', moveDrag);
    document.addEventListener('pointerup', endDrag);
    document.addEventListener('pointercancel', endDrag);
    if (SPLIT_MQ.addEventListener) SPLIT_MQ.addEventListener('change', render);
    window.addEventListener('resize', function () { syncMapRect(); syncNav(); if (appSlot) placeEmbed(appSlot); });
    setInterval(tick, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

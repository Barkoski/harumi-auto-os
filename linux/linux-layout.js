/* Harumi OS no Orange Pi: o mapa da Harumi vira o fundo permanente, com painel do carro, cards deslizaveis,
   barra de status, gaveta de apps, dock personalizavel e volume. Camada so do Linux: reaproveita a interface
   (road-map.js, app.js) sem alterar os arquivos do Android. */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var DOCK_KEY = 'hl.dock.v1', DOCK_MAX = window.innerWidth >= 1600 ? 9 : 7; // tela de 10" (1280) cabe 7; monitor grande, 9
  var DEFAULT_DOCK = ['nav', 'music', 'video', 'harumi', 'camera', 'waze']; // o carro ja tem botao proprio a esquerda da barra
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function icon(id) {
    var svg = document.createElementNS(NS, 'svg'), use = document.createElementNS(NS, 'use');
    svg.setAttribute('class', 'ck-ico'); svg.setAttribute('aria-hidden', 'true'); svg.setAttribute('focusable', 'false');
    use.setAttribute('href', '#' + id); svg.appendChild(use); return svg;
  }
  function notify(text) {
    var m = $('message'); if (!m) return;
    m.textContent = text; m.hidden = false; clearTimeout(notify.t); notify.t = setTimeout(function () { m.hidden = true; }, 4500);
  }
  function send(action, module) { if (window.HarumiNative) window.HarumiNative.dispatch(action, module || ''); }
  function closePanels() { if (window.harumiShell && window.harumiShell.closeAll) window.harumiShell.closeAll(); closeDrawer(); }
  function click(id) { var e = $(id); if (e) e.click(); }

  /* ---------------- Apps da Harumi OS (gaveta e dock) ---------------- */
  var APPS = [
    { id: 'nav', label: 'Navegar', icon: 'ck-nav', run: function () { closePanels(); var d = $('nav-dest'); if (d) d.focus(); } },
    { id: 'music', label: 'Spotify', icon: 'ck-music', img: 'spotify', run: function () { closePanels(); showCard('music'); window.harumiLinuxOpen('spotify'); } },
    { id: 'waze', label: 'Waze', icon: 'ck-nav', img: 'waze', run: function () { closePanels(); window.harumiLinuxOpen('waze'); } },
    { id: 'video', label: 'YouTube', icon: 'ck-play', img: 'youtube', run: function () { closePanels(); window.harumiLinuxOpen('youtube'); } },
    { id: 'browser', label: 'Navegador', icon: 'ck-globe', img: 'browser', run: function () { closePanels(); window.harumiLinuxOpen('browser'); } },
    { id: 'harumi', label: 'Harumi', icon: 'ck-harumi', run: function () { closeDrawer(); click('talk'); } },
    { id: 'claude', label: 'Claude', icon: 'ck-chat', img: 'claude', run: function () { closePanels(); window.harumiLinuxOpen('claude'); } },
    { id: 'chatgpt', label: 'ChatGPT', icon: 'ck-chat', img: 'chatgpt', run: function () { closePanels(); window.harumiLinuxOpen('chatgpt'); } },
    { id: 'camera', label: 'Câmeras', icon: 'ck-camera', run: function () { notify('Câmera de ré: aguardando a câmera USB e o sinal da ré.'); } },
    { id: 'car', label: 'Carro', icon: 'ck-car', run: function () { closeDrawer(); var b = document.querySelector('.hl-dock-car'); if (b) b.click(); } },
    { id: 'trip', label: 'Viagem', icon: 'ck-compass', run: function () { closePanels(); showCard('trip'); } },
    { id: 'atlas', label: 'Atlas', icon: 'ck-globe', run: function () { closeDrawer(); click('open-atlas'); } },
    { id: 'internet', label: 'Internet', icon: 'ck-wifi', run: function () { closeDrawer(); click('connections'); } },
    { id: 'settings', label: 'Ajustes', icon: 'ck-settings', run: function () { closeDrawer(); click('configure'); } },
    { id: 'catalog', label: 'Catálogo', icon: 'ck-apps', run: function () { closeDrawer(); click('open-apps'); } }
  ];
  /* Icone oficial do app (baixado para o aparelho por tools/fetch-icons.sh); sem arquivo, volta ao icone de linha. */
  function appIcon(a) {
    if (!a.img) return icon(a.icon);
    var img = el('img', 'hl-app-img'); img.alt = ''; img.src = '/app-icon/' + a.img; img.decoding = 'async';
    img.addEventListener('error', function () { img.replaceWith(icon(a.icon)); });
    return img;
  }
  function app(id) { for (var i = 0; i < APPS.length; i++) if (APPS[i].id === id) return APPS[i]; return null; }
  function flash(node) { if (!node) return; node.scrollIntoView({ block: 'nearest' }); node.classList.add('hl-flash'); setTimeout(function () { node.classList.remove('hl-flash'); }, 1200); }

  function loadDock() {
    try {
      var v = JSON.parse(localStorage.getItem(DOCK_KEY));
      if (Array.isArray(v)) {
        // avaliacao de UX (20/11/2026): "Carro" no dock repetia o botao do carro da esquerda; troca uma vez pelo Waze
        if (!localStorage.getItem('hl.dock.mig1')) {
          var i = v.indexOf('car');
          if (i >= 0) { if (v.indexOf('waze') < 0) v[i] = 'waze'; else v.splice(i, 1); localStorage.setItem(DOCK_KEY, JSON.stringify(v)); }
          localStorage.setItem('hl.dock.mig1', '1');
        }
        return v.filter(app).slice(0, DOCK_MAX);
      }
    } catch (e) { /* sem storage */ }
    return DEFAULT_DOCK.slice();
  }
  function saveDock(list) { try { localStorage.setItem(DOCK_KEY, JSON.stringify(list)); } catch (e) { /* sem storage */ } }
  var pinned = loadDock();

  var dockApps, volLabel;
  function buildDock() {
    var nav = el('nav'); nav.id = 'hl-dock'; nav.setAttribute('aria-label', 'Harumi OS');
    dockApps = el('div', 'hl-dock-apps'); nav.appendChild(dockApps);
    nav.appendChild(sep());
    var all = dockButton({ id: 'drawer', label: 'Apps', icon: 'ck-apps', run: toggleDrawer }); all.id = 'hl-dock-drawer'; nav.appendChild(all);
    nav.appendChild(sep());
    var vol = el('div', 'hl-vol'); vol.setAttribute('role', 'group'); vol.setAttribute('aria-label', 'Volume');
    var minus = el('button', 'hl-vol-btn', '−'); minus.type = 'button'; minus.setAttribute('aria-label', 'Diminuir volume');
    var plus = el('button', 'hl-vol-btn', '+'); plus.type = 'button'; plus.setAttribute('aria-label', 'Aumentar volume');
    volLabel = el('button', 'hl-vol-level', '—'); volLabel.type = 'button'; volLabel.setAttribute('aria-label', 'Silenciar ou reativar o som');
    minus.addEventListener('click', function () { send('volume.step', '-5'); });
    plus.addEventListener('click', function () { send('volume.step', '+5'); });
    volLabel.addEventListener('click', function () { send('volume.mute'); });
    vol.appendChild(minus); vol.appendChild(volLabel); vol.appendChild(plus);
    nav.appendChild(vol);
    document.body.appendChild(nav);
    renderDock();
  }
  function sep() { var s = el('span', 'hl-dock-sep'); s.setAttribute('aria-hidden', 'true'); return s; }
  function dockButton(a) {
    var b = el('button'); b.type = 'button'; b.dataset.dock = a.id; b.appendChild(a.img ? appIcon(a) : icon(a.icon)); b.appendChild(el('span', '', a.label));
    b.addEventListener('click', a.run); return b;
  }
  function renderDock() { dockApps.textContent = ''; pinned.forEach(function (id) { var a = app(id); if (a) dockApps.appendChild(dockButton(a)); }); }

  window.harumiVolume = function (v) {
    if (!volLabel) return;
    if (!v) { volLabel.textContent = '—'; return; }
    volLabel.textContent = v.muted ? 'Mudo' : v.percent + '%';
    volLabel.setAttribute('aria-pressed', v.muted ? 'true' : 'false');
  };

  /* Gaveta: todos os apps; no modo "Editar dock" o toque fixa/solta o app no dock */
  var drawer, grid, editBtn, hint, editing = false;
  function buildDrawer() {
    drawer = el('section'); drawer.id = 'hl-drawer'; drawer.hidden = true; drawer.setAttribute('aria-label', 'Todos os apps');
    var head = el('div', 'hl-drawer-head');
    head.appendChild(el('h2', '', 'Apps'));
    hint = el('span', 'hl-drawer-hint', ''); head.appendChild(hint);
    editBtn = el('button', 'hl-drawer-edit', 'Editar dock'); editBtn.type = 'button';
    editBtn.addEventListener('click', function () { setEditing(!editing); });
    head.appendChild(editBtn);
    var close = el('button', 'hl-drawer-close'); close.type = 'button'; close.setAttribute('aria-label', 'Fechar apps'); close.appendChild(icon('ck-close'));
    close.addEventListener('click', closeDrawer); head.appendChild(close);
    grid = el('div', 'hl-drawer-grid');
    drawer.appendChild(head); drawer.appendChild(grid);
    document.body.appendChild(drawer);
  }
  function setEditing(on) {
    editing = on; editBtn.textContent = on ? 'Concluir' : 'Editar dock';
    hint.textContent = on ? 'Toque para fixar ou tirar do dock (até ' + DOCK_MAX + ')' : '';
    renderDrawer();
  }
  function renderDrawer() {
    grid.textContent = '';
    APPS.forEach(function (a) {
      var on = pinned.indexOf(a.id) >= 0;
      var b = el('button', 'hl-tile'); b.type = 'button';
      var ic = el('span', 'hl-tile-ico' + (a.img ? ' has-img' : '')); ic.appendChild(appIcon(a)); b.appendChild(ic); b.appendChild(el('span', 'hl-tile-name', a.label));
      if (editing) { b.classList.add('editing'); b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.appendChild(el('span', 'hl-tile-pin', on ? 'No dock' : 'Fixar')); }
      b.addEventListener('click', function () {
        if (!editing) { a.run(); return; }
        if (on) pinned = pinned.filter(function (x) { return x !== a.id; });
        else if (pinned.length < DOCK_MAX) pinned.push(a.id);
        else { notify('O dock já tem ' + DOCK_MAX + ' apps. Tire um antes.'); return; }
        saveDock(pinned); renderDock(); renderDrawer();
      });
      grid.appendChild(b);
    });
  }
  function openDrawer() { if (window.harumiShell && window.harumiShell.closeAll) window.harumiShell.closeAll(); setEditing(false); drawer.hidden = false; $('hl-dock-drawer').setAttribute('aria-pressed', 'true'); }
  function closeDrawer() { if (!drawer || drawer.hidden) return; drawer.hidden = true; $('hl-dock-drawer').setAttribute('aria-pressed', 'false'); }
  function toggleDrawer() { if (drawer.hidden) openDrawer(); else closeDrawer(); }

  /* ---------------- Barra de status (topo do mapa) ---------------- */
  var tempEl, netEl;
  function buildStatus() {
    var right = document.querySelector('#road-map .ck-top .ck-right'); if (!right) return;
    tempEl = el('span', 'hl-status-temp', ''); tempEl.title = 'Temperatura da placa';
    netEl = el('span', 'hl-status-net', '');
    right.insertBefore(tempEl, right.firstChild);
    right.insertBefore(netEl, tempEl.nextSibling);
  }
  function pollStatus() {
    fetch('/linux/status').then(function (r) { return r.ok ? r.json() : null; }).then(function (s) {
      if (!s) return;
      // Topo sem jargao: a temperatura da placa so aparece quando esta alta; a rede vira "Online" / "Sem internet"
      if (tempEl) { var hot = s.tempC != null && s.tempC >= 75; tempEl.textContent = hot ? 'Central quente · ' + s.tempC + ' °C' : ''; tempEl.classList.toggle('hot', s.tempC >= 80); }
      if (netEl) netEl.textContent = s.online === false ? 'Sem internet · mapa offline' : s.online ? 'Online' : '';
      window.harumiVolume(s.volume);
      if (s.spotify) window.harumiSpotifyNow(s.spotify);
      window.dispatchEvent(new CustomEvent('hl-status', { detail: s }));
    }).catch(function () { /* servidor reiniciando */ });
  }

  /* ---------------- Cards deslizaveis (coluna direita): Musica e Viagem ---------------- */
  var cards, track, dots, pages = [], page = 0, music = {}, trip = { km: 0, startMs: 0, last: null };
  function row(dl, label, value) { var dt = el('dt', '', label), dd = el('dd', '', value); dl.appendChild(dt); dl.appendChild(dd); return dd; }
  function buildCards() {
    var right = document.querySelector('#road-map aside.ck-right') || document.querySelector('#road-map > .ck-right'); if (!right) return;
    cards = el('section', 'ck-card'); cards.id = 'hl-cards'; cards.setAttribute('aria-label', 'Cards');
    cards.setAttribute('aria-roledescription', 'carrossel');
    track = el('div', 'hl-cards-track');
    var pm = el('div', 'hl-page'); pm.dataset.page = 'music'; pm.setAttribute('aria-label', 'Música');
    var mt = el('div', 'hl-music-text');
    music.state = el('span', 'hl-kicker', 'Spotify · dispositivo Harumi');
    music.name = el('strong', '', 'Nada tocando');
    music.artist = el('span', 'hl-sub', 'Escolha “Harumi” no app Spotify');
    mt.appendChild(music.state); mt.appendChild(music.name); mt.appendChild(music.artist);
    pm.appendChild(mt);
    var pt = el('div', 'hl-page'); pt.dataset.page = 'trip'; pt.setAttribute('aria-label', 'Viagem');
    pt.appendChild(el('span', 'hl-kicker', 'Viagem desde que ligou'));
    var dl = el('dl', 'hl-trip');
    trip.kmEl = row(dl, 'Distância', '—'); trip.timeEl = row(dl, 'Tempo', '—'); trip.avgEl = row(dl, 'Média', '—');
    pt.appendChild(dl);
    trip.note = el('span', 'hl-sub', 'Precisa do GPS para medir.'); pt.appendChild(trip.note);
    track.appendChild(pm); track.appendChild(pt);
    pages = [pm, pt];
    dots = el('div', 'hl-dots'); dots.setAttribute('role', 'tablist');
    pages.forEach(function (p, i) {
      var d = el('button', 'hl-dot'); d.type = 'button'; d.appendChild(el('i', 'hl-dot-mark')); d.setAttribute('role', 'tab'); d.setAttribute('aria-label', p.getAttribute('aria-label'));
      d.addEventListener('click', function () { go(i); }); dots.appendChild(d);
    });
    cards.appendChild(track); cards.appendChild(dots);
    right.insertBefore(cards, right.firstChild);
    swipe(track);
    go(0);
  }
  function go(i) {
    page = Math.max(0, Math.min(pages.length - 1, i));
    track.style.transform = 'translateX(' + (-100 * page) + '%)';
    [].forEach.call(dots.children, function (d, k) { d.setAttribute('aria-selected', k === page ? 'true' : 'false'); });
    pages.forEach(function (p, k) { p.setAttribute('aria-hidden', k === page ? 'false' : 'true'); });
  }
  function showCard(name) { pages.forEach(function (p, i) { if (p.dataset.page === name) go(i); }); flash(cards); }
  function swipe(node) {
    var x0 = null;
    node.addEventListener('pointerdown', function (e) { x0 = e.clientX; });
    node.addEventListener('pointerup', function (e) { if (x0 == null) return; var dx = e.clientX - x0; x0 = null; if (Math.abs(dx) > 40) go(page + (dx < 0 ? 1 : -1)); });
    node.addEventListener('pointercancel', function () { x0 = null; });
  }
  window.harumiSpotifyNow = function (s) {
    if (!music.name || !s) return;
    music.name.textContent = s.name || 'Nada tocando';
    music.artist.textContent = s.artists || '';
    music.state.textContent = 'Spotify · ' + (s.state === 'playing' ? 'tocando' : s.state === 'paused' ? 'pausado' : 'dispositivo Harumi');
  };
  function tripFix(f) {
    if (!f || !Number.isFinite(f.lat) || !Number.isFinite(f.lon)) return;
    var now = Date.now();
    if (!trip.startMs) trip.startMs = now;
    if (trip.last) {
      var dy = (f.lat - trip.last.lat) * 111.0, dx = (f.lon - trip.last.lon) * 111.0 * Math.cos(f.lat * Math.PI / 180);
      var d = Math.sqrt(dx * dx + dy * dy); if (d < 1) trip.km += d; // ignora saltos de GPS
    }
    trip.last = f;
    var h = (now - trip.startMs) / 3600000;
    trip.kmEl.textContent = trip.km.toFixed(1) + ' km';
    trip.timeEl.textContent = Math.floor(h) + ' h ' + Math.round((h % 1) * 60) + ' min';
    trip.avgEl.textContent = h > 0.01 ? Math.round(trip.km / h) + ' km/h' : '—';
    trip.note.textContent = '';
  }

  /* ---------------- Painel do carro (coluna esquerda) ---------------- */
  var speedEl, unitEl;
  function buildCar() {
    var left = document.querySelector('#road-map .ck-left'); if (!left) return;
    var card = el('section', 'ck-card'); card.id = 'hl-car'; card.setAttribute('aria-label', 'Carro');
    var head = el('div', 'hl-car-head'); head.appendChild(el('strong', '', 'Subaru Impreza')); head.appendChild(el('span', '', '1993 · EJ18'));
    var sp = el('div', 'hl-speed'); speedEl = el('b', '', '—'); unitEl = el('span', '', 'km/h · sem GPS'); sp.appendChild(speedEl); sp.appendChild(unitEl);
    var dl = el('dl');
    function r(label, value, wait) { var dd = row(dl, label, value); if (wait) dd.className = 'hl-wait'; }
    r('Diagnóstico', 'aguardando adaptador', true); r('Câmera de ré', 'não instalada', true); r('Spotify', 'dispositivo Harumi'); r('IA', 'local · Qwen 2B');
    card.appendChild(head); card.appendChild(sp); card.appendChild(dl);
    left.insertBefore(card, left.firstChild);
  }
  function hookGps() {
    var nav = window.harumiNav; if (!nav || typeof nav.fix !== 'function' || nav.__hlWrapped) return;
    var orig = nav.fix;
    nav.fix = function (f) {
      try {
        var v = f && (Number.isFinite(f.speedMps) ? f.speedMps : f.speed);
        if (Number.isFinite(v)) {
          speedEl.textContent = Math.round(v * 3.6); unitEl.textContent = 'km/h';
          if (window.harumiEmbed && window.harumiEmbed.moving) window.harumiEmbed.moving(v * 3.6);
        }
        tripFix(f);
        window.dispatchEvent(new CustomEvent('hl-fix', { detail: f }));
      } catch (e) { /* so exibicao */ }
      return orig.apply(this, arguments);
    };
    nav.__hlWrapped = true;
  }

  /* ---------------- Mapa sempre aberto + app embutido suspenso sob outras telas ---------------- */
  function keepMap() {
    var rm = window.harumiRoadMap; if (!rm) return false;
    if (!rm.__hlKeep) { rm.__hlClose = rm.close; rm.close = function () { /* no Harumi OS o mapa e o fundo e nunca fecha */ }; rm.__hlKeep = true; }
    if (!rm.isOpen()) rm.open(false);
    return true;
  }
  function watchOverlays() {
    var ids = ['assistant', 'apps-panel', 'settings', 'connectivity', 'brazil-atlas', 'hl-drawer', 'hl-carview'];
    function update() {
      var covered = ids.some(function (id) { var n = $(id); return n && !n.hidden; });
      if (window.harumiEmbed) window.harumiEmbed.suspend(covered);
    }
    var mo = new MutationObserver(update);
    // a vista do carro (linux-mcu.js) pode nascer depois: observa quando aparecer
    function attach() { ids.forEach(function (id) { var n = $(id); if (n && !n.__hlObs) { n.__hlObs = true; mo.observe(n, { attributes: true, attributeFilter: ['hidden'] }); } }); }
    attach(); setTimeout(attach, 3000); setTimeout(attach, 8000);
  }

  /* ---------------- API para modulos (linux/modules/*.js) ----------------
     window.harumiLinux era `true` (linux-bridge.js); vira objeto (sempre truthy) com addApp e addSettingsSection. */
  var extraSections = [];
  function placeSection(sec) {
    var screen = $('settings'), list = screen && screen.querySelector('.hu-row-list'); if (!list) return false;
    var anchor = list;
    if (anchor.nextSibling && anchor.nextSibling.className === 'hl-settings-empty') anchor = anchor.nextSibling;
    extraSections.forEach(function (n) { if (n.parentNode === list.parentNode) anchor = n; });
    list.parentNode.insertBefore(sec, anchor.nextSibling); return true;
  }
  var api = (window.harumiLinux && typeof window.harumiLinux === 'object') ? window.harumiLinux : {};
  api.addApp = function (a) {
    if (!a || typeof a.id !== 'string' || typeof a.run !== 'function' || !/^[a-z0-9_-]{1,32}$/.test(a.id) || app(a.id)) return false;
    APPS.push({ id: a.id, label: String(a.label || a.id), icon: a.icon || 'ck-apps', img: /^[a-z]{2,20}$/.test(a.img || '') ? a.img : undefined, run: a.run });
    if (grid) renderDrawer();
    if (dockApps) renderDock();
    return true;
  };
  api.addSettingsSection = function (title, element) {
    if (!element || !element.nodeType) return false;
    var sec = el('section', 'hl-settings-extra'); sec.setAttribute('aria-label', String(title || ''));
    if (title) sec.appendChild(el('h3', '', String(title)));
    sec.appendChild(element);
    if (!placeSection(sec)) { document.addEventListener('DOMContentLoaded', function () { placeSection(sec); }); }
    extraSections.push(sec); return true;
  };
  window.harumiLinux = api;

  function start() {
    document.body.classList.add('hl-os');
    var q = $('question');
    if (q) q.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.defaultPrevented) { e.preventDefault(); var b = $('send-question'); if (b && !b.disabled) b.click(); } });
    buildDock(); buildDrawer();
    var tries = 0;
    (function waitMap() {
      if (keepMap()) { buildCar(); buildCards(); buildStatus(); hookGps(); watchOverlays(); pollStatus(); setInterval(pollStatus, 5000); return; }
      if (++tries < 50) setTimeout(waitMap, 200);
    })();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

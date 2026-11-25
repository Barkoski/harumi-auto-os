/* Harumi OS: mini-player, alertas no painel do carro, busca nos Ajustes, historico de viagens e postos na rota.
   Usa os eventos 'hl-status' e 'hl-fix' do linux-layout.js. Camada so do Linux. */
(function () {
  'use strict';
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  var NS = 'http://www.w3.org/2000/svg';
  function icon(id) {
    var svg = document.createElementNS(NS, 'svg'), use = document.createElementNS(NS, 'use');
    svg.setAttribute('class', 'ck-ico'); svg.setAttribute('aria-hidden', 'true'); svg.setAttribute('focusable', 'false');
    use.setAttribute('href', '#' + id); svg.appendChild(use); return svg;
  }
  function norm(s) { return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function notify(text) { var m = $('message'); if (!m) return; m.textContent = text; m.hidden = false; clearTimeout(notify.t); notify.t = setTimeout(function () { m.hidden = true; }, 4500); }

  /* ---------------- Mini-player (acima do dock, a esquerda) ---------------- */
  var mini = {}, ytTitle = '', spotify = null;
  function buildMini() {
    var box = el('section', 'ck-card'); box.id = 'hl-mini'; box.setAttribute('aria-label', 'Mini-player');
    var text = el('div', 'hl-mini-text');
    mini.source = el('span', 'hl-kicker', 'Música');
    mini.title = el('strong', '', 'Nada tocando');
    text.appendChild(mini.source); text.appendChild(mini.title);
    var btns = el('div', 'hl-mini-btns');
    [['prev', 'ck-prev', 'Anterior'], ['toggle', 'ck-play', 'Tocar ou pausar'], ['next', 'ck-next', 'Próxima']].forEach(function (b) {
      var x = el('button', 'hl-mini-btn'); x.type = 'button'; x.setAttribute('aria-label', b[2]); x.appendChild(icon(b[1]));
      x.addEventListener('click', function () { media(b[0]); }); btns.appendChild(x);
    });
    box.appendChild(text); box.appendChild(btns);
    document.body.appendChild(box);
    if (window.harumiHost && window.harumiHost.onEmbedTitle) window.harumiHost.onEmbedTitle(function (t) { ytTitle = t.replace(/\s*-\s*YouTube\s*$/, ''); renderMini(); });
  }
  function source() { var e = window.harumiEmbed; return e && e.current && e.current() === 'youtube' ? 'youtube' : 'spotify'; }
  function renderMini() {
    if (!mini.title) return;
    if (source() === 'youtube') { mini.source.textContent = 'YouTube'; mini.title.textContent = ytTitle || 'YouTube'; return; }
    mini.source.textContent = 'Spotify · Harumi' + (spotify && spotify.state === 'paused' ? ' · pausado' : '');
    mini.title.textContent = spotify && spotify.name ? spotify.name + (spotify.artists ? ' — ' + spotify.artists : '') : 'Nada tocando';
  }
  function media(cmd) {
    if (source() === 'youtube' && window.harumiHost && window.harumiHost.embedMedia) { window.harumiHost.embedMedia(cmd); return; }
    notify('Controles do Spotify pela Harumi chegam com o Client ID. Por enquanto, use o app Spotify no dispositivo “Harumi”.');
  }
  var prevSpotify = window.harumiSpotifyNow;
  window.harumiSpotifyNow = function (s) { if (prevSpotify) prevSpotify(s); spotify = s; renderMini(); };

  /* ---------------- Alertas no painel do carro ---------------- */
  var alerts, lastFixMs = 0;
  function buildAlerts() {
    var car = $('hl-car'); if (!car) return;
    alerts = el('ul', 'hl-alerts'); alerts.setAttribute('role', 'status'); alerts.setAttribute('aria-label', 'Avisos');
    car.appendChild(alerts);
  }
  function renderAlerts(s) {
    if (!alerts) return;
    var list = [];
    if (s.tempC != null && s.tempC >= 80) list.push(['warn', 'Placa quente: ' + s.tempC + ' °C. Verifique a ventilação.']);
    if (s.online === false) list.push(['info', 'Sem Internet: mapa e busca do Brasil seguem offline.']);
    if (s.llm === false) list.push(['info', 'IA local carregando ou parada.']);
    if (s.mapOffline === false) list.push(['info', 'Mapa offline ainda não instalado.']);
    if (!lastFixMs || Date.now() - lastFixMs > 30000) list.push(['info', 'Sem sinal de GPS.']);
    alerts.textContent = '';
    list.forEach(function (a) { var li = el('li', 'hl-alert ' + a[0], a[1]); alerts.appendChild(li); });
    alerts.hidden = !list.length;
  }

  /* ---------------- Busca nos Ajustes ---------------- */
  function buildSettingsSearch() {
    var screen = $('settings'), list = screen && screen.querySelector('.hu-row-list'); if (!list) return;
    var form = el('form', 'hl-settings-search'); form.setAttribute('role', 'search');
    var input = el('input'); input.type = 'search'; input.placeholder = 'Buscar ajuste (volume, Wi-Fi, voz…)'; input.setAttribute('aria-label', 'Buscar ajuste');
    var empty = el('p', 'hl-settings-empty', 'Nenhum ajuste com esse nome.'); empty.hidden = true;
    form.appendChild(input); form.addEventListener('submit', function (e) { e.preventDefault(); });
    list.parentNode.insertBefore(form, list); list.parentNode.insertBefore(empty, list.nextSibling);
    input.addEventListener('input', function () {
      var q = norm(input.value).trim(), shown = 0;
      [].forEach.call(list.querySelectorAll('.hu-row'), function (row) { var ok = !q || norm(row.textContent).indexOf(q) >= 0; row.hidden = !ok; if (ok) shown++; });
      empty.hidden = shown > 0;
    });
  }

  /* ---------------- Historico de viagens (guardado no aparelho) ---------------- */
  var TRIPS_KEY = 'hl.trips.v1', NEW_TRIP_GAP_MS = 10 * 60 * 1000, trips, tripRows = {};
  function loadTrips() { try { var t = JSON.parse(localStorage.getItem(TRIPS_KEY)); if (t && Array.isArray(t.list)) return t; } catch (e) { /* sem storage */ } return { totalKm: 0, list: [] }; }
  function saveTrips() { try { localStorage.setItem(TRIPS_KEY, JSON.stringify(trips)); } catch (e) { /* sem storage */ } }
  var lastFix = null, lastSave = 0;
  function onFix(f) {
    if (!f || !Number.isFinite(f.lat) || !Number.isFinite(f.lon)) return;
    var now = Date.now(); lastFixMs = now;
    var cur = trips.list[trips.list.length - 1];
    if (!cur || now - cur.end > NEW_TRIP_GAP_MS) { cur = { start: now, end: now, km: 0 }; trips.list.push(cur); if (trips.list.length > 50) trips.list.shift(); lastFix = null; }
    if (lastFix) {
      var dy = (f.lat - lastFix.lat) * 111.0, dx = (f.lon - lastFix.lon) * 111.0 * Math.cos(f.lat * Math.PI / 180), d = Math.sqrt(dx * dx + dy * dy);
      if (d < 1) { cur.km += d; trips.totalKm += d; }
    }
    lastFix = f; cur.end = now;
    if (now - lastSave > 30000) { saveTrips(); lastSave = now; }
    renderTrips();
  }
  function buildTripHistory() {
    var dl = document.querySelector('#hl-cards .hl-trip'); if (!dl) return;
    function row(label) { var dt = el('dt', '', label), dd = el('dd', '', '—'); dl.appendChild(dt); dl.appendChild(dd); return dd; }
    tripRows.today = row('Hoje'); tripRows.last = row('Última'); tripRows.total = row('Total');
    renderTrips();
  }
  function renderTrips() {
    if (!tripRows.today) return;
    var start = new Date(); start.setHours(0, 0, 0, 0);
    var today = trips.list.filter(function (t) { return t.end >= start.getTime(); }).reduce(function (a, t) { return a + t.km; }, 0);
    var done = trips.list.length > 1 ? trips.list[trips.list.length - 2] : null;
    tripRows.today.textContent = trips.list.length ? today.toFixed(1) + ' km' : '—';
    tripRows.last.textContent = done ? done.km.toFixed(1) + ' km' : '—';
    tripRows.total.textContent = trips.totalKm ? trips.totalKm.toFixed(0) + ' km' : '—';
  }
  window.addEventListener('pagehide', function () { saveTrips(); });

  /* ---------------- Postos no caminho (rota longa, indice offline) ---------------- */
  var fuelCard, fuelList, routeSeen = '';
  function buildFuel() {
    var left = document.querySelector('#road-map .ck-left'); if (!left) return;
    fuelCard = el('section', 'ck-card'); fuelCard.id = 'hl-fuel'; fuelCard.hidden = true; fuelCard.setAttribute('aria-label', 'Postos no caminho');
    fuelCard.appendChild(el('strong', '', 'Postos no caminho'));
    fuelCard.appendChild(el('span', 'hl-kicker', 'Sugestão a cada ~150 km, do mapa offline. Confira se está aberto.'));
    fuelList = el('ol', 'hl-fuel-list'); fuelCard.appendChild(fuelList);
    var plan = $('route-result'); if (plan && plan.parentNode === left) left.insertBefore(fuelCard, plan.nextSibling); else left.appendChild(fuelCard);
    var watch = $('route-result');
    if (watch) new MutationObserver(checkRoute).observe(watch, { attributes: true, childList: true, subtree: true, characterData: true });
  }
  function checkRoute() {
    var r = $('route-result'); if (!r) return;
    if (r.hidden) { fuelCard.hidden = true; routeSeen = ''; return; }
    var key = r.textContent; if (key === routeSeen) return; routeSeen = key;
    fetch('/linux/fuel-stops').then(function (x) { return x.ok ? x.json() : { stops: [] }; }).then(function (d) {
      var stops = (d && d.stops) || []; fuelList.textContent = '';
      stops.forEach(function (p) {
        var li = el('li'); li.appendChild(el('b', '', 'km ' + p.km)); li.appendChild(el('span', '', ' ' + p.name + (p.city ? ' — ' + p.city + (p.uf ? '/' + p.uf : '') : '')));
        fuelList.appendChild(li);
      });
      fuelCard.hidden = !stops.length;
    }).catch(function () { fuelCard.hidden = true; });
  }

  function start() {
    trips = loadTrips();
    buildMini(); renderMini();
    var tries = 0;
    (function wait() {
      if ($('hl-car') && document.querySelector('#hl-cards .hl-trip')) { buildAlerts(); buildTripHistory(); buildSettingsSearch(); buildFuel(); return; }
      if (++tries < 60) setTimeout(wait, 250);
    })();
    window.addEventListener('hl-status', function (e) { renderAlerts(e.detail || {}); renderMini(); });
    window.addEventListener('hl-fix', function (e) { onFix(e.detail); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

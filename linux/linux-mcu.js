/* Harumi OS: arranjo de central multimidia (barra inferior carro | apps | volume, cards de musica e "Navegar"
   com Casa/Trabalho, vista do carro e perfil no topo). Layout inspirado no kit "Tesla Dashboard UI Component Library"
   de Nami (CC BY 4.0, figma.com/community/file/1382192547846546595), adaptado a identidade da Harumi: sem marcas
   nem desenhos do original; o carro e um Impreza perua desenhado aqui. */
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
  function notify(text) { var m = $('message'); if (!m) return; m.textContent = text; m.hidden = false; clearTimeout(notify.t); notify.t = setTimeout(function () { m.hidden = true; }, 4500); }
  function closePanels() { if (window.harumiShell && window.harumiShell.closeAll) window.harumiShell.closeAll(); var d = $('hl-drawer'); if (d && !d.hidden) d.hidden = true; }

  /* ---------------- Favoritos Casa / Trabalho ---------------- */
  var FAV_KEY = 'hl.favorites.v1';
  function favs() { try { return JSON.parse(localStorage.getItem(FAV_KEY)) || {}; } catch (e) { return {}; } }
  function saveFav(k, v) { var f = favs(); if (v) f[k] = v; else delete f[k]; try { localStorage.setItem(FAV_KEY, JSON.stringify(f)); } catch (e) { /* sem storage */ } }

  var navCard, favEdit, favInput, favKey = null;
  function buildNavCard(row) {
    navCard = el('section', 'ck-card hl-navcard'); navCard.setAttribute('aria-label', 'Navegar');
    var search = el('button', 'hl-navcard-search'); search.type = 'button';
    search.appendChild(icon('ck-search')); search.appendChild(el('span', '', 'Navegar'));
    // focus() nao dispara focusin se o campo ja tinha o foco (ex.: depois de "Fechar teclado"): abre o teclado direto
    search.addEventListener('click', function () { closePanels(); var d = $('nav-dest'); if (d) { d.focus(); if (d.select) d.select(); /* busca nova: o que for digitado substitui o texto antigo */ if (window.harumiKeyboard) window.harumiKeyboard.open(d, false); } });
    var favRow = el('div', 'hl-navcard-favs');
    [['casa', 'Casa', 'ck-home'], ['trabalho', 'Trabalho', 'ck-car']].forEach(function (f) {
      var pair = el('div', 'hl-fav-pair');
      var b = el('button', 'hl-fav'); b.type = 'button'; b.dataset.fav = f[0];
      b.appendChild(icon(f[2])); b.appendChild(el('span', '', f[1]));
      b.addEventListener('click', function () { goFav(f[0], f[1]); });
      // toque longo: trocar o endereco salvo
      var t = null;
      b.addEventListener('pointerdown', function () { t = setTimeout(function () { t = 'long'; editFav(f[0], f[1]); }, 700); });
      b.addEventListener('pointerup', function (e) { if (t === 'long') { e.preventDefault(); } clearTimeout(t); });
      b.addEventListener('pointerleave', function () { clearTimeout(t); });
      var pen = el('button', 'hl-fav-pen', '✎'); pen.type = 'button'; pen.setAttribute('aria-label', 'Editar endereço de ' + f[1]);
      pen.addEventListener('click', function () { editFav(f[0], f[1]); });
      pair.appendChild(b); pair.appendChild(pen); favRow.appendChild(pair);
    });
    favEdit = el('form', 'hl-fav-edit'); favEdit.hidden = true;
    favInput = el('input'); favInput.type = 'text'; favInput.setAttribute('aria-label', 'Endereço do favorito');
    var save = el('button', 'hl-fav-save', 'Salvar'); save.type = 'submit';
    var clear = el('button', 'hl-fav-clear', 'Apagar'); clear.type = 'button';
    clear.addEventListener('click', function () { saveFav(favKey, null); favEdit.hidden = true; notify('Favorito apagado.'); });
    favEdit.appendChild(favInput); favEdit.appendChild(save); favEdit.appendChild(clear);
    favEdit.addEventListener('submit', function (e) {
      e.preventDefault(); var v = favInput.value.trim().slice(0, 160);
      if (v.length < 3) { notify('Digite um endereço ou lugar.'); return; }
      saveFav(favKey, v); favEdit.hidden = true; favInput.blur(); notify('Favorito salvo: ' + v);
    });
    navCard.appendChild(search); navCard.appendChild(favRow); navCard.appendChild(favEdit);
    row.appendChild(navCard);
  }
  function goFav(key, name) {
    var v = favs()[key];
    if (!v) { editFav(key, name); return; }
    closePanels();
    if (window.harumiRoadMap && window.harumiRoadMap.navigateTo) window.harumiRoadMap.navigateTo(v);
  }
  function editFav(key, name) {
    favKey = key; favEdit.hidden = false;
    favInput.placeholder = 'Endereço de ' + name + ' (ex.: Rua X, 100, Londrina)';
    favInput.value = favs()[key] || '';
    favInput.focus();
  }

  /* ---------------- Barra inferior: carro | apps | volume ---------------- */
  var carView;
  function restyleDock() {
    var dock = $('hl-dock'); if (!dock) return false;
    dock.classList.add('hl-mcu');
    var carBtn = el('button', 'hl-dock-car'); carBtn.type = 'button'; carBtn.setAttribute('aria-label', 'Vista do carro');
    carBtn.appendChild(icon('ck-car'));
    carBtn.addEventListener('click', function () { toggleCarView(); });
    dock.insertBefore(carBtn, dock.firstChild);
    [].forEach.call(dock.querySelectorAll('.hl-dock-apps button, #hl-dock-drawer'), function (b) {
      var s = b.querySelector('span'); if (s && !b.getAttribute('aria-label')) b.setAttribute('aria-label', s.textContent);
    });
    // os botoes de apps sao recriados ao editar o dock: mantem o rotulo acessivel
    new MutationObserver(function () {
      [].forEach.call(dock.querySelectorAll('.hl-dock-apps button'), function (b) { var s = b.querySelector('span'); if (s) b.setAttribute('aria-label', s.textContent); });
    }).observe(dock.querySelector('.hl-dock-apps'), { childList: true });
    return true;
  }

  /* ---------------- Painel do carro: velocimetro + blocos de estado ---------------- */
  var SPEED_MAX = 200, ARC = 270, gauge = {}, tiles = {};
  function arcPath(cx, cy, r, a0, a1) {
    function pt(a) { var t = (a - 90) * Math.PI / 180; return [cx + r * Math.cos(t), cy + r * Math.sin(t)]; }
    var p0 = pt(a0), p1 = pt(a1), large = a1 - a0 > 180 ? 1 : 0;
    return 'M' + p0[0].toFixed(1) + ' ' + p0[1].toFixed(1) + ' A' + r + ' ' + r + ' 0 ' + large + ' 1 ' + p1[0].toFixed(1) + ' ' + p1[1].toFixed(1);
  }
  function svgEl(tag, attrs) { var e = document.createElementNS(NS, tag); Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); }); return e; }
  function buildGauge() {
    var s = svgEl('svg', { viewBox: '0 0 300 300', 'class': 'hl-gauge', role: 'img', 'aria-label': 'Velocidade' });
    var start = -ARC / 2, end = ARC / 2;
    s.appendChild(svgEl('path', { d: arcPath(150, 150, 120, start, end), 'class': 'track' }));
    gauge.bar = svgEl('path', { d: arcPath(150, 150, 120, start, start + 0.1), 'class': 'bar' });
    s.appendChild(gauge.bar);
    for (var v = 0; v <= SPEED_MAX; v += 20) {
      var ang = start + ARC * v / SPEED_MAX, t = (ang - 90) * Math.PI / 180, big = v % 40 === 0;
      s.appendChild(svgEl('line', { x1: 150 + 100 * Math.cos(t), y1: 150 + 100 * Math.sin(t), x2: 150 + (big ? 90 : 95) * Math.cos(t), y2: 150 + (big ? 90 : 95) * Math.sin(t), 'class': 'tick' }));
      if (big) { var tx = svgEl('text', { x: 150 + 76 * Math.cos(t), y: 150 + 76 * Math.sin(t) + 5, 'class': 'num' }); tx.textContent = v; s.appendChild(tx); }
    }
    gauge.value = svgEl('text', { x: 150, y: 160, 'class': 'value' }); gauge.value.textContent = '—'; s.appendChild(gauge.value);
    var u = svgEl('text', { x: 150, y: 192, 'class': 'unit' }); u.textContent = 'km/h'; s.appendChild(u);
    gauge.note = svgEl('text', { x: 150, y: 250, 'class': 'unit' }); gauge.note.textContent = 'sem GPS'; s.appendChild(gauge.note);
    return s;
  }
  function setSpeed(kmh) {
    var v = Math.max(0, Math.min(SPEED_MAX, kmh)), start = -ARC / 2;
    gauge.bar.setAttribute('d', arcPath(150, 150, 120, start, start + Math.max(0.1, ARC * v / SPEED_MAX)));
    gauge.value.textContent = Math.round(kmh); gauge.note.textContent = '';
  }
  function tile(grid, key, ico, label, value) {
    var t = el('div', 'hl-tile2'); var i = el('span', 'hl-tile2-ico'); i.appendChild(icon(ico)); t.appendChild(i);
    var tx = el('div', 'hl-tile2-text'); tx.appendChild(el('span', '', label)); var v = el('b', '', value); tx.appendChild(v); t.appendChild(tx);
    grid.appendChild(t); tiles[key] = { box: t, value: v };
  }
  function setTile(key, value, state) { var t = tiles[key]; if (!t) return; t.value.textContent = value; t.box.dataset.state = state || ''; }
  function buildCarView() {
    carView = el('section', 'hl-carview'); carView.id = 'hl-carview'; carView.hidden = true; carView.setAttribute('aria-label', 'Painel do carro');
    var head = el('div', 'hl-carview-head');
    head.appendChild(el('strong', '', 'Subaru Impreza perua 1993 · EJ18'));
    var close = el('button', 'hl-carview-close'); close.type = 'button'; close.setAttribute('aria-label', 'Fechar painel do carro'); close.appendChild(icon('ck-close'));
    close.addEventListener('click', function () { toggleCarView(false); });
    head.appendChild(close);
    var stage = el('div', 'hl-carview-stage hl-dash');
    stage.appendChild(buildGauge());
    var grid = el('div', 'hl-tiles2');
    tile(grid, 'motor', 'ck-car', 'Motor', 'aguardando scanner');
    tile(grid, 'gps', 'ck-compass', 'GPS', 'sem sinal');
    tile(grid, 'net', 'ck-wifi', 'Internet', '—');
    tile(grid, 'ia', 'ck-harumi', 'IA local', '—');
    tile(grid, 'camera', 'ck-camera', 'Câmera de ré', 'não instalada');
    tile(grid, 'placa', 'ck-settings', 'Central', '—');
    stage.appendChild(grid);
    carView.appendChild(head); carView.appendChild(stage);
    document.body.appendChild(carView);
    setTile('motor', 'aguardando scanner', 'wait'); setTile('camera', 'não instalada', 'wait'); setTile('gps', 'sem sinal', 'wait');
    window.addEventListener('hl-status', function (e) {
      var s = e.detail || {};
      setTile('placa', s.tempC != null ? s.tempC + ' °C' : '—', s.tempC >= 80 ? 'warn' : 'ok');
      setTile('net', s.online === false ? 'offline · mapa local' : s.online ? 'conectada' : '—', s.online === false ? 'wait' : 'ok');
      setTile('ia', s.llm === false ? 'carregando' : s.llm ? 'pronta · Qwen 2B' : '—', s.llm === false ? 'wait' : 'ok');
    });
    window.addEventListener('hl-fix', function (e) {
      var f = e.detail || {}, v = Number.isFinite(f.speedMps) ? f.speedMps : f.speed;
      if (Number.isFinite(v)) setSpeed(v * 3.6);
      setTile('gps', 'com sinal', 'ok');
    });
  }
  function toggleCarView(force) {
    var on = typeof force === 'boolean' ? force : carView.hidden;
    if (on) closePanels();
    carView.hidden = !on;
    var b = document.querySelector('#hl-dock .hl-dock-car'); if (b) b.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  /* ---------------- Topo: perfil ---------------- */
  function buildProfile() {
    var top = document.querySelector('#road-map .ck-top'); if (!top) return;
    var p = el('span', 'hl-profile'); p.appendChild(icon('ck-harumi')); p.appendChild(el('span', '', 'Lucas'));
    top.appendChild(p);
  }

  /* ---------------- Navegacao em andamento: botao Encerrar no lugar do card Navegar ---------------- */
  function watchNav(row) {
    var rm = $('road-map'); if (!rm) return;
    var stop = el('button', 'hl-stop'); stop.type = 'button'; stop.appendChild(icon('ck-close')); stop.appendChild(el('span', '', 'Encerrar navegação'));
    stop.addEventListener('click', function () { var b = $('nav-stop'); if (b) b.click(); });
    row.appendChild(stop);
    // Sem GPS a navegacao fica esperando o sinal: oferece ver a rota a partir de Casa.
    var fromHome = el('button', 'hl-fromhome'); fromHome.type = 'button'; fromHome.appendChild(icon('ck-home'));
    var fhText = el('span', '', 'Ver rota a partir de Casa'); fromHome.appendChild(fhText);
    fromHome.addEventListener('click', function () {
      var casa = favs().casa, dest = ($('nav-street') && $('nav-street').textContent.trim()) || '';
      if (!casa) { editFav('casa', 'Casa'); notify('Salve o endereço de Casa para ver a rota sem GPS.'); return; }
      if (!dest || dest === '—') { notify('Destino não identificado. Busque de novo.'); return; }
      var b = $('nav-stop'); if (b) b.click();
      setTimeout(function () { if (window.harumiRoadMap && window.harumiRoadMap.plan) window.harumiRoadMap.plan(casa, dest); }, 300);
    });
    row.appendChild(fromHome);
    var gpsAt = 0;
    window.addEventListener('hl-fix', function () { gpsAt = Date.now(); sync(); });
    function sync() {
      var on = rm.classList.contains('nav-on');
      document.body.classList.toggle('hl-nav-on', on);
      document.body.classList.toggle('hl-nav-nogps', on && Date.now() - gpsAt > 15000);
    }
    new MutationObserver(sync).observe(rm, { attributes: true, attributeFilter: ['class'] }); sync();
  }

  function start() {
    var tries = 0;
    (function wait() {
      var mini = $('hl-mini');
      if ($('hl-dock') && mini && document.querySelector('#road-map .ck-top')) {
        var row = el('div'); row.id = 'hl-bottom-cards';
        document.body.appendChild(row);
        mini.classList.add('hl-musiccard'); row.appendChild(mini);
        buildNavCard(row);
        restyleDock(); buildCarView(); buildProfile(); watchNav(row);
        return;
      }
      if (++tries < 60) setTimeout(wait, 250);
    })();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

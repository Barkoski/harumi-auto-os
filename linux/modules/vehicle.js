/* Harumi OS: painel lateral no estilo das centrais modernas (velocidade grande, proximidade, motor, bateria, pneus)
   e a aba do carro com todos os modulos de hardware. Dados reais de /linux/vehicle (plugins/vehicle.py),
   dos eventos hl-fix (GPS) e hl-status (placa, internet, IA). Sem dado, mostra "—" e o que falta instalar. */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function icon(id) {
    var s = document.createElementNS(NS, 'svg'), u = document.createElementNS(NS, 'use');
    s.setAttribute('class', 'ck-ico'); s.setAttribute('aria-hidden', 'true'); s.setAttribute('focusable', 'false');
    u.setAttribute('href', '#' + id); s.appendChild(u); return s;
  }
  function svg(tag, attrs) { var e = document.createElementNS(NS, tag); Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); }); return e; }
  function post(path, body) {
    return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); });
  }
  function notify(t) { var m = document.getElementById('message'); if (m) { m.textContent = t; m.hidden = false; setTimeout(function () { m.hidden = true; }, 4000); } }

  // Icones proprios (mesmo traco dos icones ck-*): termometro, conta-giros, bateria, pneu, gravacao, radar.
  var ICONS = {
    'hl-temp': '<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/><path d="M12 9v7"/>',
    'hl-rpm': '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/>',
    'hl-battery': '<rect x="3" y="7" width="18" height="12" rx="2"/><path d="M7 7V5h3v2M14 7V5h3v2M7 13h4M15 11v4M13 13h4"/>',
    'hl-tire': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 4v5M12 15v5M4 12h5M15 12h5"/>',
    'hl-rec': '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3"/><circle cx="9.5" cy="12" r="2" fill="currentColor"/>',
    'hl-radar': '<path d="M5 19a10 10 0 0 1 0-14M8 16a6 6 0 0 1 0-8"/><path d="M19 19a10 10 0 0 0 0-14M16 16a6 6 0 0 0 0-8"/><circle cx="12" cy="12" r="1.5"/>'
  };
  function sprite() {
    var s = svg('svg', { 'aria-hidden': 'true', focusable: 'false' }); s.setAttribute('hidden', '');
    Object.keys(ICONS).forEach(function (id) {
      var sym = svg('symbol', { id: id, viewBox: '0 0 24 24' });
      var g = svg('g', { fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
      // conteudo fixo deste arquivo (nao vem de fora): monta os elementos a partir do texto acima
      var tmp = new DOMParser().parseFromString('<svg xmlns="' + NS + '">' + ICONS[id] + '</svg>', 'image/svg+xml').documentElement;
      // importNode COPIA o no; por isso percorre uma lista fixa (um while em tmp.firstChild nunca terminaria).
      Array.prototype.slice.call(tmp.childNodes).forEach(function (n) { g.appendChild(document.importNode(n, true)); });
      sym.appendChild(g); s.appendChild(sym);
    });
    document.body.appendChild(s);
  }

  var V = null, fixAt = 0, fixSrc = '', status = {};
  var pane, P = {}, grid, G = {};

  /* ---------- Painel lateral ---------- */
  function buildPane() {
    pane = el('aside', 'hl-pane'); pane.id = 'hl-pane'; pane.setAttribute('aria-label', 'Painel do motorista');
    var head = el('div', 'hl-pane-head');
    head.appendChild(el('strong', '', 'Subaru Impreza')); head.appendChild(el('span', '', '1993 · EJ18'));
    pane.appendChild(head);

    var hero = el('div', 'hl-pane-speed');
    P.speed = el('b', '', '—'); hero.appendChild(P.speed);
    var u = el('div', 'hl-pane-unit'); u.appendChild(el('span', '', 'km/h')); P.src = el('span', 'hl-pane-src', 'sem GPS'); u.appendChild(P.src);
    hero.appendChild(u); pane.appendChild(hero);

    pane.appendChild(buildProx());

    var tiles = el('div', 'hl-pane-tiles');
    P.agua = qtile(tiles, 'hl-temp', 'Água');
    P.rpm = qtile(tiles, 'hl-rpm', 'Rotação');
    P.bat = qtile(tiles, 'hl-battery', 'Bateria');
    P.pneus = qtile(tiles, 'hl-tire', 'Pneus');
    pane.appendChild(tiles);

    var chips = el('div', 'hl-pane-chips');
    P.gps = chip(chips, 'ck-compass', 'GPS'); P.net = chip(chips, 'ck-wifi', 'Internet');
    P.ia = chip(chips, 'ck-harumi', 'IA'); P.placa = chip(chips, 'ck-settings', 'Placa');
    pane.appendChild(chips);

    var open = el('button', 'hl-pane-open'); open.type = 'button';
    open.appendChild(icon('ck-car')); open.appendChild(el('span', '', 'Painel do carro'));
    open.addEventListener('click', function () { var b = document.querySelector('.hl-dock-car'); if (b) b.click(); });
    pane.appendChild(open);
    document.body.appendChild(pane);
  }
  function qtile(box, ico, label) {
    var t = el('div', 'hl-qtile'); var i = el('span', 'hl-qtile-ico'); i.appendChild(icon(ico)); t.appendChild(i);
    var tx = el('div', 'hl-qtile-text'); tx.appendChild(el('span', '', label)); var v = el('b', '', '—'); tx.appendChild(v); t.appendChild(tx);
    box.appendChild(t); return { box: t, v: v };
  }
  function chip(box, ico, label) {
    var c = el('span', 'hl-chip'); c.appendChild(icon(ico)); var t = el('span', '', label); c.appendChild(t);
    box.appendChild(c); return { box: c, t: t, label: label };
  }
  function setQ(q, text, state) { q.v.textContent = text; q.box.dataset.state = state || ''; }
  var COMPACT = window.matchMedia('(min-width:900px) and (max-width:1279px), (min-width:900px) and (max-height:760px)');
  function setChip(c, text, state) {
    // na tela pequena o icone ja diz o que e: mostra so o valor (o leitor de tela recebe o texto completo)
    c.t.textContent = COMPACT.matches ? text : c.label + ' · ' + text;
    c.box.setAttribute('aria-label', c.label + ': ' + text); c.box.dataset.state = state || '';
  }

  // Vista de cima (esquematica) com 4 setores de proximidade: frente, tras, esquerda, direita.
  function buildProx() {
    var wrap = el('div', 'hl-prox');
    var s = svg('svg', { viewBox: '0 0 200 240', 'class': 'hl-prox-svg', role: 'img', 'aria-label': 'Sensores de proximidade' });
    P.zones = {
      frente: svg('path', { d: 'M60 52 Q100 18 140 52', 'class': 'zone' }),
      tras: svg('path', { d: 'M60 188 Q100 222 140 188', 'class': 'zone' }),
      esq: svg('path', { d: 'M48 70 Q30 120 48 170', 'class': 'zone' }),
      dir: svg('path', { d: 'M152 70 Q170 120 152 170', 'class': 'zone' })
    };
    Object.keys(P.zones).forEach(function (k) { s.appendChild(P.zones[k]); });
    s.appendChild(svg('rect', { x: 66, y: 58, width: 68, height: 124, rx: 22, 'class': 'body' }));
    s.appendChild(svg('rect', { x: 74, y: 84, width: 52, height: 26, rx: 8, 'class': 'glass' }));
    s.appendChild(svg('rect', { x: 74, y: 140, width: 52, height: 22, rx: 8, 'class': 'glass' }));
    wrap.appendChild(s);
    P.proxNote = el('p', 'hl-prox-note', 'Proximidade: sensor não instalado');
    wrap.appendChild(P.proxNote);
    return wrap;
  }

  /* ---------- Aba do carro (modulos) ---------- */
  function section(title, ico) {
    var c = el('section', 'hl-vcard'); var h = el('h3'); h.appendChild(icon(ico)); h.appendChild(el('span', '', title));
    c.appendChild(h); var body = el('div', 'hl-vbody'); c.appendChild(body); grid.appendChild(c); return body;
  }
  function row(body, label) {
    var r = el('div', 'hl-vrow'); r.appendChild(el('span', '', label)); var v = el('b', '', '—'); r.appendChild(v); body.appendChild(r); return v;
  }
  function note(body) { var n = el('p', 'hl-vnote'); body.appendChild(n); return n; }
  function portSelect(body, key, label) {
    var lab = el('label', 'hl-vsel'); lab.appendChild(el('span', '', label));
    var s = el('select'); s.addEventListener('change', function () {
      post('/linux/vehicle-set', { chave: key, valor: s.value || null }).then(function (j) { if (j.ok) render(j); else notify(j.erro || 'Erro'); });
    });
    lab.appendChild(s); body.appendChild(lab); return s;
  }
  function fillPorts(s, ports, cur) {
    s.textContent = '';
    var o = el('option', '', ports.length ? 'Escolher porta…' : 'Nenhuma porta USB-serial'); o.value = ''; s.appendChild(o);
    ports.forEach(function (p) { var op = el('option', '', p.id + ' (' + p.dev + ')'); op.value = p.id; if (p.id === cur) op.selected = true; s.appendChild(op); });
    s.disabled = !ports.length;
  }
  function buildGrid(carView) {
    var stage = carView.querySelector('.hl-carview-stage'); if (stage) stage.hidden = true;
    grid = el('div', 'hl-vgrid'); carView.appendChild(grid);

    var m = section('Motor (ECU · SSM1)', 'hl-temp');
    G.rpm = row(m, 'Rotação'); G.agua = row(m, 'Temperatura da água'); G.kmhEcu = row(m, 'Velocidade (ECU)');
    G.ssmSel = portSelect(m, 'ssm1_port', 'Cabo SSM1'); G.mNote = note(m);

    var b = section('Bateria e alternador', 'hl-battery');
    G.volts = row(b, 'Tensão'); G.batSensor = row(b, 'Sensor'); G.bNote = note(b);

    var t = section('Pneus (Bluetooth)', 'hl-tire');
    G.pneus = {};
    [['de', 'Dianteiro esq.'], ['dd', 'Dianteiro dir.'], ['te', 'Traseiro esq.'], ['td', 'Traseiro dir.']].forEach(function (p) { G.pneus[p[0]] = row(t, p[1]); });
    G.tNote = note(t);

    var c = section('Câmeras (ré, 360°, dashcam)', 'ck-camera');
    G.camList = el('div', 'hl-vcams'); c.appendChild(G.camList); G.cNote = note(c);

    var d = section('Dashcam', 'hl-rec');
    G.dState = row(d, 'Estado'); G.dUse = row(d, 'Espaço usado');
    var dbtn = el('button', 'hl-vbtn'); dbtn.type = 'button'; dbtn.textContent = 'Ligar gravação'; G.dBtn = dbtn;
    dbtn.addEventListener('click', function () {
      var on = !(V && V.dashcam && V.dashcam.gravando);
      dbtn.disabled = true;
      post('/linux/vehicle-dashcam', { on: on }).then(function (j) { dbtn.disabled = false; if (j.ok) render(j); else notify(j.erro || 'Erro'); });
    });
    d.appendChild(dbtn); G.dNote = note(d);
    G.dNote.textContent = 'Grava em blocos de 1 minuto e apaga o mais antigo quando chega ao limite. Fica só na placa.';

    var p = section('Proximidade (radar / sensor de ré)', 'hl-radar');
    G.pState = row(p, 'Estado'); G.radarSel = portSelect(p, 'radar_port', 'Porta do sensor'); G.pNote = note(p);

    var mic = section('Microfone', 'ck-mic');
    G.micState = row(mic, 'Estado'); G.micList = note(mic);

    var sys = section('Sistema', 'ck-settings');
    G.sGps = row(sys, 'GPS'); G.sNet = row(sys, 'Internet'); G.sIa = row(sys, 'IA local'); G.sPlaca = row(sys, 'Temperatura da placa');
  }

  /* ---------- Atualizacao ---------- */
  var LABEL = { nao_instalado: 'não instalado', detectado: 'adaptador detectado', conectado: 'conectado', ok: 'ok',
    aguardando_sensores: 'aguardando sensores', sem_bluetooth: 'sem Bluetooth', baixa: 'baixa', alta: 'alta', erro: 'erro' };
  function lab(s) { return LABEL[s] || s || '—'; }
  function render(v) {
    V = v;
    try { window.dispatchEvent(new CustomEvent('hl-vehicle', { detail: v })); } catch (e) { /* sem ouvintes */ }
    var bat = v.bateria || {};
    setQ(P.agua, v.motor && v.motor.aguaC != null ? v.motor.aguaC + ' °C' : '—', v.motor && v.motor.aguaC != null ? 'ok' : 'wait');
    setQ(P.rpm, v.motor && v.motor.rpm != null ? v.motor.rpm + ' rpm' : '—', v.motor && v.motor.rpm != null ? 'ok' : 'wait');
    setQ(P.bat, bat.volts != null ? bat.volts.toFixed(1) + ' V' : '—', bat.volts == null ? 'wait' : bat.estado === 'ok' ? 'ok' : 'warn');
    setQ(P.pneus, v.pneus && v.pneus.pneus ? 'ok' : '—', v.pneus && v.pneus.pneus ? 'ok' : 'wait');
    var prox = v.proximidade || {};
    P.proxNote.textContent = prox.setores ? 'Proximidade: ativa' : prox.estado === 'nao_instalado' ? 'Proximidade: sensor não instalado' : 'Proximidade: ' + lab(prox.estado);
    if (!grid) return;
    var mo = v.motor || {};
    G.rpm.textContent = mo.rpm != null ? mo.rpm + ' rpm' : '—';
    G.agua.textContent = mo.aguaC != null ? mo.aguaC + ' °C' : '—';
    G.kmhEcu.textContent = mo.kmh != null ? mo.kmh + ' km/h' : '—';
    fillPorts(G.ssmSel, v.seriais || [], mo.porta); G.mNote.textContent = mo.nota || '';
    G.volts.textContent = bat.volts != null ? bat.volts.toFixed(2) + ' V (' + lab(bat.estado) + ')' : '—';
    G.batSensor.textContent = bat.sensor || 'não instalado';
    G.bNote.textContent = bat.volts == null ? 'Instale um medidor INA219/INA226 (I2C) ligado ao 12 V. Normal: 12,4–12,7 V desligado; 13,8–14,6 V com o motor ligado.' : (bat.detalhe || '');
    var pn = v.pneus || {};
    Object.keys(G.pneus).forEach(function (k) { G.pneus[k].textContent = pn.pneus && pn.pneus[k] != null ? pn.pneus[k] + ' psi' : '—'; });
    G.tNote.textContent = pn.nota || '';
    renderCams(v.cameras || []);
    var dc = v.dashcam || {};
    G.dState.textContent = dc.gravando ? 'gravando' : dc.erro ? dc.erro : 'parada';
    G.dUse.textContent = (dc.usadoMB || 0) + ' MB de ' + (dc.limiteGB || 8) + ' GB · ' + (dc.arquivos || 0) + ' blocos';
    G.dBtn.textContent = dc.gravando ? 'Parar gravação' : 'Ligar gravação';
    G.dBtn.setAttribute('aria-pressed', dc.gravando ? 'true' : 'false');
    G.pState.textContent = lab(prox.estado); fillPorts(G.radarSel, v.seriais || [], prox.porta); G.pNote.textContent = prox.nota || '';
    var mic = v.microfone || {};
    G.micState.textContent = lab(mic.estado);
    G.micList.textContent = mic.fontes && mic.fontes.length ? 'Entradas: ' + mic.fontes.join(', ') : 'Nenhum microfone encontrado. Sugestão: microfone de lapela USB no teto, perto do retrovisor.';
  }
  function renderCams(cams) {
    G.camList.textContent = '';
    if (!cams.length) { G.cNote.textContent = 'Nenhuma câmera USB encontrada. O kit 360° entra por uma placa de captura USB; a câmera de ré e a dashcam, por USB.'; return; }
    G.cNote.textContent = 'Escolha o papel de cada câmera.';
    cams.forEach(function (c) {
      var lab = el('label', 'hl-vsel'); lab.appendChild(el('span', '', c.nome + ' (' + c.dev + ')'));
      var s = el('select');
      [['nenhum', 'Sem uso'], ['re', 'Câmera de ré'], ['360', 'Visão 360°'], ['dashcam', 'Dashcam']].forEach(function (o) {
        var op = el('option', '', o[1]); op.value = o[0]; if (o[0] === c.papel) op.selected = true; s.appendChild(op);
      });
      s.addEventListener('change', function () {
        post('/linux/vehicle-set', { chave: 'cam_role', valor: { nome: c.nome, papel: s.value } }).then(function (j) { if (j.ok) render(j); else notify(j.erro || 'Erro'); });
      });
      lab.appendChild(s); G.camList.appendChild(lab);
    });
  }
  function renderStatus() {
    var gpsOk = Date.now() - fixAt < 15000;
    setChip(P.gps, gpsOk ? (fixSrc === 'simulacao' ? 'simulação' : 'ok') : 'sem sinal', gpsOk ? 'ok' : 'wait');
    setChip(P.net, status.online === false ? 'offline' : status.online ? 'ok' : '—', status.online ? 'ok' : 'wait');
    setChip(P.ia, status.llm === false ? 'carregando' : status.llm ? 'pronta' : '—', status.llm ? 'ok' : 'wait');
    setChip(P.placa, status.tempC != null ? status.tempC + ' °C' : '—', status.tempC >= 80 ? 'warn' : status.tempC != null ? 'ok' : 'wait');
    if (!gpsOk) { P.speed.textContent = '--'; P.speed.classList.add('none'); P.src.textContent = 'sem GPS'; }
    if (grid) {
      G.sGps.textContent = gpsOk ? (fixSrc === 'simulacao' ? 'simulação' : 'com sinal') : 'sem sinal';
      G.sNet.textContent = status.online === false ? 'offline · mapa local' : status.online ? 'conectada' : '—';
      G.sIa.textContent = status.llm === false ? 'carregando' : status.llm ? 'pronta · Qwen 2B' : '—';
      G.sPlaca.textContent = status.tempC != null ? status.tempC + ' °C' : '—';
    }
  }

  function poll() {
    var carOpen = grid && !document.getElementById('hl-carview').hidden;
    if (document.hidden) return;
    fetch('/linux/vehicle').then(function (r) { return r.json(); }).then(function (j) { if (j.ok) render(j); }).catch(function () {});
    return carOpen;
  }

  function start() {
    document.body.classList.add('hl-tesla');
    sprite(); buildPane();
    var tries = 0;
    (function waitCar() {
      var cv = document.getElementById('hl-carview');
      if (cv && !grid) { buildGrid(cv); if (V) render(V); renderStatus(); return; }
      if (++tries < 40) setTimeout(waitCar, 250);
    })();
    window.addEventListener('hl-fix', function (e) {
      var f = e.detail || {}, v = Number.isFinite(f.speedMps) ? f.speedMps : f.speed;
      fixAt = Date.now(); fixSrc = f.fonte || '';
      if (Number.isFinite(v)) { P.speed.textContent = Math.round(v * 3.6); P.speed.classList.remove('none'); }
      P.src.textContent = fixSrc === 'simulacao' ? 'GPS · simulação' : 'GPS';
      renderStatus();
    });
    window.addEventListener('hl-status', function (e) { status = e.detail || {}; renderStatus(); });
    renderStatus(); poll();
    // Tela de 7": o mini-player de musica vai para o pe do painel lateral (como nas centrais modernas) e volta
    // para o lugar original na tela grande.
    var mq = window.matchMedia('(min-width:900px) and (max-width:1279px), (min-width:900px) and (max-height:760px)');
    var home = null;
    function placeMini() {
      var m = document.getElementById('hl-mini'); if (!m) return false;
      // espera o linux-mcu.js colocar o player na fileira de baixo (#hl-bottom-cards) antes de guardar o lugar original
      if (!home && m.parentNode !== pane && (!m.parentNode || m.parentNode.id !== 'hl-bottom-cards')) return false;
      if (!home && m.parentNode !== pane) home = { parent: m.parentNode, next: m.nextSibling };
      if (mq.matches) { if (m.parentNode !== pane) pane.appendChild(m); }
      else if (home && m.parentNode === pane) home.parent.insertBefore(m, home.next && home.next.parentNode === home.parent ? home.next : null);
      return true;
    }
    (function waitMini(n) { if (!placeMini() && n < 40) setTimeout(function () { waitMini(n + 1); }, 250); })(0);
    if (mq.addEventListener) mq.addEventListener('change', placeMini);
    setInterval(function () { poll(); renderStatus(); }, 5000);
    // O mapa ocupa so a area a direita do painel: avisa o MapLibre que o tamanho mudou.
    setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 300);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

/* Garagem: app da gaveta com 3 abas (Viagem, Abastecimentos, Manutencao).
   Dados no servidor (plugins/garage.py: GET /linux/garage, POST /linux/garage-add|done|del).
   Viagem: distancia e tempo calculados no navegador a partir dos eventos 'hl-fix'; fica salva em localStorage. */
(function () {
  'use strict';
  var TRIP_KEY = 'harumi.garage.trip';
  var NOGPS_MS = 15000;
  var panel, tabs = {}, pages = {}, current = 'viagem', data = null, msgEl;
  var trip = loadTrip(), lastFixAt = 0, tripEls = {};

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function today() { var d = new Date(); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function fmt(n, dec) { return Number(n).toLocaleString('pt-BR', { minimumFractionDigits: dec || 0, maximumFractionDigits: dec || 0 }); }
  function brl(n) { return 'R$ ' + fmt(n, 2); }
  function brDate(s) { var p = String(s || '').split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : ''; }

  /* ---------------- Viagem ---------------- */
  function loadTrip() {
    try {
      var t = JSON.parse(localStorage.getItem(TRIP_KEY) || 'null');
      if (t && Number.isFinite(t.km) && Number.isFinite(t.startMs)) return { km: t.km, startMs: t.startMs, last: null };
    } catch (e) { /* ignora */ }
    return { km: 0, startMs: 0, last: null };
  }
  function saveTrip() { try { localStorage.setItem(TRIP_KEY, JSON.stringify({ km: trip.km, startMs: trip.startMs })); } catch (e) { /* ignora */ } }
  function meters(a, b) {
    var R = 6371000, r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLon = (b.lon - a.lon) * r;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
  }
  function onFix(e) {
    var f = e && e.detail;
    if (!f || !Number.isFinite(f.lat) || !Number.isFinite(f.lon)) return;
    var now = Date.now();
    lastFixAt = now;
    if (!trip.startMs) trip.startMs = now;
    if (trip.last) {
      var d = meters(trip.last, f);
      if (d >= 3 && d < 1000) trip.km += d / 1000; // ignora tremor parado e saltos de GPS
    }
    trip.last = { lat: f.lat, lon: f.lon };
    saveTrip();
    renderTrip();
  }
  function renderTrip() {
    if (!tripEls.km) return;
    var gps = Date.now() - lastFixAt < NOGPS_MS && lastFixAt > 0;
    var ms = trip.startMs ? Date.now() - trip.startMs : 0, h = ms / 3600000;
    tripEls.km.textContent = fmt(trip.km, 1) + ' km';
    tripEls.time.textContent = Math.floor(h) + ' h ' + pad(Math.floor((h % 1) * 60)) + ' min';
    tripEls.avg.textContent = h > 0.01 && trip.km > 0 ? fmt(trip.km / h, 0) + ' km/h' : '—';
    tripEls.gps.textContent = gps ? 'GPS ativo' : 'sem GPS';
    tripEls.gps.classList.toggle('warn', !gps);
  }
  function newTrip() {
    trip = { km: 0, startMs: lastFixAt && Date.now() - lastFixAt < NOGPS_MS ? Date.now() : 0, last: null };
    saveTrip(); renderTrip();
  }

  /* ---------------- Rede ---------------- */
  function say(text, bad) {
    if (!msgEl) return;
    msgEl.textContent = text || '';
    msgEl.classList.toggle('bad', !!bad);
  }
  function load() {
    return fetch('/linux/garage', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (j) {
      data = j; renderAll();
    }).catch(function () { say('Não consegui ler a Garagem. O servidor está ativo?', true); });
  }
  function post(path, body) {
    return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (x) {
        if (x.ok && x.j && x.j.ok) { data = x.j; renderAll(); say('Salvo.'); return true; }
        say((x.j && x.j.erro) || 'Não foi possível salvar.', true); return false;
      }).catch(function () { say('Falha de comunicação com o servidor.', true); return false; });
  }

  /* ---------------- Formularios ---------------- */
  function field(form, name, label, opts) {
    opts = opts || {};
    var w = el('label', 'hl-g-field');
    w.appendChild(el('span', '', label));
    var i = el('input');
    i.type = 'text'; i.name = name; i.autocomplete = 'off';
    if (opts.mode) i.setAttribute('inputmode', opts.mode);
    if (opts.value) i.value = opts.value;
    if (opts.placeholder) i.placeholder = opts.placeholder;
    i.maxLength = opts.max || 24;
    w.appendChild(i); form.appendChild(w);
    return i;
  }
  function button(text, cls, fn) {
    var b = el('button', 'hl-g-btn' + (cls ? ' ' + cls : ''), text);
    b.type = 'button'; b.addEventListener('click', fn); return b;
  }
  function val(i) { return i.value.trim(); }
  function confirmButton(text, fn) {
    var b = button(text, 'danger', function () {
      if (b.dataset.arm === '1') { fn(); return; }
      b.dataset.arm = '1'; b.textContent = 'Toque de novo';
      setTimeout(function () { b.dataset.arm = ''; b.textContent = text; }, 3500);
    });
    return b;
  }

  /* ---------------- Paginas ---------------- */
  function buildTripPage(p) {
    p.appendChild(el('h3', '', 'Viagem atual'));
    var grid = el('div', 'hl-g-stats');
    function stat(key, label) {
      var c = el('div', 'hl-g-stat'); tripEls[key] = el('b', '', '—');
      c.appendChild(tripEls[key]); c.appendChild(el('span', '', label)); grid.appendChild(c);
    }
    stat('km', 'distância'); stat('time', 'tempo'); stat('avg', 'média');
    p.appendChild(grid);
    tripEls.gps = el('p', 'hl-g-note', 'sem GPS');
    p.appendChild(tripEls.gps);
    p.appendChild(el('p', 'hl-g-note', 'Calculado pelos sinais do GPS: só soma enquanto há sinal. O tempo conta desde o primeiro sinal da viagem.'));
    p.appendChild(button('Nova viagem', 'primary', newTrip));
  }

  var fuelListEl, maintListEl, odoEl, avgEl;
  function buildFuelPage(p) {
    p.appendChild(el('h3', '', 'Novo abastecimento'));
    var form = el('div', 'hl-g-form');
    var fData = field(form, 'data', 'Data (AAAA-MM-DD)', { value: today(), max: 10, mode: 'numeric' });
    var fKm = field(form, 'km', 'Hodômetro (km)', { mode: 'numeric', max: 8 });
    var fL = field(form, 'litros', 'Litros', { mode: 'decimal', max: 8 });
    var fV = field(form, 'valor', 'Valor total (R$)', { mode: 'decimal', max: 9 });
    var fP = field(form, 'posto', 'Posto (opcional)', { max: 40 });
    var cw = el('label', 'hl-g-check'); var ck = el('input'); ck.type = 'checkbox'; ck.checked = true;
    cw.appendChild(ck); cw.appendChild(el('span', '', 'Tanque cheio (necessário para calcular km/l)'));
    form.appendChild(cw);
    form.appendChild(button('Adicionar', 'primary', function () {
      post('/linux/garage-add', { tipo: 'fuel', data: val(fData), km: val(fKm), litros: val(fL), valor: val(fV), posto: val(fP), cheio: ck.checked })
        .then(function (ok) { if (ok) { fKm.value = ''; fL.value = ''; fV.value = ''; fP.value = ''; } });
    }));
    p.appendChild(form);
    avgEl = el('p', 'hl-g-avg', ''); p.appendChild(avgEl);
    p.appendChild(el('h3', '', 'Histórico'));
    fuelListEl = el('div', 'hl-g-list'); p.appendChild(fuelListEl);
  }

  function buildMaintPage(p) {
    p.appendChild(el('h3', '', 'Hodômetro atual'));
    odoEl = el('p', 'hl-g-note', ''); p.appendChild(odoEl);
    var of = el('div', 'hl-g-form row');
    var fo = field(of, 'km', 'Atualizar hodômetro (km)', { mode: 'numeric', max: 8 });
    of.appendChild(button('Salvar km', '', function () {
      post('/linux/garage-add', { tipo: 'odo', km: val(fo) }).then(function (ok) { if (ok) fo.value = ''; });
    }));
    p.appendChild(of);
    p.appendChild(el('h3', '', 'Novo lembrete'));
    var form = el('div', 'hl-g-form');
    var fN = field(form, 'nome', 'Nome (ex.: troca de óleo)', { max: 40 });
    var fK = field(form, 'cada_km', 'A cada (km)', { mode: 'numeric', max: 7 });
    var fM = field(form, 'cada_meses', 'A cada (meses)', { mode: 'numeric', max: 3 });
    var fUk = field(form, 'ultimo_km', 'Feito pela última vez no km', { mode: 'numeric', max: 8 });
    var fUd = field(form, 'ultima_data', 'Feito em (AAAA-MM-DD)', { mode: 'numeric', max: 10 });
    form.appendChild(button('Adicionar lembrete', 'primary', function () {
      post('/linux/garage-add', { tipo: 'maint', nome: val(fN), cada_km: val(fK), cada_meses: val(fM), ultimo_km: val(fUk), ultima_data: val(fUd) })
        .then(function (ok) { if (ok) { fN.value = ''; fK.value = ''; fM.value = ''; fUk.value = ''; fUd.value = ''; } });
    }));
    p.appendChild(form);
    p.appendChild(el('h3', '', 'Lembretes'));
    maintListEl = el('div', 'hl-g-list'); p.appendChild(maintListEl);
  }

  function renderAll() {
    renderTrip();
    if (!data) return;
    // abastecimentos
    avgEl.textContent = data.media_kml != null ? 'Média: ' + fmt(data.media_kml, 2) + ' km/l (entre tanques cheios)' : 'Média km/l: precisa de dois abastecimentos com tanque cheio.';
    fuelListEl.textContent = '';
    if (!data.abastecimentos.length) fuelListEl.appendChild(el('p', 'hl-g-empty', 'Nenhum abastecimento ainda. Preencha o formulário acima e toque em Adicionar: data, km do hodômetro, litros e valor.'));
    data.abastecimentos.forEach(function (f) {
      var row = el('div', 'hl-g-row');
      var info = el('div', 'hl-g-info');
      info.appendChild(el('strong', '', brDate(f.data) + ' · ' + fmt(f.km) + ' km'));
      info.appendChild(el('span', '', fmt(f.litros, 2) + ' L · ' + brl(f.valor) + (f.preco_litro ? ' (' + brl(f.preco_litro) + '/L)' : '') + (f.posto ? ' · ' + f.posto : '') + (f.cheio ? '' : ' · parcial')));
      if (f.kml != null) info.appendChild(el('span', 'hl-g-kml', fmt(f.kml, 2) + ' km/l'));
      row.appendChild(info);
      row.appendChild(confirmButton('Remover', function () { post('/linux/garage-del', { tipo: 'fuel', id: f.id }); }));
      fuelListEl.appendChild(row);
    });
    // manutencao
    odoEl.textContent = data.odometro != null ? 'Último km conhecido: ' + fmt(data.odometro) + ' km (maior entre abastecimentos e o valor salvo aqui).' : 'Hodômetro desconhecido. Salve o km atual abaixo ou registre um abastecimento.';
    maintListEl.textContent = '';
    if (!data.manutencoes.length) maintListEl.appendChild(el('p', 'hl-g-empty', 'Nenhum lembrete ainda. Informe o nome, a cada quantos km e/ou meses, e quando foi feito pela última vez.'));
    data.manutencoes.forEach(function (m) {
      var row = el('div', 'hl-g-row ' + m.status);
      var info = el('div', 'hl-g-info');
      info.appendChild(el('strong', '', m.nome));
      var parts = [];
      if (m.km_restante != null) parts.push(m.km_restante < 0 ? 'vencido há ' + fmt(-m.km_restante) + ' km' : 'vence em ' + fmt(m.km_restante) + ' km');
      if (m.dias_restantes != null) parts.push(m.dias_restantes < 0 ? 'vencido há ' + fmt(-m.dias_restantes) + ' dias' : 'vence em ' + fmt(m.dias_restantes) + ' dias');
      if (!parts.length) parts.push('sem dados para calcular (faltam km atual ou última data)');
      info.appendChild(el('span', 'hl-g-due', (m.status === 'vencido' ? 'VENCIDO · ' : '') + parts.join(' · ')));
      var cfg = [];
      if (m.cada_km) cfg.push('a cada ' + fmt(m.cada_km) + ' km');
      if (m.cada_meses) cfg.push('a cada ' + m.cada_meses + ' meses');
      if (m.ultimo_km != null) cfg.push('último: ' + fmt(m.ultimo_km) + ' km');
      if (m.ultima_data) cfg.push(brDate(m.ultima_data));
      info.appendChild(el('span', '', cfg.join(' · ')));
      row.appendChild(info);
      row.appendChild(button('Feito agora', '', function () { post('/linux/garage-done', { id: m.id }); }));
      row.appendChild(confirmButton('Remover', function () { post('/linux/garage-del', { tipo: 'maint', id: m.id }); }));
      maintListEl.appendChild(row);
    });
  }

  /* ---------------- Painel ---------------- */
  function select(name) {
    current = name;
    Object.keys(tabs).forEach(function (k) {
      var on = k === name;
      tabs[k].setAttribute('aria-selected', on ? 'true' : 'false');
      tabs[k].tabIndex = on ? 0 : -1;
      pages[k].hidden = !on;
    });
    say('');
  }
  function build() {
    panel = el('section', 'hl-garage'); panel.id = 'hl-garage'; panel.hidden = true;
    panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', 'Garagem');
    var head = el('div', 'hl-g-head');
    head.appendChild(el('h2', '', 'Garagem'));
    var tl = el('div', 'hl-g-tabs'); tl.setAttribute('role', 'tablist');
    [['viagem', 'Viagem'], ['abast', 'Abastecimentos'], ['manut', 'Manutenção']].forEach(function (t) {
      var b = el('button', 'hl-g-tab', t[1]); b.type = 'button'; b.setAttribute('role', 'tab');
      b.addEventListener('click', function () { select(t[0]); });
      tabs[t[0]] = b; tl.appendChild(b);
    });
    tl.addEventListener('keydown', function (e) {
      var keys = Object.keys(tabs), i = keys.indexOf(current);
      if (e.key === 'ArrowRight') { select(keys[(i + 1) % keys.length]); tabs[current].focus(); }
      else if (e.key === 'ArrowLeft') { select(keys[(i + keys.length - 1) % keys.length]); tabs[current].focus(); }
    });
    head.appendChild(tl);
    head.appendChild(button('Fechar', 'close', close));
    panel.appendChild(head);
    msgEl = el('p', 'hl-g-msg', ''); msgEl.setAttribute('role', 'status'); panel.appendChild(msgEl);
    var body = el('div', 'hl-g-body');
    ['viagem', 'abast', 'manut'].forEach(function (k) { pages[k] = el('div', 'hl-g-page'); pages[k].setAttribute('role', 'tabpanel'); body.appendChild(pages[k]); });
    buildTripPage(pages.viagem); buildFuelPage(pages.abast); buildMaintPage(pages.manut);
    panel.appendChild(body);
    document.body.appendChild(panel);
    panel.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    select('viagem');
  }
  function open() {
    if (!panel) build();
    panel.hidden = false; select(current); load(); renderTrip();
    tabs[current].focus();
  }
  function close() { if (panel) panel.hidden = true; }

  function start() {
    window.addEventListener('hl-fix', onFix);
    setInterval(function () { if (panel && !panel.hidden) renderTrip(); }, 1000);
    if (window.harumiLinux && window.harumiLinux.addApp) {
      window.harumiLinux.addApp({ id: 'garage', label: 'Garagem', icon: 'ck-car', run: open });
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

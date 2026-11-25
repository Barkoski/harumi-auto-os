/* Modulo GPS: recebe os fixes do plugins/gps.py (gpsd ou simulador) e os entrega a pagina.
   Caminhos de entrada: SSE (harumiGpsFix, via linux-bridge.js) e, de reserva, GET /linux/gps a cada 2 s.
   Saida: window.harumiNav.fix(f) (e o que o mapa usa; o gancho de linux-layout.js ja emite 'hl-fix' nesse caso).
   Se o gancho ainda nao estiver ativo, este modulo emite 'hl-fix' por conta propria. */
(function () {
  'use strict';
  var lastSeq = 0, lastSseAt = 0, lastFixAt = 0, lastSource = null, state = { sim: false, gpsd: false, fonte: null };
  var badge, statusEl, switchEl;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function apply(fix) {
    if (!fix || !Number.isFinite(fix.lat) || !Number.isFinite(fix.lon)) return;
    if (fix.seq && fix.seq <= lastSeq) return; // ja aplicado (SSE e polling podem repetir)
    if (fix.seq) lastSeq = fix.seq;
    lastFixAt = Date.now(); lastSource = fix.fonte || null;
    var h = Number.isFinite(fix.heading) ? fix.heading : null;
    var f = { lat: fix.lat, lon: fix.lon, speedMps: Number.isFinite(fix.speedMps) ? fix.speedMps : 0,
              heading: h, bearing: h == null ? -1 : h, quality: 'OK', fonte: fix.fonte || null };
    var nav = window.harumiNav;
    if (nav && typeof nav.fix === 'function') {
      // o gancho de linux-layout.js (__hlWrapped) ja dispara 'hl-fix' dentro de nav.fix
      if (!nav.__hlWrapped) window.dispatchEvent(new CustomEvent('hl-fix', { detail: f }));
      try { nav.fix(f); } catch (e) { console.warn('gps nav.fix', e); }
    } else {
      window.dispatchEvent(new CustomEvent('hl-fix', { detail: f }));
    }
    renderBadge();
  }

  // Chamada pelo servidor por SSE: {fn:'harumiGpsFix', args:[fix]}
  window.harumiGpsFix = function (fix) { lastSseAt = Date.now(); apply(fix); };

  function renderBadge() {
    if (!badge) return;
    var on = lastSource === 'simulacao' && Date.now() - lastFixAt < 10000;
    badge.hidden = !on;
  }

  function renderStatus() {
    if (!statusEl) return;
    var txt;
    if (state.fonte === 'gpsd') txt = 'Sinal do gpsd (GPS real).';
    else if (state.fonte === 'simulacao') txt = 'Usando o SIMULADOR. A posição não é real.';
    else if (state.gpsd) txt = 'gpsd conectado, aguardando posição (sem fix).';
    else txt = 'Sem sinal: gpsd não encontrado (nova tentativa a cada 30 s).';
    statusEl.textContent = txt;
    if (switchEl) {
      switchEl.setAttribute('aria-checked', state.sim ? 'true' : 'false');
      switchEl.textContent = state.sim ? 'Simulador ligado' : 'Simulador desligado';
      switchEl.classList.toggle('on', !!state.sim);
    }
  }

  function poll() {
    fetch('/linux/gps', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j) return;
      state = { sim: !!j.sim, gpsd: !!j.gpsd, fonte: j.fonte || null };
      // reserva: so aplica por aqui se o SSE esta calado
      if (j.fix && j.fonte && Date.now() - lastSseAt > 3000) apply(j.fix);
      renderStatus(); renderBadge();
    }).catch(function () { /* servidor fora: tenta no proximo ciclo */ });
  }

  function toggleSim() {
    if (!window.HarumiNative || !window.HarumiNative.dispatch) return;
    window.HarumiNative.dispatch('gps.sim', state.sim ? 'off' : 'on');
    setTimeout(poll, 400);
  }

  function build() {
    badge = el('div', 'hl-gps-badge', 'SIMULAÇÃO');
    badge.setAttribute('role', 'status'); badge.hidden = true;
    document.body.appendChild(badge);

    var box = el('div', 'hl-gps-box');
    statusEl = el('p', 'hl-gps-status', 'Verificando o GPS…');
    switchEl = el('button', 'hl-gps-switch', 'Simulador desligado');
    switchEl.type = 'button'; switchEl.setAttribute('role', 'switch'); switchEl.setAttribute('aria-checked', 'false');
    switchEl.addEventListener('click', toggleSim);
    var hint = el('p', 'hl-gps-hint', 'O simulador percorre um trajeto fixo no centro de Londrina, só para testar sem GPS. Enquanto ligado, aparece o selo SIMULAÇÃO no topo.');
    box.appendChild(statusEl); box.appendChild(switchEl); box.appendChild(hint);
    var api = window.harumiLinux;
    if (api && api.addSettingsSection) api.addSettingsSection('GPS', box);

    poll(); setInterval(poll, 2000);
    setInterval(renderBadge, 2000);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();

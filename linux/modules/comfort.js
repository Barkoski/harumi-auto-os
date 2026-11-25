/* Conforto da Harumi OS: modo tela limpa (so mapa/relogio + barra inferior) e lembrete de descanso.
   Modulo injetado pelo servidor (linux/modules). Sem estilo inline (CSP): tudo em comfort.css, classes e atributo hidden.
   API: window.harumiComfort.cleanScreen(on) | isClean() ; window.harumiAssistCmd(cmd) recebe as intencoes do assistente. */
(function () {
  'use strict';
  var PREF_CLOCK = 'ck.comfort.clock', PREF_REST = 'ck.comfort.rest';
  var REST_CHOICES = [{ h: 0, label: 'Desligado' }, { h: 1, label: '1 h' }, { h: 2, label: '2 h' }, { h: 3, label: '3 h' }];
  var MOVING_MPS = 2;              /* acima disso conta como em movimento */
  var PAUSE_RESET_MS = 10 * 60e3;  /* parado/sem uso por tanto tempo zera a contagem (pausa feita) */
  var REPEAT_MS = 30 * 60e3;       /* nao repete o aviso antes disso */
  var GPS_FRESH_MS = 60e3;         /* fix mais novo que isso = ha GPS */
  var TICK_MS = 30e3;
  var NOTICE_SHOW_MS = 45e3;

  function load(key, def) { try { var v = localStorage.getItem(key); return v === null ? def : v; } catch (e) { return def; } }
  function save(key, val) { try { localStorage.setItem(key, String(val)); } catch (e) { /* armazenamento indisponivel */ } }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text) e.textContent = text; return e; }

  var clockPref = load(PREF_CLOCK, '0') === '1';
  var restHours = (function () { var n = parseInt(load(PREF_REST, '2'), 10); return n >= 0 && n <= 3 ? n : 2; })();

  /* ---------------- Tela limpa ---------------- */
  var clean = false, overlay, clockEl, exitBtn, hintEl, clockTimer = 0, restoreFocus = null;

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function mapOpen() { var rm = window.harumiRoadMap; try { return !!(rm && rm.isOpen && rm.isOpen()); } catch (e) { return false; } }
  function tickClock() {
    clearTimeout(clockTimer);
    if (!clean) return;
    var d = new Date(); clockEl.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes());
    clockTimer = setTimeout(tickClock, 60e3 - (d.getSeconds() * 1000 + d.getMilliseconds()) + 50);
  }
  function showClock() { return clockPref || !mapOpen(); }

  function buildOverlay() {
    overlay = el('div'); overlay.id = 'ck-clean'; overlay.hidden = true;
    overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-label', 'Tela limpa');
    clockEl = el('div', 'ck-clean-clock'); clockEl.setAttribute('aria-live', 'off');
    hintEl = el('p', 'ck-clean-hint', 'Toque em qualquer lugar para voltar');
    exitBtn = el('button', 'ck-clean-exit', 'Sair da tela limpa'); exitBtn.type = 'button';
    exitBtn.addEventListener('click', function (e) { e.stopPropagation(); setClean(false); });
    overlay.addEventListener('click', function () { setClean(false); });
    overlay.appendChild(exitBtn); overlay.appendChild(clockEl); overlay.appendChild(hintEl);
    document.body.appendChild(overlay);
  }

  function setClean(on) {
    on = !!on;
    if (on === clean) return;
    if (!overlay) buildOverlay();
    clean = on;
    document.body.classList.toggle('ck-clean', on);
    overlay.hidden = !on;
    if (on) {
      restoreFocus = document.activeElement;
      var showC = showClock();
      clockEl.hidden = !showC;
      overlay.classList.toggle('ck-clean-solid', !mapOpen());
      if (window.harumiKeyboard && window.harumiKeyboard.close) { try { window.harumiKeyboard.close(); } catch (e) { /* teclado ausente */ } }
      if (window.harumiEmbed && window.harumiEmbed.suspend) window.harumiEmbed.suspend(true);
      tickClock();
      try { exitBtn.focus({ preventScroll: true }); } catch (e) { /* sem foco */ }
    } else {
      clearTimeout(clockTimer);
      if (window.harumiEmbed && window.harumiEmbed.suspend) window.harumiEmbed.suspend(false);
      try { if (restoreFocus && restoreFocus.focus) restoreFocus.focus({ preventScroll: true }); } catch (e) { /* elemento sumiu */ }
      restoreFocus = null;
    }
    syncSettings();
  }

  /* tocar no dock (apps, volume) tambem sai da tela limpa: os paineis ficariam escondidos */
  document.addEventListener('click', function (e) { if (clean && e.target.closest && e.target.closest('#hl-dock')) setClean(false); }, true);
  document.addEventListener('keydown', function (e) { if (clean && e.key === 'Escape') { e.preventDefault(); setClean(false); } });

  /* ---------------- Lembrete de descanso ---------------- */
  var acc = 0,             /* ms de uso contado desde a ultima pausa */
      lastFixAt = 0,       /* ultimo hl-fix recebido */
      lastMoveAt = 0,      /* ultimo instante em movimento (GPS) */
      lastTickAt = Date.now(), nextAllowedAt = 0, notice, noticeText, noticeTimer = 0;

  function gpsActive() { return lastFixAt && Date.now() - lastFixAt < GPS_FRESH_MS; }
  function limitMs() { return restHours * 3600e3; }

  function onFix(f) {
    f = f || {};
    var v = Number.isFinite(f.speedMps) ? f.speedMps : f.speed, now = Date.now();
    var dt = lastFixAt ? now - lastFixAt : 0;
    lastFixAt = now;
    if (!Number.isFinite(v)) return;
    if (v > MOVING_MPS) {
      if (lastMoveAt && now - lastMoveAt > PAUSE_RESET_MS) acc = 0;
      /* tempo entre fixes so conta se for curto: buraco no sinal (tunel, reinicio) nao infla a contagem */
      if (dt > 0 && dt <= 10e3) acc += dt;
      lastMoveAt = now;
      check();
    }
  }
  window.addEventListener('hl-fix', function (e) { onFix(e.detail); });

  function tick() {
    var now = Date.now(), dt = now - lastTickAt;
    lastTickAt = now;
    if (dt > PAUSE_RESET_MS) { acc = 0; return; }       /* aparelho dormiu/tela apagada por muito tempo */
    if (document.visibilityState === 'hidden') return;
    if (!gpsActive()) {                                  /* sem GPS: conta o tempo com a tela ligada */
      acc += Math.min(dt, TICK_MS * 2);
      check();
    } else if (lastMoveAt && now - lastMoveAt > PAUSE_RESET_MS) {
      acc = 0;                                           /* com GPS: parado 10 min = pausa */
    }
    syncSettings();
  }
  setInterval(tick, TICK_MS);

  var WORDS = { 1: 'Uma hora', 2: 'Duas horas', 3: 'Três horas' };
  function buildNotice() {
    notice = el('div', 'ck-rest'); notice.hidden = true; notice.setAttribute('role', 'status'); notice.setAttribute('aria-live', 'polite');
    noticeText = el('span', 'ck-rest-text');
    var ok = el('button', 'ck-rest-ok', 'Dispensar'); ok.type = 'button';
    ok.addEventListener('click', hideNotice);
    notice.appendChild(noticeText); notice.appendChild(ok);
    document.body.appendChild(notice);
  }
  function hideNotice() { clearTimeout(noticeTimer); if (notice) notice.hidden = true; }
  function showNotice(gps) {
    if (!notice) buildNotice();
    noticeText.textContent = (WORDS[restHours] || (restHours + ' horas')) + (gps ? ' de direção' : ' de uso da tela') + '. Que tal uma pausa?';
    notice.hidden = false;
    clearTimeout(noticeTimer); noticeTimer = setTimeout(hideNotice, NOTICE_SHOW_MS);
  }
  function check() {
    if (!restHours || acc < limitMs()) return;
    var now = Date.now();
    if (now < nextAllowedAt) return;
    nextAllowedAt = now + REPEAT_MS;
    showNotice(!!gpsActive());
  }

  /* ---------------- Ajustes ---------------- */
  var cleanBtn, clockBtn, restBtns = [], modeEl;
  function syncSettings() {
    if (cleanBtn) cleanBtn.setAttribute('aria-pressed', clean ? 'true' : 'false');
    if (clockBtn) clockBtn.setAttribute('aria-pressed', clockPref ? 'true' : 'false');
    restBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(parseInt(b.dataset.h, 10) === restHours)); });
    if (modeEl) {
      var mins = Math.floor(acc / 60e3);
      modeEl.textContent = (gpsActive() ? 'Contagem pelo GPS: só conta o tempo em movimento.' : 'Sem GPS: a contagem usa o tempo com a tela ligada.') +
        (restHours ? ' Contado até agora: ' + mins + ' min.' : '');
    }
  }
  function buildSettings() {
    if (!window.harumiLinux || !window.harumiLinux.addSettingsSection) return;
    var box = el('div', 'ck-comfort');
    cleanBtn = el('button', 'ck-comfort-btn', 'Tela limpa'); cleanBtn.type = 'button';
    cleanBtn.setAttribute('aria-pressed', 'false');
    cleanBtn.addEventListener('click', function () { setClean(true); });
    clockBtn = el('button', 'ck-comfort-btn', 'Relógio grande na tela limpa'); clockBtn.type = 'button';
    clockBtn.addEventListener('click', function () { clockPref = !clockPref; save(PREF_CLOCK, clockPref ? '1' : '0'); syncSettings(); });
    var row1 = el('div', 'ck-comfort-row'); row1.appendChild(cleanBtn); row1.appendChild(clockBtn);

    var lab = el('p', 'ck-comfort-label', 'Lembrete de descanso'); lab.id = 'ck-rest-label';
    var grp = el('div', 'ck-comfort-row'); grp.setAttribute('role', 'group'); grp.setAttribute('aria-labelledby', 'ck-rest-label');
    REST_CHOICES.forEach(function (c) {
      var b = el('button', 'ck-comfort-btn', c.label); b.type = 'button'; b.dataset.h = String(c.h);
      b.addEventListener('click', function () {
        restHours = c.h; save(PREF_REST, c.h); acc = 0; nextAllowedAt = 0; hideNotice(); syncSettings();
      });
      restBtns.push(b); grp.appendChild(b);
    });
    modeEl = el('p', 'ck-comfort-note');
    box.appendChild(row1); box.appendChild(lab); box.appendChild(grp); box.appendChild(modeEl);
    window.harumiLinux.addSettingsSection('Conforto', box);
    syncSettings();
  }

  /* ---------------- API e intencoes do assistente ---------------- */
  window.harumiComfort = { cleanScreen: setClean, isClean: function () { return clean; } };
  window.harumiAssistCmd = function (cmd) {
    if (!cmd || typeof cmd.type !== 'string') return;
    if (cmd.type === 'cleanScreen') { setClean(!!cmd.on); return; }
    if (cmd.type === 'closeApp') {
      if (window.harumiEmbed && window.harumiEmbed.close) window.harumiEmbed.close();
      if (window.HarumiNative && window.HarumiNative.dispatch) window.HarumiNative.dispatch('linux.close', '');
    }
  };

  function start() { buildSettings(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

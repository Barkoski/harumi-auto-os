/* Privacidade: modo manobrista (PIN) e "Apagar meus dados". Fala com plugins/privacy.py (/linux/privacy*).
   Com o modo ligado, o body ganha a classe hl-valet e o privacy.css esconde conversa com a IA, favoritos,
   historico de viagens e a Garagem. O PIN so trafega para o servidor local e nunca e guardado na pagina. */
(function () {
  'use strict';
  var state = { valet: false, pinSet: false, waitS: 0 };
  var KEY_PREFIX = 'hl.';

  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }

  function call(path, body) {
    var opt = body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
    return fetch(path, opt).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { j.status = r.status; return j; }); })
      .catch(function () { return { ok: false, error: 'rede', status: 0 }; });
  }
  function msg(j) {
    if (j.ok) return '';
    if (j.error === 'espera') return 'Muitas tentativas. Aguarde ' + j.waitS + ' s.';
    if (j.error === 'pin') return 'PIN incorreto.';
    if (j.error === 'formato') return 'O PIN deve ter de 4 a 8 dígitos.';
    if (j.error === 'sem-pin') return 'Defina um PIN antes de ligar o modo manobrista.';
    if (j.error === 'rede') return 'Sem resposta do servidor local.';
    return 'Não foi possível concluir.';
  }
  function say(text) {
    var m = document.getElementById('message'); if (!m) return;
    m.textContent = text; m.hidden = false; clearTimeout(say.t); say.t = setTimeout(function () { m.hidden = true; }, 4500);
  }

  /* Impede que a pagina regrave hl.* (ex.: historico de viagens no pagehide) depois de apagar os dados. */
  var wiped = false;
  try {
    var origSet = Storage.prototype.setItem;
    Storage.prototype.setItem = function (k, v) { if (wiped && String(k).indexOf(KEY_PREFIX) === 0) return; return origSet.call(this, k, v); };
  } catch (e) { /* sem storage */ }

  function wipeLocal() {
    wiped = true;
    try {
      var keys = [];
      for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k && k.indexOf(KEY_PREFIX) === 0) keys.push(k); }
      keys.forEach(function (k) { localStorage.removeItem(k); });
    } catch (e) { /* sem storage */ }
  }

  function applyState(s) {
    if (s && typeof s.valet === 'boolean') { state.valet = s.valet; state.pinSet = !!s.pinSet; state.waitS = s.waitS || 0; }
    document.body.classList.toggle('hl-valet', state.valet);
    if (exitBtn) exitBtn.hidden = !state.valet;
    if (statusEl) renderSettings();
  }
  function refresh() { return call('/linux/privacy').then(function (j) { if (j.ok) applyState(j); }); }

  /* ---------- botao fixo para sair do modo (exige o PIN) ---------- */
  var exitBtn, dlg, dlgInput, dlgErr, dlgOk;
  function buildExit() {
    exitBtn = el('button', 'hl-priv-exit', 'Sair do modo manobrista'); exitBtn.type = 'button'; exitBtn.hidden = true;
    exitBtn.addEventListener('click', function () { askPin('Digite o PIN para sair do modo manobrista.', function (pin, done) {
      call('/linux/privacy-valet', { on: false, pin: pin }).then(function (j) { if (j.ok) { applyState(j); done(true); } else done(false, msg(j)); });
    }); });
    document.body.appendChild(exitBtn);

    dlg = el('div', 'hl-priv-dialog'); dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-modal', 'true'); dlg.setAttribute('aria-labelledby', 'hl-priv-dlg-title'); dlg.hidden = true;
    var box = el('form', 'hl-priv-box');
    var title = el('h3', '', ''); title.id = 'hl-priv-dlg-title';
    dlgInput = el('input'); dlgInput.type = 'password'; dlgInput.inputMode = 'numeric'; dlgInput.autocomplete = 'off'; dlgInput.maxLength = 8; dlgInput.setAttribute('aria-label', 'PIN');
    dlgErr = el('p', 'hl-priv-err', ''); dlgErr.setAttribute('role', 'alert');
    var row = el('div', 'hl-priv-row');
    dlgOk = el('button', 'hl-priv-btn primary', 'Confirmar'); dlgOk.type = 'submit';
    var cancel = el('button', 'hl-priv-btn', 'Cancelar'); cancel.type = 'button';
    row.appendChild(dlgOk); row.appendChild(cancel);
    box.appendChild(title); box.appendChild(dlgInput); box.appendChild(dlgErr); box.appendChild(row); dlg.appendChild(box);
    document.body.appendChild(dlg);
    var handler = null, opener = null;
    function close() { dlg.hidden = true; dlgInput.value = ''; dlgErr.textContent = ''; handler = null; if (opener && opener.focus) opener.focus(); }
    cancel.addEventListener('click', close);
    dlg.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    box.addEventListener('submit', function (e) {
      e.preventDefault(); if (!handler) return;
      var pin = dlgInput.value; dlgOk.disabled = true;
      handler(pin, function (ok, err) { dlgOk.disabled = false; if (ok) close(); else { dlgErr.textContent = err || 'Não foi possível concluir.'; dlgInput.value = ''; dlgInput.focus(); } });
    });
    askPin = function (text, fn) { title.textContent = text; handler = fn; opener = document.activeElement; dlg.hidden = false; dlgInput.focus(); };
  }
  var askPin = function () { /* definido em buildExit */ };

  /* ---------- secao em Ajustes ---------- */
  var statusEl, secBody, pinForm, wipeBox;
  function field(label, id, hint) {
    var wrap = el('label', 'hl-priv-field'); wrap.appendChild(el('span', '', label));
    var i = el('input'); i.type = 'password'; i.inputMode = 'numeric'; i.autocomplete = 'off'; i.maxLength = 8; i.id = id; if (hint) i.placeholder = hint;
    wrap.appendChild(i); return { wrap: wrap, input: i };
  }
  function button(text, cls, fn) { var b = el('button', 'hl-priv-btn ' + (cls || ''), text); b.type = 'button'; b.addEventListener('click', fn); return b; }

  function build() {
    secBody = el('div', 'hl-priv');
    statusEl = el('p', 'hl-priv-status', '');
    statusEl.setAttribute('role', 'status');
    secBody.appendChild(el('h4', '', 'Modo manobrista'));
    secBody.appendChild(el('p', 'hl-priv-note', 'Com o modo ligado, ficam escondidos: conversa com a IA, favoritos Casa/Trabalho, histórico de viagens e Garagem. Para sair é preciso o PIN.'));
    secBody.appendChild(statusEl);

    pinForm = el('form', 'hl-priv-form');
    var cur = field('PIN atual', 'hl-priv-cur'), nw = field('Novo PIN (4 a 8 dígitos)', 'hl-priv-new');
    var pinErr = el('p', 'hl-priv-err', ''); pinErr.setAttribute('role', 'alert');
    var save = el('button', 'hl-priv-btn', 'Salvar PIN'); save.type = 'submit';
    pinForm.appendChild(cur.wrap); pinForm.appendChild(nw.wrap); pinForm.appendChild(save); pinForm.appendChild(pinErr);
    pinForm.addEventListener('submit', function (e) {
      e.preventDefault();
      call('/linux/privacy-pin', { pin: nw.input.value, current: cur.input.value }).then(function (j) {
        pinErr.textContent = msg(j); cur.input.value = ''; nw.input.value = '';
        if (j.ok) { applyState({ valet: state.valet, pinSet: true, waitS: 0 }); say('PIN salvo.'); }
      });
    });
    pinForm.cur = cur.wrap;
    secBody.appendChild(pinForm);

    var row = el('div', 'hl-priv-row');
    var toggle = button('Ligar modo manobrista', 'primary', function () {
      if (!state.pinSet) { document.getElementById('hl-priv-new').focus(); return; }
      call('/linux/privacy-valet', { on: true }).then(function (j) { if (j.ok) applyState(j); else statusEl.textContent = msg(j); });
    });
    toggle.id = 'hl-priv-toggle'; row.appendChild(toggle); secBody.appendChild(row);

    secBody.appendChild(el('h4', '', 'Apagar meus dados'));
    var info = el('p', 'hl-priv-note', 'Será apagado do aparelho: (1) tudo o que a Harumi guardou em ~/.local/share/harumi/store; (2) as preferências e históricos guardados nesta tela, chaves “hl.*” (dock, favoritos, viagens); (3) o arquivo ~/.cache/harumi/spotify-now.json. Mapas, modelos de IA e o sistema NÃO são apagados. O PIN do modo manobrista também permanece.');
    secBody.appendChild(info);
    wipeBox = el('div', 'hl-priv-wipe');
    var step1 = button('Apagar meus dados…', '', function () { step1.hidden = true; confirmBox.hidden = false; (wipePin.wrap.hidden ? doWipe : wipePin.input).focus(); });
    var confirmBox = el('div', 'hl-priv-confirm'); confirmBox.hidden = true;
    confirmBox.appendChild(el('p', 'hl-priv-warn', 'Confirmação final: isto não pode ser desfeito.'));
    var wipePin = field('PIN (necessário com o modo manobrista ligado)', 'hl-priv-wipe-pin'); wipePin.wrap.hidden = true; confirmBox.appendChild(wipePin.wrap);
    var wipeErr = el('p', 'hl-priv-err', ''); wipeErr.setAttribute('role', 'alert');
    var doWipe = button('Sim, apagar tudo isso', 'danger', function () {
      call('/linux/privacy-wipe', { confirm: 'APAGAR', pin: wipePin.input.value }).then(function (j) {
        wipePin.input.value = '';
        if (!j.ok) { wipeErr.textContent = msg(j); return; }
        wipeLocal(); say('Dados apagados.'); setTimeout(function () { location.reload(); }, 600);
      });
    });
    var no = button('Cancelar', '', function () { confirmBox.hidden = true; step1.hidden = false; wipeErr.textContent = ''; });
    var r2 = el('div', 'hl-priv-row'); r2.appendChild(doWipe); r2.appendChild(no); confirmBox.appendChild(r2); confirmBox.appendChild(wipeErr);
    wipeBox.appendChild(step1); wipeBox.appendChild(confirmBox); secBody.appendChild(wipeBox);
    wipeBox.pinField = wipePin.wrap;
    return secBody;
  }
  function renderSettings() {
    var t = document.getElementById('hl-priv-toggle');
    statusEl.textContent = state.valet ? 'Modo manobrista LIGADO.' : (state.pinSet ? 'Modo manobrista desligado.' : 'Nenhum PIN definido ainda.');
    if (t) { t.hidden = state.valet; t.textContent = 'Ligar modo manobrista'; }
    if (pinForm && pinForm.cur) pinForm.cur.hidden = !state.pinSet;
    if (wipeBox && wipeBox.pinField) wipeBox.pinField.hidden = !state.valet;
  }

  /* ---------- itens do app que dependem da tela: marca tiles do drawer ---------- */
  var HIDE_TILES = { 'Harumi': 1, 'Viagem': 1, 'Garagem': 1 };
  function markTiles() {
    var d = document.getElementById('hl-drawer'); if (!d) return;
    [].forEach.call(d.querySelectorAll('.hl-tile'), function (t) {
      var n = t.querySelector('.hl-tile-name');
      t.classList.toggle('hl-valet-hide', !!(n && HIDE_TILES[n.textContent.trim()]));
    });
  }

  function start() {
    buildExit();
    var L = window.harumiLinux;
    if (L && L.addSettingsSection) L.addSettingsSection('Privacidade', build());
    if (L && L.addApp) {
      L.addApp({ id: 'valet', label: 'Manobrista', icon: 'ck-settings', run: function () {
        if (state.valet) { exitBtn.click(); return; }
        if (!state.pinSet) { var s = document.getElementById('configure'); if (s) s.click(); say('Defina um PIN em Ajustes > Privacidade.'); return; }
        call('/linux/privacy-valet', { on: true }).then(function (j) { if (j.ok) applyState(j); });
      } });
    }
    var d = document.getElementById('hl-drawer');
    if (d) new MutationObserver(markTiles).observe(d, { childList: true, subtree: true });
    markTiles();
    refresh();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

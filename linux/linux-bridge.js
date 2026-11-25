/* Ponte da Harumi no Linux: imita window.HarumiNative do Android (MainActivity.Bridge).
   dispatch -> POST /bridge (respostas imediatas); eventos demorados (IA, comandos) chegam por /events (SSE).
   Cada chamada e {fn, args}; so funcoes harumi* (e alguns metodos do mapa) podem ser chamadas. */
(function () {
  'use strict';
  var METHODS = { 'harumiRoadMap.open': 1, 'harumiRoadMap.plan': 1, 'harumiRoadMap.navigateTo': 1 };
  function notify(text) {
    var el = document.getElementById('message');
    if (el) { el.textContent = String(text || ''); el.hidden = false; setTimeout(function () { el.hidden = true; }, 4500); }
  }
  function call(c) {
    if (!c || typeof c.fn !== 'string') return;
    if (c.fn === '__notify') { notify(c.args && c.args[0]); return; }
    var target = window, fn;
    if (METHODS[c.fn]) {
      var parts = c.fn.split('.');
      target = window[parts[0]];
      fn = target && target[parts[1]];
    } else if (/^harumi[A-Za-z]{1,40}$/.test(c.fn)) {
      fn = window[c.fn];
    }
    if (typeof fn === 'function') { try { fn.apply(target, c.args || []); } catch (e) { console.error('harumi', c.fn, e); } }
  }
  function post(action, module) {
    return fetch('/bridge', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: action, module: module || '' }) })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (calls) { (calls || []).forEach(call); })
      .catch(function (e) { console.warn('harumi bridge', action, e); });
  }
  function listen() {
    var es = new EventSource('/events');
    es.onmessage = function (ev) { try { call(JSON.parse(ev.data)); } catch (e) { console.warn('harumi evento', e); } };
    es.onerror = function () { es.close(); setTimeout(listen, 2000); };
  }
  window.HarumiNative = { dispatch: function (action, module) { post(String(action), String(module || '')); } };
  window.harumiLinux = true;
  // Na moldura Electron o YouTube abre DENTRO da Harumi (linux-embed.js); fora dela, em janela separada.
  window.harumiLinuxOpen = function (id) {
    id = String(id || '');
    if (/^(youtube|browser|claude|chatgpt|waze)$/.test(id) && window.harumiHost && window.harumiEmbed) { window.harumiEmbed.open(id); return; }
    post('linux.open', id);
  };
  window.addEventListener('load', function () { listen(); post('__ready', ''); });
})();

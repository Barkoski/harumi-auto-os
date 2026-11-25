/* Aviso quando a IA local e pausada por calor (e quando volta). Consulta /linux/thermal; usa o aviso #message. */
(function () {
  'use strict';
  var last = null;
  function say(text) {
    var m = document.getElementById('message'); if (!m) return;
    m.textContent = text; m.hidden = false; clearTimeout(say.t); say.t = setTimeout(function () { m.hidden = true; }, 8000);
  }
  function poll() {
    fetch('/linux/thermal').then(function (r) { return r.json(); }).then(function (j) {
      if (!j || j.ok !== true) return;
      if (last !== null && j.paused !== last) {
        say(j.paused ? 'IA pausada por calor (' + j.tempC + ' °C). Volta sozinha quando a placa esfriar.' : 'IA religada: a placa esfriou.');
      } else if (last === null && j.paused) {
        say('IA pausada por calor (' + j.tempC + ' °C).');
      }
      last = j.paused;
    }).catch(function () { /* servidor indisponivel: tenta de novo */ });
  }
  function start() { poll(); setInterval(poll, 15000); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

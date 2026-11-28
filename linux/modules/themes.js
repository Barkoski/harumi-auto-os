/* Seletor de tema (Ajustes > Aparência): Harumi, Calma, Dia ou Automático (Dia das 6h às 18h, Harumi no resto).
   O horario do Automatico e fixo e aproximado: sem GPS a Harumi nao calcula nascer e por do sol. Fica salvo no aparelho. */
(function () {
  'use strict';
  var KEY = 'hl.theme.v1';
  var THEMES = [
    { id: 'harumi', name: 'Harumi', desc: 'Rosa suave no escuro', sw: ['#1d1a22', '#d2a0bd', '#f0eaf0'] },
    { id: 'calma', name: 'Calma', desc: 'Grafite, menos detalhes, letras maiores', sw: ['#1b1d21', '#d9b779', '#ececee'] },
    { id: 'dia', name: 'Dia', desc: 'Claro, para sol forte', sw: ['#fbfaf8', '#2f6f73', '#1f2226'] },
    { id: 'auto', name: 'Automático', desc: 'Dia das 6h às 18h; Harumi à noite', sw: ['#fbfaf8', '#1d1a22', '#d2a0bd'] }
  ];
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function load() { try { var v = localStorage.getItem(KEY); return THEMES.some(function (t) { return t.id === v; }) ? v : 'harumi'; } catch (e) { return 'harumi'; } }
  var choice = load(), buttons = [];

  function effective() {
    if (choice !== 'auto') return choice;
    var h = new Date().getHours();
    return h >= 6 && h < 18 ? 'dia' : 'harumi';
  }
  function apply() {
    var t = effective(), b = document.body;
    ['harumi', 'calma', 'dia'].forEach(function (id) { b.classList.toggle('hl-theme-' + id, id === t && id !== 'harumi'); });
    buttons.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.theme === choice ? 'true' : 'false'); });
  }
  function set(id) {
    if (!THEMES.some(function (t) { return t.id === id; })) return;
    choice = id; try { localStorage.setItem(KEY, id); } catch (e) { /* sem armazenamento */ }
    apply();
  }
  function settings() {
    if (!window.harumiLinux || !window.harumiLinux.addSettingsSection) return;
    var row = el('div', 'hl-theme-row');
    THEMES.forEach(function (t) {
      var b = el('button', 'hl-theme-opt'); b.type = 'button'; b.dataset.theme = t.id;
      b.setAttribute('aria-label', 'Tema ' + t.name + ': ' + t.desc);
      var sw = el('span', 'hl-theme-sw'); sw.setAttribute('aria-hidden', 'true');
      t.sw.forEach(function (c) { var i = el('i'); i.style.background = c; sw.appendChild(i); });
      b.appendChild(sw); b.appendChild(el('span', '', t.name)); b.appendChild(el('small', '', t.desc));
      b.addEventListener('click', function () { set(t.id); });
      buttons.push(b); row.appendChild(b);
    });
    row.appendChild(el('p', 'hl-theme-note', 'O tema muda só as cores e o tamanho dos textos; o layout das telas continua o mesmo.'));
    window.harumiLinux.addSettingsSection('Aparência', row);
    apply();
  }
  window.harumiTheme = { set: set, current: function () { return choice; }, effective: effective };
  function start() { apply(); settings(); setInterval(function () { if (choice === 'auto') apply(); }, 60000); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

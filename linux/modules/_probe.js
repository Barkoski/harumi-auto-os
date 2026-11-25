/* Sonda de teste: so entra com HARUMI_PROBE=1 no servidor. Adiciona o app "Sonda" apenas com ?probe=1 ou window.HARUMI_PROBE. */
(function () {
  'use strict';
  if (!(/[?&]probe=1(&|$)/.test(location.search) || window.HARUMI_PROBE)) return;
  if (window.harumiLinux && window.harumiLinux.addApp) {
    window.harumiLinux.addApp({ id: 'probe', label: 'Sonda', icon: 'ck-apps', run: function () { fetch('/linux/probe').then(function (r) { return r.json(); }).then(function (j) { document.title = 'probe:' + JSON.stringify(j); }); } });
  }
})();

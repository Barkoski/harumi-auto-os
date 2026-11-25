'use strict';
(function(){
// Casca da interface: aba ativa da barra global, espelho de status e fechamento de todas as telas.
function $(id){return document.getElementById(id);}
function shown(id){var e=$(id);return !!e&&!e.hidden;}
var tabs={home:$('hu-tab-home'),harumi:$('hu-tab-harumi'),apps:$('open-apps')};
function sync(){
 var key=shown('apps-panel')?'apps':shown('assistant')?'harumi':'home';
 Object.keys(tabs).forEach(function(name){
  var tab=tabs[name];if(!tab)return;
  var on=name===key;tab.classList.toggle('is-active',on);
  if(on)tab.setAttribute('aria-current','page');else tab.removeAttribute('aria-current');
 });
}
var watch=new MutationObserver(sync);
['apps-panel','assistant','settings','connectivity','brazil-atlas','road-map'].forEach(function(id){var e=$(id);if(e)watch.observe(e,{attributes:true,attributeFilter:['hidden']});});
sync();
// Estado da Harumi: espelha #assistant-status em #hu-harumi-status.
var status=$('assistant-status'),mirror=$('hu-harumi-status');
function copyStatus(){if(status&&mirror)mirror.textContent=status.textContent;}
if(status&&mirror){new MutationObserver(copyStatus).observe(status,{childList:true,characterData:true,subtree:true});copyStatus();}
// Animacao da Harumi: copia data-animation de #harumi-actor para #assistant[data-voice] (onda de voz).
var actor=$('harumi-actor'),sheet=$('assistant');
function copyVoice(){if(actor&&sheet&&actor.dataset.animation)sheet.dataset.voice=actor.dataset.animation;}
if(actor&&sheet){new MutationObserver(copyVoice).observe(actor,{attributes:true,attributeFilter:['data-animation']});copyVoice();}
// Fecha apps, cockpit, atlas, conversa, internet e ajustes (volta para o Inicio).
function closeAll(){
 if(window.harumiApps&&window.harumiApps.isOpen())window.harumiApps.close();
 if(window.harumiRoadMap&&window.harumiRoadMap.isOpen())window.harumiRoadMap.close();
 if(window.harumiAtlas&&window.harumiAtlas.isOpen())window.harumiAtlas.close(false);
 [['assistant','close-assistant'],['connectivity','close-connectivity'],['settings','close']].forEach(function(pair){if(shown(pair[0]))$(pair[1]).click();});
 sync();
}
window.harumiShell={closeAll:closeAll,sync:sync};
})();

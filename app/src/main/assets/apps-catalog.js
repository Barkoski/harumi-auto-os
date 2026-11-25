'use strict';
(function(){
function $(id){return document.getElementById(id);}
var panel=$('apps-panel'),list=$('apps-grid'),installedGrid=$('apps-installed-grid'),install=$('apps-install'),data,inventory={},segment='installed';
var NS='http://www.w3.org/2000/svg';
var TABS={installed:'apps-tab-installed',own:'apps-tab-own',oem:'apps-oem-tab',more:'apps-tab-more'};
// Apps opcionais de terceiros, em ordem. Nada disso e necessario para o basico: a instalacao e opcional, pela loja oficial, um por vez, com confirmacao do Android.
var OPTIONAL=['waze','maps','youtube','spotify'];
// Icones de linha por app (sem icone colorido); o PNG real so aparece quando o Android confirma a instalacao.
var LINE={maps:'ck-nav',waze:'ck-nav',spotify:'ck-music',youtube:'ck-music',chrome:'ck-globe',torque:'ck-car',igo:'ck-nav',gpsmonitor:'ck-nav',radio:'ck-music',localmusic:'ck-music',bluetooth:'ck-bt',camera:'ck-camera',cpaa:'ck-car',claude:'ck-chat',chatgpt:'ck-chat'};
// Recursos proprios da Harumi: ja vem no aplicativo, nao dependem de instalacao.
var OWN=[
 {name:'Navegação própria',icon:'ck-nav',run:function(){if(window.harumiRoadMap)window.harumiRoadMap.open(false);}},
 {name:'Conversa',icon:'ck-chat',run:function(){$('talk').click();}},
 {name:'Atlas do Brasil',icon:'ck-globe',run:function(){$('open-atlas').click();}}
];
function native(){return !!window.HarumiNative;}
function isInstalled(id){return !!(inventory[id]&&inventory[id].installed);}
function missing(){if(!data)return [];return OPTIONAL.map(function(id){return data.apps.filter(function(a){return a.id===id&&a.store;})[0];}).filter(function(a){return a&&!isInstalled(a.id);});}
function updateInstall(){var m=missing();if(segment!=='more'||!native()||!Object.keys(inventory).length){install.hidden=true;return;}install.hidden=false;install.disabled=!m.length;install.textContent=m.length?'Instalar apps opcionais · próximo: '+m[0].name+' ('+m.length+')':'Apps opcionais instalados';}
function action(name,id){window.harumiSend(name,id||'');}
function lineIcon(id){var svg=document.createElementNS(NS,'svg'),use=document.createElementNS(NS,'use');svg.setAttribute('class','ck-ico');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');use.setAttribute('href','#'+id);svg.appendChild(use);return svg;}
// Tile 148x120: circulo de 56px com icone de linha (ou PNG real quando instalado), nome e uma linha de estado.
function tile(opt){
 var wrap=document.createElement('div'),button=document.createElement('button'),ico=document.createElement('span'),title=document.createElement('h3'),status=document.createElement('p');
 wrap.className='app-tile';button.type='button';button.className='app-card';ico.className='app-ico';
 function fallback(){ico.className='app-ico';ico.textContent='';ico.appendChild(lineIcon(opt.line||'ck-apps'));}
 if(opt.img){var img=document.createElement('img');img.alt='';img.src=opt.img;img.onerror=function(){img.onerror=null;fallback();};ico.className='app-ico is-real';ico.appendChild(img);}else fallback();
 title.textContent=opt.name;status.className='app-availability'+(opt.ok?' available':'');status.textContent=opt.status;status.title=opt.status;
 button.appendChild(ico);button.appendChild(title);button.appendChild(status);button.addEventListener('click',opt.run);wrap.appendChild(button);
 if(opt.assign){var assign=document.createElement('button');assign.type='button';assign.className='app-assign';assign.setAttribute('aria-label','Alterar app de '+opt.name);assign.appendChild(lineIcon('ck-settings'));assign.addEventListener('click',opt.assign);wrap.appendChild(assign);}
 return wrap;
}
function ownTile(item){return tile({name:item.name,line:item.icon,status:'Da Harumi',ok:true,run:function(){close();item.run();}});}
function appTile(app){
 var state=inventory[app.id],installed=!!(state&&state.installed),oem=app.group==='oem';
 var text=installed?(state.status||'Instalado'):oem?'Função da central':'Ver na loja';
 return tile({name:app.name,line:LINE[app.id]||'ck-apps',img:installed&&!oem?'app-icons/'+app.id+'.png':'',status:text,ok:installed,run:function(){action('catalog.open',app.id);},assign:oem&&installed?function(){action('catalog.assign',app.id);}:null});
}
function render(){
 if(!data)return;
 list.textContent='';
 if(segment==='own')OWN.forEach(function(item){list.appendChild(ownTile(item));});
 else if(segment==='oem')data.apps.filter(function(a){return a.group==='oem';}).forEach(function(a){list.appendChild(appTile(a));});
 else if(segment==='more')data.apps.filter(function(a){return a.group==='android';}).forEach(function(a){list.appendChild(appTile(a));});
 updateInstall();
}
function select(name){
 segment=name;
 Object.keys(TABS).forEach(function(key){var tab=$(TABS[key]),on=key===name;tab.setAttribute('aria-selected',String(on));tab.tabIndex=on?0:-1;});
 installedGrid.hidden=name!=='installed';list.hidden=name==='installed';
 render();if(name==='installed')updateInstall();
}
function close(){panel.hidden=true;if(window.harumiAvatar)window.harumiAvatar.obscure(false);$('open-apps').focus();}
async function open(){
 ['assistant','settings','connectivity'].forEach(function(id){$(id).hidden=true;});
 if(window.harumiAtlas&&window.harumiAtlas.isOpen())window.harumiAtlas.close(false);
 if(window.harumiRoadMap&&window.harumiRoadMap.isOpen())window.harumiRoadMap.close();
 if(native())action('assistant.cancel.quiet');
 if(window.harumiAvatar){window.harumiAvatar.dock('home');window.harumiAvatar.obscure(true);}
 panel.hidden=false;select(native()?'installed':'own');$('apps-close').focus();
 try{if(!data){var response=await fetch('apps-catalog.json');if(!response.ok)throw new Error();data=await response.json();}render();refresh();}
 catch(e){list.textContent='Não foi possível carregar a lista de aplicativos.';}
}
function refresh(){if(!panel.hidden&&native()){action('catalog.list');if(window.harumiLauncherRefresh)window.harumiLauncherRefresh();}}
window.harumiAppsUpdate=function(rows){inventory={};rows.forEach(function(row){inventory[row.id]=row;});render();};
window.harumiApps={open:open,close:close,isOpen:function(){return !panel.hidden;},refresh:refresh};
$('open-apps').addEventListener('click',open);$('apps-close').addEventListener('click',close);
Object.keys(TABS).forEach(function(key){$(TABS[key]).addEventListener('click',function(){select(key);});});
$('apps-refresh').addEventListener('click',refresh);install.addEventListener('click',function(){var m=missing();if(m.length)action('catalog.store',m[0].id);});$('apps-all').addEventListener('click',function(){action('catalog.all');});
if(new URLSearchParams(location.search).get('apps')==='1')open();
})();

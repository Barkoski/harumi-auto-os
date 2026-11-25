'use strict';
(function(){
function $(id){return document.getElementById(id);}
var grid=$('apps-installed-grid');
var NS='http://www.w3.org/2000/svg';
function lineIcon(id){var svg=document.createElementNS(NS,'svg'),use=document.createElementNS(NS,'use');svg.setAttribute('class','ck-ico');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');use.setAttribute('href','#'+id);svg.appendChild(use);return svg;}
function refresh(){if(window.HarumiNative)window.harumiSend('launcher.list','');}
function empty(text){grid.textContent='';var p=document.createElement('p');p.className='hu-empty';p.textContent=text;grid.appendChild(p);}
function tile(app){
 var wrap=document.createElement('div'),button=document.createElement('button'),ico=document.createElement('span'),img=document.createElement('img'),name=document.createElement('h3');
 wrap.className='app-tile';button.type='button';button.className='app-card';ico.className='app-ico is-real';
 img.alt='';img.src=app.icon;img.onerror=function(){img.onerror=null;ico.classList.remove('is-real');ico.textContent='';ico.appendChild(lineIcon('ck-apps'));};
 ico.appendChild(img);name.textContent=app.name;button.appendChild(ico);button.appendChild(name);
 button.addEventListener('click',function(){window.harumiSend('launcher.open',app.id);});
 wrap.appendChild(button);return wrap;
}
window.harumiLauncherRefresh=refresh;
window.harumiLauncherUpdate=function(data){
 var apps=(data&&data.apps)||[];
 if(!apps.length){empty('Nenhum app com atalho disponível neste Android.');return;}
 grid.textContent='';apps.forEach(function(app){grid.appendChild(tile(app));});
};
empty('Abra o APK para ver os apps deste Android.');
// Navegacao: Inicio, Navegar, Harumi e atalhos da Home.
function openRoad(plan){
 if(window.harumiShell)window.harumiShell.closeAll();
 if(!window.harumiRoadMap)return;
 window.harumiRoadMap.open(false);
 if(plan)plan();else setTimeout(function(){var dest=$('nav-dest');if(dest)dest.focus();},80);
}
function on(id,fn){var e=$(id);if(e)e.addEventListener('click',fn);}
on('home-road-map',function(){openRoad();});
on('hu-tab-nav',function(){openRoad();});
on('hu-cities',function(){openRoad(function(){var toggle=$('ck-cities-toggle');if(toggle&&toggle.getAttribute('aria-expanded')==='false')toggle.click();});});
on('hu-tab-harumi',function(){$('talk').click();});
on('hu-tab-home',function(){if(window.harumiShell)window.harumiShell.closeAll();});
on('settings-internet',function(){$('connections').click();});
refresh();
})();

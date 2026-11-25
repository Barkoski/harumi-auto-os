'use strict';
(function(){
var panel=document.getElementById('brazil-atlas'),select=document.getElementById('atlas-select'),svg=document.getElementById('brazil-map');
var data=window.HARUMI_ATLAS_DATA;if(!panel||!data)return;
var ns='http://www.w3.org/2000/svg',paths={},selected;
function element(name,attrs){var e=document.createElementNS(ns,name);Object.keys(attrs).forEach(function(k){e.setAttribute(k,attrs[k]);});return e;}
data.states.forEach(function(state){
 var path=element('path',{d:state.path,'data-uf':state.uf,tabindex:'0',role:'button','aria-label':state.name+' · capital '+state.capital,'aria-pressed':'false',class:'atlas-state'});
 var title=element('title',{});title.textContent=state.name;path.appendChild(title);
 path.addEventListener('click',function(){choose(state.uf);});path.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(state.uf);}});svg.appendChild(path);paths[state.uf]=path;
 var option=document.createElement('option');option.value=state.uf;option.textContent=state.uf+' — '+state.name;select.appendChild(option);
});
var marker=element('circle',{r:'6',class:'atlas-capital-marker','aria-hidden':'true'});svg.appendChild(marker);
var df=data.states.filter(function(s){return s.uf==='DF';})[0];
var dfHit=element('g',{class:'atlas-df',role:'button',tabindex:'0','aria-label':'Distrito Federal · Brasília'});
dfHit.appendChild(element('circle',{cx:df.capital_point[0],cy:df.capital_point[1],r:'22','class':'df-hit'}));/* alvo de toque maior (estilo em atlas.css; CSP bloqueia style inline) */
 dfHit.appendChild(element('circle',{cx:df.capital_point[0],cy:df.capital_point[1],r:'10'}));
var dfLabel=element('text',{x:df.capital_point[0]+14,y:df.capital_point[1]+5});dfLabel.textContent='DF';dfHit.appendChild(dfLabel);dfHit.addEventListener('click',function(){choose('DF');});dfHit.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();choose('DF');}});svg.appendChild(dfHit);
function choose(uf){
 var state=data.states.filter(function(s){return s.uf===uf;})[0];if(!state)return;selected=state;
 data.states.forEach(function(s){paths[s.uf].classList.toggle('selected',s.uf===uf);paths[s.uf].setAttribute('aria-pressed',String(s.uf===uf));});
 select.value=uf;document.getElementById('atlas-state-name').textContent=state.name;document.getElementById('atlas-uf').textContent=uf;document.getElementById('atlas-capital').textContent=state.capital;
 document.getElementById('atlas-municipalities').textContent=state.municipalities.toLocaleString('pt-BR')+' municípios na base IBGE';
 var photo=document.getElementById('atlas-photo');photo.src=state.photo.file;photo.alt='Vista de '+state.capital+', '+state.name;
 document.getElementById('atlas-photo-author').textContent=state.photo.author||'Autoria indicada na fonte';
 document.getElementById('atlas-photo-license').textContent=state.photo.license;
 var credit=document.getElementById('atlas-photo-source');credit.textContent='Fonte: '+state.photo.source_url;
 document.getElementById('atlas-credits').open=false;marker.setAttribute('cx',state.capital_point[0]);marker.setAttribute('cy',state.capital_point[1]);
 /* No app o DOM storage esta desativado de proposito (MainActivity); o try/catch cobre isso. */
 try{localStorage.setItem('harumi.atlas.uf',uf);}catch(e){}
}
select.addEventListener('change',function(){choose(select.value);});
function close(focus){panel.hidden=true;if(window.harumiAvatar)window.harumiAvatar.obscure(false);if(focus!==false)document.getElementById('open-atlas').focus();}
function open(){
 ['assistant','settings','connectivity'].forEach(function(id){document.getElementById(id).hidden=true;});
 if(window.HarumiNative)window.harumiSend('assistant.cancel.quiet','');
 if(window.harumiAvatar){window.harumiAvatar.dock('home');window.harumiAvatar.obscure(true);}panel.hidden=false;select.focus();
}
window.harumiAtlas={open:open,close:close,isOpen:function(){return !panel.hidden;},select:choose};
document.getElementById('open-atlas').addEventListener('click',open);document.getElementById('atlas-close').addEventListener('click',function(){close();});
document.getElementById('atlas-route').addEventListener('click',function(){window.harumiSend('assistant.ask','Trace uma rota para '+selected.capital+', '+selected.name+', Brasil');});
var initial='PR';try{initial=localStorage.getItem('harumi.atlas.uf')||initial;}catch(e){}choose(paths[initial]?initial:'PR');
if(new URLSearchParams(location.search).get('atlas')==='1')open();
})();

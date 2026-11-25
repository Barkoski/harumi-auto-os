'use strict';
(function(){
/* ===== Funcoes puras da navegacao (testaveis via DevTools: window.HarumiNavCore) ===== */
var Core=(function(){
 var R=6371000,RAD=Math.PI/180;
 var MOD={'uturn':'uturn','sharp left':'sharp_left','left':'left','slight left':'slight_left','straight':'straight','slight right':'slight_right','right':'right','sharp right':'sharp_right'};
 function haversine(a,b){var dLat=(b.lat-a.lat)*RAD,dLon=(b.lon-a.lon)*RAD,x=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(a.lat*RAD)*Math.cos(b.lat*RAD)*Math.sin(dLon/2)*Math.sin(dLon/2);return 2*R*Math.asin(Math.min(1,Math.sqrt(x)));}
 function cumulative(coords){var cum=[0],i;for(i=1;i<coords.length;i++)cum.push(cum[i-1]+haversine({lat:coords[i-1][1],lon:coords[i-1][0]},{lat:coords[i][1],lon:coords[i][0]}));return cum;}
 function scan(coords,cum,p,from,to){
  var cosLat=Math.cos(p.lat*RAD),best=null,i;
  for(i=from;i<=to;i++){
   var ax=(coords[i][0]-p.lon)*cosLat*RAD*R,ay=(coords[i][1]-p.lat)*RAD*R,bx=(coords[i+1][0]-p.lon)*cosLat*RAD*R,by=(coords[i+1][1]-p.lat)*RAD*R;
   var dx=bx-ax,dy=by-ay,l2=dx*dx+dy*dy,t=l2>0?(-(ax*dx+ay*dy))/l2:0;t=Math.max(0,Math.min(1,t));
   var px=ax+t*dx,py=ay+t*dy,off=Math.sqrt(px*px+py*py);
   if(!best||off<best.off)best={seg:i,t:t,off:off,s:cum[i]+t*(cum[i+1]-cum[i])};
  }
  return best;
 }
 /* Projeta p={lat,lon} na polilinha coords([lon,lat]) com acumuladas cum. Retorna {seg,t,off(m),s(m ao longo da linha)}. */
 function project(coords,cum,p,hintSeg,windowM){
  var n=coords.length-1;if(n<1)return null;
  if(hintSeg==null||isNaN(hintSeg))return scan(coords,cum,p,0,n-1);
  var h=Math.max(0,Math.min(n-1,hintSeg)),from=Math.max(0,h-3),to=h;
  while(to<n-1&&cum[to]-cum[h]<(windowM||400))to++;
  var r=scan(coords,cum,p,from,to);if(r.off<=50)return r;
  var g=scan(coords,cum,p,0,n-1);return g.off<r.off?g:r;
 }
 function fmtDist(m){
  if(!isFinite(m)||m<0)m=0;
  if(m<1000){var r=m<100?Math.round(m/10)*10:Math.round(m/50)*50;if(r<10)r=10;if(r>=1000)return '1,0 km';return r+' m';}
  var km=m/1000;return (km<10?km.toFixed(1):String(Math.round(km))).replace('.',',')+' km';
 }
 function fmtDur(sec){
  var min=Math.max(1,Math.round(sec/60));if(min<60)return min+' min';
  var h=Math.floor(min/60),mm=min%60;return h+' h '+(mm<10?'0':'')+mm+' min';
 }
 /* codigo de fala [a-z0-9_] para a manobra OSRM, ou null quando nao ha instrucao a dar */
 function speechCode(type,modifier,exit){
  var m=MOD[modifier]||null;
  switch(type){
   case 'arrive':return 'arrive';
   case 'depart':case 'new name':case 'notification':case 'exit roundabout':case 'exit rotary':return null;
   case 'roundabout':case 'rotary':
    if(typeof exit==='number'&&isFinite(exit)&&exit>=1)return 'roundabout_'+Math.min(5,Math.floor(exit));
    return m;
   case 'fork':case 'merge':
    if(m==='left'||m==='slight_left'||m==='sharp_left')return 'keep_left';
    if(m==='right'||m==='slight_right'||m==='sharp_right')return 'keep_right';
    return type==='fork'?m:null;
   case 'continue':return m==='straight'?null:m;
   default:return m;
  }
 }
 /* velocidade (km/h) -> zoom: <30 z17, <70 z16, <100 z15, senao z14 */
 function zoomForSpeed(kmh){return kmh<30?17:kmh<70?16:kmh<100?15:14;}
 /* decide a fala de distancia (ou null). Marca os niveis ja cruzados em said (um objeto por step). */
 function nextSpeech(said,d,kmh,code){
  if(code==='arrive')return null;
  var levels=[{t:1000,c:'d1k',min:100},{t:500,c:'d500',min:70},{t:200,c:'d200',min:0},{t:30,c:'now',min:0}],out=null,i,L;
  for(i=0;i<levels.length;i++){L=levels[i];
   if(d<=L.t&&!said[L.t]){said[L.t]=true;if((L.min===0||kmh>L.min)&&(L.t===30||d>=L.t*0.5))out=L.c;}
  }
  return out;
 }
 var LANE={'left':'left','slight left':'slight_left','sharp left':'sharp_left','straight':'straight','right':'right','slight right':'slight_right','sharp right':'sharp_right','uturn':'uturn','none':'straight'};
 function lanesOf(st){
  var ix=st.intersections&&st.intersections[0],ls=ix&&ix.lanes;if(!Array.isArray(ls)||!ls.length)return null;
  return ls.map(function(l){var ind=(l&&Array.isArray(l.indications)?l.indications:[]).map(function(x){return LANE[x]||'straight';});if(!ind.length)ind=['straight'];return {ind:ind,valid:!!(l&&l.valid)};});
 }
 /* rota OSRM -> {coords,cum,total,duration,man:[{at,code,type,name}]} */
 function buildRoute(route){
  var coords=route.geometry.coordinates,cum=cumulative(coords),total=cum[cum.length-1];
  var steps=(route.legs&&route.legs[0]&&route.legs[0].steps)||[],sum=0,i,man=[],at=0;
  for(i=0;i<steps.length;i++)sum+=steps[i].distance||0;
  var scale=sum>0?total/sum:1;
  for(i=0;i<steps.length;i++){
   var st=steps[i],mv=st.maneuver||{},start=at,code;at+=(st.distance||0)*scale;
   code=speechCode(mv.type,mv.modifier,mv.exit);if(!code)continue;
   var mo={at:code==='arrive'?total:start,code:code,type:mv.type,name:st.name||'',said:{}},ln=code==='arrive'?null:lanesOf(st);if(ln)mo.lanes=ln;man.push(mo);
  }
  if(!man.length||man[man.length-1].code!=='arrive')man.push({at:total,code:'arrive',type:'arrive',name:'',said:{}});
  return {coords:coords,cum:cum,total:total,duration:route.duration||0,man:man};
 }
 return {haversine:haversine,cumulative:cumulative,project:project,fmtDist:fmtDist,fmtDur:fmtDur,speechCode:speechCode,lanesOf:lanesOf,zoomForSpeed:zoomForSpeed,nextSpeech:nextSpeech,buildRoute:buildRoute};
})();
window.HarumiNavCore=Core;

var panel=document.getElementById('road-map'),opener,map,m3=null,initWait=false,planState=null,tiles,line,markers=[],request=0,abort,from=document.getElementById('route-from'),to=document.getElementById('route-to');
var cities=window.HARUMI_CITIES||[],status=document.getElementById('route-status'),result=document.getElementById('route-result');
var states=(window.HARUMI_ATLAS_DATA||{states:[]}).states;
function $(id){return document.getElementById(id);}
function norm(s){return s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();}
function label(c){return c.name+' / '+c.uf;}
function resolve(text){
 var n=norm(text),found=cities.filter(function(c){var name=norm(c.name);var state=states.filter(function(s){return s.uf===c.uf;})[0];var tail=n.indexOf(name+' ')===0?n.slice(name.length+1).replace(/^(?:(?:no|na|em) (?:estado de )?|estado de )/,''):'';return n===name||tail===c.uf.toLowerCase()||state&&tail===norm(state.name);});
 return found.length===1?found[0]:null;
}
var locked=false;
function suggestions(input,list){
 input.addEventListener('input',function(){
  var n=norm(input.value);list.textContent='';
  request++;if(abort)abort.abort();clearRoute();$('calculate-route').disabled=locked;status.textContent='Escolha as cidades e toque em Traçar rota.';
  if(n.length<2)return;
  cities.filter(function(c){return norm(label(c)).indexOf(n)!==-1||norm(c.name).indexOf(n)!==-1;}).slice(0,15).forEach(function(c){var option=document.createElement('option');option.value=label(c);list.appendChild(option);});
 });
}
suggestions(from,$('route-from-options'));suggestions(to,$('route-to-options'));
function clearRoute(){if(line){line.remove();line=null;}markers.forEach(function(m){m.remove();});markers=[];planState=null;result.hidden=true;$('route-origin-note').hidden=true;panel.classList.remove('has-route');renderNearby(false);}
/* ===== Escolha do motor: 3D (MapLibre, map3d.js) com Leaflet 2D como reserva automatica ===== */
var CREDIT_2D='© OpenStreetMap contributors (ODbL) · Rotas: OSRM',CREDIT_3D='© OpenStreetMap · OpenFreeMap · Rotas: OSRM',gl2=null,failed3d=false; // sem DOM storage no WebView (localStorage nulo) a falha tambem fica em memoria
function webgl2(){
 if(gl2!==null)return gl2;
 try{var c=document.createElement('canvas'),g=c.getContext('webgl2');gl2=!!g;if(g){var x=g.getExtension('WEBGL_lose_context');if(x)x.loseContext();}}catch(e){gl2=false;}
 return gl2;
}
var pref=null,switching=false; // escolha do motorista (2D/3D) nesta sessao: '2d' | '3d'; tambem em localStorage quando existir
function want3d(){
 if(pref==='3d')return webgl2(); // pediu 3D de proposito: tenta mesmo depois de uma falha anterior
 if(pref==='2d'||failed3d)return false;
 try{if(localStorage.getItem('harumi.map3d')==='0')return false;}catch(e){}
 try{if(sessionStorage.getItem('harumi.map3d.failed')==='1')return false;}catch(e){}
 return webgl2();
}
function engine(){return m3?'3d':map?'2d':'';}
function resize(){if(m3)m3.resize();else if(map)map.invalidateSize();}
function init(){
 if(map||m3||initWait)return;
 if(want3d()&&!window.HarumiMap3D&&document.readyState!=='complete'){
  /* o modulo map3d.js ainda nao carregou: espera ele (ou o fim do carregamento da pagina) antes de escolher o motor */
  initWait=true;
  var go=function(){if(!initWait)return;initWait=false;window.removeEventListener('harumi-map3d-ready',go);window.removeEventListener('load',go);init();resize();if(!navActive)frameHere();};
  window.addEventListener('harumi-map3d-ready',go);window.addEventListener('load',go);return;
 }
 if(want3d()&&window.HarumiMap3D&&init3d())return;
 init2d();
}
function init3d(){
 try{
  m3=window.HarumiMap3D.create($('route-canvas'),{
   onDrag:function(){userMoved();},
   onStatus:function(ok){$('route-map-network').hidden=ok;},
   onIdle:function(){renderNearby(false);},
   onFail:function(why){setTimeout(function(){fallback(why);},0);}
  });
 }catch(e){m3=null;return false;}
 $('nav-credit').textContent=CREDIT_3D;panel.classList.add('map-3d');refreshEngine();
 return true;
}
/* 3D falhou (WebGL, worker, estilo): lembra na sessao e refaz tudo no Leaflet, preservando rota planejada e navegacao em curso */
function fallback(why){
 if(!m3)return;
 failed3d=true;pref='2d'; // o botao 2D/3D continua oferecendo uma nova tentativa
 try{sessionStorage.setItem('harumi.map3d.failed','1');}catch(e){}
 try{console.warn('Mapa 3D indisponivel, usando o 2D:',why);}catch(e){}
 toLeaflet(false);
}
/* Refaz o mapa no Leaflet 2D preservando rota planejada e navegacao em curso (falha do 3D ou escolha do motorista) */
function toLeaflet(user){
 var old=m3;m3=null;try{old.destroy();}catch(e){}
 $('route-canvas').textContent='';$('route-canvas').className='';panel.classList.remove('map-3d');$('route-map-network').hidden=true;
 line=null;markers=[];carMarker=null;navLine=null;navCasing=null;navDone=null;destMarker=null;
 init2d();refreshEngine();
 if(planState)drawPlan(planState.geometry,planState.origin,planState.destination);
 if(navActive){
  map.setMaxZoom(17);enterRotate();
  if(dest)destMarker=makeDest(dest);
  if(route)drawNavRoute();
  if(lastFix){updateCar(lastFix);follow(lastFix,true);}
 }else if(user&&!planState)frameHere();
 setTimeout(function(){map.invalidateSize();},60);
}
/* Volta ao 3D (MapLibre) a partir do Leaflet, simetrico ao toLeaflet(): desmonta o 2D e redesenha rota planejada ou navegacao */
function toMapLibre(){
 if(m3||!map||!window.HarumiMap3D||!webgl2())return false;
 if(rotating)exitRotate();
 var old=map;map=null;tiles=null;try{old.remove();}catch(e){}
 $('route-canvas').textContent='';$('route-canvas').className='';$('route-map-network').hidden=true;
 line=null;markers=[];carMarker=null;navLine=null;navCasing=null;navDone=null;destMarker=null;
 if(!init3d()){init2d();refreshEngine();if(planState)drawPlan(planState.geometry,planState.origin,planState.destination);return false;}
 if(planState)drawPlan(planState.geometry,planState.origin,planState.destination);
 if(navActive){
  m3.setMode('nav');
  if(dest)destMarker=makeDest(dest);
  if(route)drawNavRoute();
  if(lastFix){updateCar(lastFix);follow(lastFix,true);}
 }else if(!planState)frameHere();
 return true;
}
function setPref(v){pref=v;try{localStorage.setItem('harumi.map3d',v==='3d'?'1':'0');}catch(e){}} // WebView do app: sem DOM storage, fica so em memoria
function switchEngine(target){
 if(switching||(target==='2d'&&!m3)||(target==='3d'&&(m3||!map||!window.HarumiMap3D||!webgl2())))return false;
 switching=true;
 try{
  setPref(target);
  if(target==='2d')toLeaflet(true);
  else{failed3d=false;try{sessionStorage.removeItem('harumi.map3d.failed');}catch(e){}toMapLibre();}
 }finally{switching=false;}
 refreshEngine();renderNearby(true);setTimeout(resize,60);
 return true;
}
function init2d(){
 if(map)return;
 map=L.map('route-canvas',{zoomControl:false,attributionControl:true}).setView([-18,-52],5);
 $('nav-credit').textContent=CREDIT_2D;refreshEngine();
 L.control.zoom({position:'bottomright'}).addTo(map);
 tiles=L.tileLayer('map-api/tiles/{z}/{x}/{y}.png',{maxZoom:18,minZoom:3,attribution:'© OpenStreetMap contributors (ODbL)',keepBuffer:0,updateWhenIdle:true}).addTo(map);
 var failures=0;tiles.on('tileerror',function(){failures++;$('route-map-network').hidden=false;});tiles.on('loading',function(){failures=0;});tiles.on('load',function(){if(!failures)$('route-map-network').hidden=true;});
 map.on('dragstart',userMoved);
}
function debugOn(){return location.search.indexOf('debug=1')!==-1||window.HARUMI_DEBUG===true;}
function refreshDebug(){var on=debugOn();Array.prototype.forEach.call(panel.querySelectorAll('.nav-replay-btn'),function(b){b.hidden=!on;});}
function setCities(on){$('route-form').hidden=!on;$('ck-cities-toggle').setAttribute('aria-expanded',on?'true':'false');renderNearby(false);}
function openCities(){setCities(true);}
function refreshEngine(){
 $('ck-engine').textContent=m3?'3D':map?'2D':'';
 var b=$('ck-view'),can=!!(m3||(map&&window.HarumiMap3D&&webgl2())); // o botao mostra o modo para onde vai trocar
 b.hidden=!can;
 if(can){b.firstChild.textContent=m3?'2D':'3D';b.setAttribute('aria-label',m3?'Mudar para o mapa 2D':'Mudar para o mapa 3D');b.title=m3?'Ver o mapa em 2D':'Ver o mapa em 3D';}
}
window.addEventListener('harumi-map3d-ready',refreshEngine);
var BRASIL={lat:-14.235,lon:-51.925};
/* Enquadra a posicao do carro (z13); sem fix usavel mostra o Brasil inteiro (z4), sem inventar posicao. frame() existe so em versoes novas do map3d.js */
function frameHere(){
 var ok=usableFix();
 if(m3){
  if(ok){if(typeof m3.frame==='function')m3.frame(lastFix.lat,lastFix.lon,15,30);else m3.setView(lastFix.lat,lastFix.lon,13);}
  else m3.setView(BRASIL.lat,BRASIL.lon,4);
 }else if(map){
  if(ok)map.setView([lastFix.lat,lastFix.lon],13,{animate:false});else map.setView([BRASIL.lat,BRASIL.lon],4,{animate:false});
 }
}
function tickClock(){var d=new Date();$('ck-clock').textContent=pad2(d.getHours())+':'+pad2(d.getMinutes());}
function syncNet(){var n=$('network-short');$('ck-net').textContent=n?n.textContent:'';}
/* A navegacao sempre parte da posicao GPS atual, nao da origem digitada: o botao e o aviso dizem isso. O GPS so liga em nav.start: sem fix a navegacao espera o sinal (Aguardando sinal do GPS) */
function nearestCity(p){var best=null,bd=Infinity;cities.forEach(function(c){var d=Core.haversine(p,c);if(d<bd){bd=d;best=c;}});return best;}
var fromTouched=false;
function fillFrom(){if(fromTouched||from.value.trim()||!usableFix())return;var c=nearestCity(lastFix);if(c)from.value=label(c);}
function updateStart(){
 var b=$('route-start'),n=$('route-origin-note');b.disabled=false;
 if(!planState){b.textContent='Iniciar navegação';n.hidden=true;return;}
 var dn=label(planState.destination),on=label(planState.origin);
 if(!usableFix()){n.textContent='A navegação parte da sua posição atual quando o GPS responder.';n.hidden=false;b.textContent='Navegar até '+dn;return;}
 if(Core.haversine(lastFix,planState.origin)>25000){
  var c=nearestCity(lastFix);
  n.textContent='A navegação parte da sua posição atual (perto de '+(c?label(c):'onde você está')+'), não de '+on+'.';n.hidden=false;b.textContent='Navegar daqui até '+dn;return;
 }
 n.hidden=true;b.textContent='Iniciar navegação';
}
function open(cancel){
 ['assistant','settings','connectivity'].forEach(function(id){$(id).hidden=true;});
 if(window.harumiAtlas&&window.harumiAtlas.isOpen())window.harumiAtlas.close(false);
 if(cancel!==false&&window.HarumiNative)window.harumiSend('assistant.cancel.quiet','');
 if(window.harumiAvatar){window.harumiAvatar.dock('home');window.harumiAvatar.obscure(true);}
 opener=document.activeElement;panel.hidden=false;init();refreshDebug();refreshEngine();tickClock();syncNet();
 if(!navActive){setStatus('');fillFrom();frameHere();}
 renderNearby(true);setTimeout(resize,60);
}
function close(){stopNav();searchId++;request++;if(abort)abort.abort();$('calculate-route').disabled=locked;panel.hidden=true;if(window.harumiAvatar)window.harumiAvatar.obscure(false);var back=opener;opener=null;if(back&&back!==document.body&&document.body.contains(back)&&back.offsetParent!==null&&back.focus)back.focus();else $('open-road-map').focus();}
function fitPad(){
 var w=panel.clientWidth||1024,h=panel.clientHeight||600;
 if(w<=600){var col=panel.querySelector('.ck-left'),cb=col?Math.round(col.getBoundingClientRect().bottom)+16:Math.round(h*0.5);return {top:Math.min(cb,Math.round(h*0.65)),left:40,right:40,bottom:100};}
 return {top:60,left:w<=900?330:380,right:40,bottom:110};
}
function fit(){
 if(!line||!planState)return;var pad=fitPad();
 if(m3)m3.fitBounds(planState.geometry.coordinates,{padding:pad,maxZoom:13});
 else map.fitBounds(line.getBounds(),{paddingTopLeft:[pad.left,pad.top],paddingBottomRight:[pad.right,pad.bottom],maxZoom:13});
}
function point(city,letter){if(m3)return m3.addPin(city.lat,city.lon,letter,label(city));return L.marker([city.lat,city.lon],{icon:L.divIcon({className:'route-pin',html:letter,iconSize:[30,30],iconAnchor:[15,15]})}).addTo(map).bindTooltip(label(city),{direction:'top'});}
function drawPlan(geometry,origin,destination){
 if(m3){m3.setRoute(geometry.coordinates);line={remove:function(){m3&&m3.clearRoute();}};}
 else line=L.geoJSON(geometry,{style:{color:'#d9a0c3',weight:6,opacity:1,lineJoin:'round'}}).addTo(map);
 markers=[point(origin,'A'),point(destination,'B')];fit();
}
async function calculate(){
 openCities();
 if(locked){status.textContent='Pare o carro para digitar.';return;}
 if(!from.value.trim()){fromTouched=false;fillFrom();}
 var origin=resolve(from.value),destination=resolve(to.value);request++;if(abort)abort.abort();var id=request;clearRoute();
 if(!origin||!destination){status.textContent='Escolha uma cidade e sua UF nas sugestões. A busca atual é por centros de cidades brasileiras.';return;}
 if(origin.id===destination.id){status.textContent='Escolha cidades diferentes para origem e destino.';return;}
 from.value=label(origin);to.value=label(destination);
 status.textContent='Calculando o trajeto pelas vias…';$('calculate-route').disabled=true;
 abort=new AbortController();var controller=abort;var timeout=setTimeout(function(){controller.abort();},25000);
 try{
  var coords=[origin.lon,origin.lat,destination.lon,destination.lat].join(',');
  var response=await fetch('map-api/route?points='+encodeURIComponent(coords),{signal:abort.signal});
  if(!response.ok)throw new Error('network');var data=await response.json();
  if(id!==request)return;
  if(data.code!=='Ok'||!data.routes||!data.routes.length)throw new Error('no-route');
  var route=data.routes[0];if(!route.geometry||route.geometry.type!=='LineString'||route.geometry.coordinates.length<2)throw new Error('geometry');
  planState={geometry:route.geometry,origin:origin,destination:destination};
  $('route-distance').textContent=Math.round(route.distance/1000).toLocaleString('pt-BR')+' km';
  var minutes=Math.round(route.duration/60);$('route-duration').textContent=Math.floor(minutes/60)+' h '+(minutes%60)+' min';
  var arr=new Date(Date.now()+route.duration*1000);$('route-arrive').textContent=pad2(arr.getHours())+':'+pad2(arr.getMinutes());
  $('route-endpoints').textContent=label(origin)+' → '+label(destination);updateStart();
  result.hidden=false;panel.classList.add('has-route');setCities(false);renderNearby(false);$('nav-results').textContent='';setStatus(''); // recolhe o formulario e a lista: a previa ocupa o lugar deles
  status.textContent=(data.cached?'Rota em cache de '+new Date(data.computedAt).toLocaleDateString('pt-BR')+' · ':'Rota calculada · ')+'Estimativa de carro, sem trânsito em tempo real. Confira o trajeto antes de sair.';
  drawPlan(route.geometry,origin,destination); // depois da previa: o enquadramento ja considera a altura dos cartoes
 }catch(e){if(id===request){clearRoute();status.textContent='Não foi possível calcular a rota. Confira a Internet e tente novamente. Nenhum trajeto foi inventado.';}}
 finally{clearTimeout(timeout);if(id===request)$('calculate-route').disabled=locked;}
}

/* ===== Navegacao propria ===== */
var navActive=false,following=true,lastFix=null,fixAt=0,dest=null,route=null,routeReq=0,routeCtl=null,requesting=false,routeFailed=false;
var offCount=0,lastRecalc=0,recalcDelay=10000,offEpisode=false,recalcSaidAt=0,arrived=false,arrivalTimer=0,nextMan=0,carMarker=null,navLine=null,destMarker=null,searchId=0,searchCtl=null;
var zoomTarget=0,zoomChangedAt=0,lastBearing=0,msgKind='',gpsReason='';
var navCasing=null,navDone=null,doneAt=0,mapRot=0,carCum=0,rotating=false,lanesFor=null,nextFor=-1;
function angDiff(a,b){return (((a-b+180)%360)+360)%360-180;}
function reduced(){return !!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);}
function rotateAllowed(){try{if(window.HARUMI_NO_ROTATE===true||localStorage.getItem('harumi.navRotate')==='0')return false;}catch(e){}return true;}
var MAN_ARROW={left:'↰',right:'↱',slight_left:'↖',slight_right:'↗',sharp_left:'↙',sharp_right:'↘',straight:'↑',uturn:'↩',keep_left:'↖',keep_right:'↗',arrive:'●',recalc:'↻'};
var MAN_TEXT={left:'Vire à esquerda',right:'Vire à direita',slight_left:'Curva suave à esquerda',slight_right:'Curva suave à direita',sharp_left:'Curva fechada à esquerda',sharp_right:'Curva fechada à direita',straight:'Siga em frente',uturn:'Faça o retorno',keep_left:'Mantenha-se à esquerda',keep_right:'Mantenha-se à direita',arrive:'Você chegou ao destino'};
function icon(code){
 var fr=document.createDocumentFragment(),m=/^roundabout_([1-9])$/.exec(code),id=m?'roundabout':String(code);
 if(!/^[a-z_0-9]+$/.test(id)||!(id==='roundabout'||MAN_ARROW.hasOwnProperty(id)))id='straight';
 var ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg'),use=document.createElementNS(ns,'use');
 svg.setAttribute('aria-hidden','true');use.setAttribute('href','#m-'+id);svg.appendChild(use);fr.appendChild(svg);
 if(m){var sp=document.createElement('span');sp.className='rb-exit';sp.textContent=m[1];fr.appendChild(sp);}
 return fr;
}
function setIcon(el,code){el.textContent='';el.appendChild(icon(code));}
function manText(code){var m=/^roundabout_(\d)$/.exec(code);return m?'Rotatória · saída '+m[1]:(MAN_TEXT[code]||'');}
function send(a,m){if(typeof window.harumiSend==='function')window.harumiSend(a,m||'');}
function sayManeuver(distCode,code){if(distCode)send('nav.say',distCode);send('nav.say',code);}
function pad2(n){return (n<10?'0':'')+n;}
function usableFix(){return !!lastFix&&(lastFix.quality==='OK'||lastFix.quality==='FRACO')&&Date.now()-fixAt<5000;}
function showMsg(text,retry,kind){msgKind=kind||'';$('nav-msg-text').textContent=text;$('nav-retry').hidden=!retry;$('nav-msg').hidden=false;}
function hideMsg(kind){if(kind&&msgKind!==kind)return;msgKind='';$('nav-msg').hidden=true;}
function setLock(on){
 if(on===locked)return;locked=on;
 ['nav-dest','nav-search','route-from','route-to','swap-route','calculate-route'].forEach(function(id){$(id).disabled=on;});
 $('nav-lock').hidden=!on;
 if(on&&document.activeElement&&document.activeElement.tagName==='INPUT')document.activeElement.blur();
}
function setStatus(t){$('nav-search-status').textContent=t;}
function renderIdle(){
 $('nav-arrow').textContent='…';hideHud();$('nav-dist').textContent='—';$('nav-street').textContent=dest?dest.name:'';
 $('nav-eta').textContent='--:--';$('nav-rem').textContent='—';$('nav-time').textContent='—';
}
function hideHud(){$('nav-next').hidden=true;$('nav-lanes').hidden=true;lanesFor=null;nextFor=-1;var i=document.querySelector('#nav-progress i');if(i)i.style.width='0';}
function sizeCanvas(){
 if(!rotating||!map)return;
 var cv=$('route-canvas'),w=cv.parentNode,W=w.clientWidth,H=w.clientHeight,s=Math.ceil(Math.sqrt(W*W+H*H));
 cv.style.width=s+'px';cv.style.height=s+'px';cv.style.left=Math.round((W-s)/2)+'px';cv.style.top=Math.round((H-s)/2)+'px';map.invalidateSize();
}
function enterRotate(){
 if(!rotateAllowed()||rotating)return;
 var cv=$('route-canvas');rotating=true;mapRot=0;
 cv.parentNode.style.overflow='hidden';cv.style.position='absolute';cv.style.transformOrigin='50% 50%';cv.style.transition=reduced()?'none':'transform .6s ease';cv.style.transform='rotate(0deg)';
 if(map)map.dragging.disable(); // arrastar com o mapa girado anda na direcao da tela, nao do mapa
 sizeCanvas();
}
function exitRotate(){
 if(!rotating)return;
 var cv=$('route-canvas');rotating=false;mapRot=0;
 ['position','width','height','left','top','transform','transition','transformOrigin'].forEach(function(k){cv.style[k]='';});
 if(map){map.dragging.enable();map.invalidateSize();}
}
window.addEventListener('resize',function(){if(navActive)sizeCanvas();});
function enterNav(){
 navActive=true;following=true;panel.classList.add('nav-on');$('nav-hud').hidden=false;$('nav-recenter').hidden=true;$('nav-gps').hidden=true;
 refreshDebug();if(m3){m3.setMode('nav');}else if(map){map.setMaxZoom(17);enterRotate();}send('nav.start','');setTimeout(resize,60);
}
function clearNavLayers(){
 clearRouteLines();if(destMarker){destMarker.remove();destMarker=null;}if(carMarker){carMarker.remove();carMarker=null;}if(m3)m3.clearCar();
}
function stopNav(){
 if(!navActive)return;
 navActive=false;routeReq++;if(routeCtl)routeCtl.abort();requesting=false;clearTimeout(arrivalTimer);
 dest=null;route=null;arrived=false;routeFailed=false;offCount=0;
 clearNavLayers();hideHud();exitRotate();if(m3)m3.setMode('plan');else if(map)map.setMaxZoom(18);panel.classList.remove('nav-on');$('nav-hud').hidden=true;hideMsg();
 send('nav.stop','');setStatus('');frameHere();renderNearby(true);
 setTimeout(resize,60);
}
function startNav(d){
 searchId++;$('nav-results').textContent='';
 if(navActive){routeReq++;if(routeCtl)routeCtl.abort();requesting=false;clearTimeout(arrivalTimer);clearNavLayers();}
 else enterNav();
 recenter();
 dest=d;route=null;arrived=false;routeFailed=false;offCount=0;nextMan=0;lastRecalc=0;recalcDelay=10000;offEpisode=false;recalcSaidAt=0;
 renderIdle();
 destMarker=makeDest(d);
 if(usableFix()){updateCar(lastFix);follow(lastFix,true);requestRoute(false);}
 else showMsg(gpsReason?'GPS indisponível: '+gpsReason:'Aguardando sinal do GPS…',false,'wait');
 renderNearby(true);
}
function makeDest(d){
 if(m3)return m3.addPin(d.lat,d.lon,'B',d.name);
 return L.marker([d.lat,d.lon],{icon:L.divIcon({className:'route-pin',html:'<span class="pin-t">B</span>',iconSize:[30,30],iconAnchor:[15,15]}),interactive:false,keyboard:false}).addTo(map);
}
function drawNavRoute(){
 clearRouteLines();
 if(m3){m3.setRoute(route.coords);doneAt=0;return;}
 var ll=route.ll||(route.ll=route.coords.map(function(c){return [c[1],c[0]];}));
 navCasing=L.polyline(ll,{color:'#3a2f3d',weight:12,opacity:1,lineJoin:'round',lineCap:'round',interactive:false}).addTo(map);
 navLine=L.polyline(ll,{color:'#d9a0c3',weight:7,opacity:1,lineJoin:'round',lineCap:'round',interactive:false}).addTo(map);
 navDone=L.polyline([],{color:'#7a6678',weight:7,opacity:1,lineJoin:'round',lineCap:'round',interactive:false}).addTo(map);doneAt=0;
}
async function requestRoute(recalc){
 if(requesting||!dest||!lastFix||!navActive)return;
 requesting=true;var id=++routeReq,f=lastFix,d=dest;
 routeCtl=new AbortController();var ctl=routeCtl,timeout=setTimeout(function(){ctl.abort();},20000);
 showMsg(recalc?'Recalculando a rota…':'Calculando a rota…',false,'route');
 try{
  var url='map-api/route?points='+encodeURIComponent([f.lon,f.lat,d.lon,d.lat].join(','));
  if(isFinite(f.bearing)&&f.bearing>=0)url+='&bearing='+Math.round(f.bearing);
  var response=await fetch(url,{signal:ctl.signal});
  if(!response.ok)throw new Error('network');var data=await response.json();
  if(id!==routeReq||!navActive)return;
  if(data.code!=='Ok'||!data.routes||!data.routes.length)throw new Error('no-route');
  var r=data.routes[0];if(!r.geometry||r.geometry.type!=='LineString'||!r.geometry.coordinates||r.geometry.coordinates.length<2)throw new Error('geometry');
  route=Core.buildRoute(r);route.seg=0;route.s=0;nextMan=0;offCount=0;routeFailed=false;
  route.ll=route.coords.map(function(c){return [c[1],c[0]];});
  drawNavRoute();
  hideMsg('route');
  guide(lastFix);
 }catch(e){
  if(id===routeReq&&navActive){
   if(recalc&&route){showMsg('Não foi possível recalcular. Seguindo a rota anterior.',false,'route');}
   else{routeFailed=true;showMsg('Não foi possível calcular a rota. Confira a Internet. Nenhum trajeto foi inventado.',true,'route');}
  }
 }
 finally{clearTimeout(timeout);if(id===routeReq)requesting=false;}
}
function clearRouteLines(){if(m3)m3.clearRoute();if(navLine){navLine.remove();navLine=null;}if(navCasing){navCasing.remove();navCasing=null;}if(navDone){navDone.remove();navDone=null;}}
function updateDone(p){
 if(!route||!route.ll||(!m3&&!navDone))return;var now=Date.now();if(now-doneAt<(m3?1000:400))return;doneAt=now;
 if(m3){
  /* 3D: so o rastro recente (ate ~4 km atras do carro) e redesenhado; o resto fica fora da tela e reenviar a rota inteira custaria caro */
  var c=route.coords,j=p.seg,lim=route.cum[p.seg]-4000;while(j>0&&route.cum[j]>lim)j--;
  var tr=c.slice(j,p.seg+1),q=c[p.seg],r=c[p.seg+1]||q;tr.push([q[0]+(r[0]-q[0])*p.t,q[1]+(r[1]-q[1])*p.t]);m3.setDone(tr);return;
 }
 var a=route.ll[p.seg],b=route.ll[p.seg+1]||a,arr=route.ll.slice(0,p.seg+1);arr.push([a[0]+(b[0]-a[0])*p.t,a[1]+(b[1]-a[1])*p.t]);navDone.setLatLngs(arr);
}
function carIcon(){return L.divIcon({className:'nav-car-icon',html:'<div class="nav-car"></div>',iconSize:[44,44],iconAnchor:[22,22]});}
function updateCar(f){
 var ll=[f.lat,f.lon];
 if(isFinite(f.bearing)&&f.bearing>=0&&f.speedMps>1)lastBearing=f.bearing;
 if(m3){carCum+=angDiff(lastBearing,carCum);m3.setCar(f.lat,f.lon,carCum);return;}
 if(!carMarker)carMarker=L.marker(ll,{icon:carIcon(),interactive:false,keyboard:false,zIndexOffset:1000}).addTo(map);else carMarker.setLatLng(ll);
 if(isFinite(f.bearing)&&f.bearing>=0&&f.speedMps>1)lastBearing=f.bearing;
 if(rotating&&f.speedMps>2&&isFinite(f.bearing)&&f.bearing>=0){var dd=angDiff(f.bearing,mapRot);if(Math.abs(dd)>3){mapRot+=dd;$('route-canvas').style.transform='rotate('+(-mapRot)+'deg)';if(destMarker){var pe=destMarker.getElement&&destMarker.getElement(),sp=pe&&pe.querySelector('.pin-t');if(sp)sp.style.transform='rotate('+mapRot+'deg)';}}}
 // o marcador vive dentro do container girado: apontar para o rumo real (referencial do mapa) deixa o carro para cima quando rumo == rotacao do mapa
 carCum+=angDiff(lastBearing,carCum);
 var el=carMarker.getElement?carMarker.getElement():carMarker._icon,car=el&&el.firstChild;
 if(car){car.style.transition=reduced()?'none':'transform .6s ease';car.style.transform='rotate('+Math.round(carCum)+'deg)';}
}
function follow(f,force){
 if(!following&&!force)return;
 var kmh=(f.speedMps||0)*3.6,z=Core.zoomForSpeed(kmh);if(kmh>=8)z=Math.min(z,16);
 var now=Date.now();
 if(!zoomTarget||(z!==zoomTarget&&now-zoomChangedAt>6000)){zoomTarget=z;zoomChangedAt=now;}
 if(m3){m3.follow(f.lat,f.lon,lastBearing,kmh,{zoom:zoomTarget,force:!!force});return;}
 var c=L.latLng(f.lat,f.lon),H=$('route-canvas').parentNode.clientHeight,off=0.12*H,a=(rotating?mapRot:lastBearing)*Math.PI/180;
 if(navActive&&H>0&&(rotating||(f.speedMps||0)>2)){var pt=map.project(c,zoomTarget).add([Math.sin(a)*off,-Math.cos(a)*off]);c=map.unproject(pt,zoomTarget);}
 map.setView(c,zoomTarget,{animate:!force,duration:0.6});
}
function guide(f){
 if(!route||!navActive||arrived)return;
 var p=Core.project(route.coords,route.cum,{lat:f.lat,lon:f.lon},route.seg,400);if(!p)return;
 var kmh=(f.speedMps||0)*3.6;
 if(p.off>50&&!(f.accuracyM>50)){
  offCount++;
  // Fora da rota: fala "Recalculando" uma vez por saida; se continuar fora (rua sem mapa, estacionamento), recalcula em silencio com espera crescente ate 60 s.
  if(offCount>=3&&!requesting&&Date.now()-lastRecalc>=recalcDelay){
   if(!offEpisode&&Date.now()-recalcSaidAt>=30000){recalcSaidAt=Date.now();send('nav.say','recalc');} // motorista que ignora varias curvas nao ouve a mesma frase a cada esquina
   offEpisode=true;lastRecalc=Date.now();recalcDelay=Math.min(60000,recalcDelay*2);offCount=0;requestRoute(true);
  }
  return;
 }
 if(offEpisode){offEpisode=false;recalcDelay=10000;}
 offCount=0;route.seg=p.seg;route.s=p.s;
 var remaining=Math.max(0,route.total-p.s);
 while(nextMan<route.man.length-1&&p.s>route.man[nextMan].at+15)nextMan++;
 var m=route.man[nextMan],d=Math.max(0,m.at-p.s);
 if(remaining<30){
  arrived=true;send('nav.say','arrive');
  setIcon($('nav-arrow'),'arrive');hideHud();$('nav-dist').textContent='Chegou';$('nav-street').textContent=dest?dest.name:'';
  renderFoot(0,f);arrivalTimer=setTimeout(function(){stopNav();setStatus('Você chegou ao destino.');},8000);
  return;
 }
 var dc=Core.nextSpeech(m.said,d,kmh,m.code);
 if(dc)sayManeuver(dc,m.code);
 var round=m.code.indexOf('roundabout_')===0;
 setIcon($('nav-arrow'),m.code);
 $('nav-dist').textContent=d<=30?'Agora':Core.fmtDist(d);
 $('nav-street').textContent=m.name||(round?'Rotatória · saída '+m.code.slice(-1):(MAN_TEXT[m.code]||''));
 renderFoot(remaining,f);
 var nx=route.man[nextMan+1],nel=$('nav-next');
 if(nx&&nx.at-p.s<1500){
  if(nextFor!==nextMan){nextFor=nextMan;nel.textContent='';nel.appendChild(icon(nx.code));nel.appendChild(document.createTextNode(nx.code==='arrive'?'Depois: chegada':'Depois: '+manText(nx.code)+' · '+Core.fmtDist(nx.at-m.at)));}
  nel.hidden=false;
 }else{nel.hidden=true;nextFor=-1;}
 var lel=$('nav-lanes'),ln=m.lanes;
 if(ln&&ln.length>=2&&d<=800){
  if(lanesFor!==m){lanesFor=m;lel.textContent='';ln.forEach(function(l){var div=document.createElement('div');div.className='lane'+(l.valid?' valid':'');div.appendChild(icon(l.ind[0]));lel.appendChild(div);});}
  lel.hidden=false;
 }else{lel.hidden=true;lanesFor=null;}
 var bar=document.querySelector('#nav-progress i');if(bar)bar.style.width=Math.min(100,Math.max(0,p.s/route.total*100))+'%';
 updateDone(p);
}
function renderFoot(remaining,f){
 var sec=route&&route.total>0?route.duration*remaining/route.total:0,eta=new Date(Date.now()+sec*1000);
 $('nav-eta').textContent=pad2(eta.getHours())+':'+pad2(eta.getMinutes());
 $('nav-rem').textContent=Core.fmtDist(remaining);$('nav-time').textContent=remaining<=0?'0 min':Core.fmtDur(sec);
 $('nav-speed').textContent=String(Math.round((f.speedMps||0)*3.6));
}
function onFix(f){
 if(!f||!isFinite(f.lat)||!isFinite(f.lon))return;
 if(!isFinite(f.speedMps))f.speedMps=0;
 lastFix=f;fixAt=Date.now();gpsReason='';
 if(!result.hidden)updateStart();
 if(!navActive&&!panel.hidden)fillFrom();
 var good=f.quality==='OK'||f.quality==='FRACO';
 if(good)setLock(f.speedMps>10/3.6);
 renderNearby(false);
 if(!navActive)return;
 $('nav-gps').hidden=!(f.quality==='SEM_FIX'||f.quality==='VELHO');
 if(!good)return;
 hideMsg('wait');hideMsg('gps');
 updateCar(f);follow(f,false);
 if(!route){if(!requesting&&!routeFailed&&dest)requestRoute(false);return;}
 guide(f);
}
function unavailable(reason){
 gpsReason=String(reason||'indisponível').slice(0,80);
 if(navActive){$('nav-gps').hidden=false;if(!route)showMsg('GPS indisponível: '+gpsReason,false,'gps');}
 else setStatus('GPS indisponível: '+gpsReason);
}
function showResults(list){
 var box=$('nav-results');box.textContent='';renderNearby(false);
 list.slice(0,6).forEach(function(r,idx){
  var b=document.createElement('button'),i=String(r.name).indexOf(','),n=document.createElement('i'),t=document.createElement('strong'),s=document.createElement('span');
  b.type='button';b.className='nav-result';n.textContent=String(idx+1);t.textContent=i>0?r.name.slice(0,i):r.name;s.textContent=i>0?r.name.slice(i+1).trim():'';b.appendChild(n);b.appendChild(t);b.appendChild(s);
  if(usableFix()){var e=document.createElement('em');e.textContent=Core.fmtDist(Core.haversine(lastFix,{lat:r.lat,lon:r.lon}));e.title='Distância em linha reta';b.appendChild(e);}
  b.addEventListener('click',function(){startNav(r);});box.appendChild(b);
 });
}
function uniqueName(text){var n=norm(text),f=cities.filter(function(c){return norm(c.name)===n;});return f.length===1?f[0]:null;}
async function searchDestination(text){
 text=String(text||'').trim();if(!text){setStatus('Digite o destino.');return;}
 var id=++searchId;$('nav-results').textContent='';renderNearby(false);
 if(searchCtl)searchCtl.abort();
 var city=resolve(text)||uniqueName(text);
 if(city){startNav({name:label(city),lat:city.lat,lon:city.lon});return;}
 setStatus('Procurando destino…');
 searchCtl=new AbortController();var ctl=searchCtl,timeout=setTimeout(function(){ctl.abort();},15000);
 try{
  var url='map-api/geocode?q='+encodeURIComponent(text);
  if(lastFix)url+='&lat='+lastFix.lat+'&lon='+lastFix.lon;
  var response=await fetch(url,{signal:ctl.signal});if(!response.ok)throw new Error('network');
  var data=await response.json();if(id!==searchId)return;
  var list=(Array.isArray(data)?data:[]).filter(function(r){return r&&typeof r.name==='string'&&isFinite(r.lat)&&isFinite(r.lon);}).map(function(r){return {name:r.name,lat:Number(r.lat),lon:Number(r.lon)};});
  if(!list.length){setStatus('Nenhum local encontrado. Tente outro nome.');return;}
  if(list.length===1){startNav(list[0]);return;}
  setStatus('Toque no destino:');showResults(list);
 }catch(e){if(id===searchId)setStatus('Não foi possível buscar. Confira a Internet e tente novamente.');}
 finally{clearTimeout(timeout);}
}
function navigateTo(text){
 open(false);if(navActive)stopNav();
 text=String(text||'').trim();$('nav-dest').value=text;
 if(!text){setStatus('Digite o destino.');return;}
 return searchDestination(text);
}

/* ===== Perto de voce: POIs reais dos tiles vetoriais carregados (so no 3D; o 2D raster nao tem POI) ===== */
var NB={at:null,t:0,list:[],sig:'',box:$('ck-nearby')};
function nbFresh(){
 if(!lastFix||(lastFix.quality!=='OK'&&lastFix.quality!=='FRACO'))return false;
 return Date.now()-fixAt<(navActive?15000:120000); // no planejador o GPS pode estar desligado: ate 2 min de idade, nunca uma posicao antiga
}
function nbMax(){
 if(!m3||panel.hidden||!nbFresh())return 0;
 if(navActive)return (arrived||(panel.clientHeight||600)<=560)?0:3;
 return (result.hidden&&!$('nav-results').childElementCount&&$('route-form').hidden)?4:0;
}
function placeNearby(){
 var want=navActive?$('nav-top'):$('nav-results').parentNode,box=NB.box;
 if(box.parentNode===want)return;
 if(navActive)want.appendChild(box);else want.insertBefore(box,$('nav-results').nextSibling);
}
function renderNearby(force){
 placeNearby();
 var box=NB.box,max=nbMax();
 if(!max){box.hidden=true;return;}
 var now=Date.now(),moved=NB.at?Core.haversine(NB.at,lastFix):Infinity;
 if(force||!NB.at||moved>=300||now-NB.t>=15000||(!NB.list.length&&now-NB.t>=1500)){ // a cada ~15 s ou 300 m, nao a cada fix
  var res=m3.nearbyPlaces(lastFix.lat,lastFix.lon,3000,4);
  if(res.length||!NB.list.length||moved>=300||now-NB.t>=120000)NB.list=res; // tiles ainda carregando: mantem a lista anterior em vez de piscar
  NB.at={lat:lastFix.lat,lon:lastFix.lon};NB.t=now;
 }
 var items=NB.list.slice(0,max);
 if(!items.length){box.hidden=true;return;}
 var sig=items.map(function(it){return it.name+'|'+Core.fmtDist(it.dist);}).join(';');
 if(sig!==NB.sig){
  NB.sig=sig;var list=$('ck-nearby-list');list.textContent='';
  items.forEach(function(it,idx){
   var b=document.createElement('button'),n=document.createElement('i'),t=document.createElement('strong'),sp=document.createElement('span'),e=document.createElement('em');
   b.type='button';b.className='nav-result';n.textContent=String(idx+1);t.textContent=it.name;sp.textContent=it.label;e.textContent=Core.fmtDist(it.dist);e.title='Distância em linha reta';
   b.appendChild(n);b.appendChild(t);b.appendChild(sp);b.appendChild(e);
   b.addEventListener('click',function(){startNav({name:it.name,lat:it.lat,lon:it.lon});});list.appendChild(b);
  });
 }
 box.hidden=false;
}

from.addEventListener('input',function(){fromTouched=true;});
$('ck-view').addEventListener('click',function(){switchEngine(m3?'2d':'3d');});
$('open-road-map').addEventListener('click',function(){open();});
$('close-road-map').addEventListener('click',close);
$('route-form').addEventListener('submit',function(e){e.preventDefault();calculate();});
$('nav-form').addEventListener('submit',function(e){e.preventDefault();if(locked){setStatus('Pare o carro para digitar.');return;}searchDestination($('nav-dest').value);});
$('nav-stop').addEventListener('click',function(){stopNav();setStatus('Navegação encerrada.');});
// Toque no mapa solta a camera; ela volta sozinha ao carro 12 s depois do ultimo toque (no carro nao da para depender do botao).
var recenterTimer=0;
function recenter(){clearTimeout(recenterTimer);following=true;$('nav-recenter').hidden=true;if(navActive&&lastFix)follow(lastFix,true);}
function userMoved(){if(!navActive)return;following=false;$('nav-recenter').hidden=false;clearTimeout(recenterTimer);recenterTimer=setTimeout(recenter,12000);}
$('nav-recenter').addEventListener('click',recenter);
$('nav-retry').addEventListener('click',function(){routeFailed=false;if(usableFix())requestRoute(false);else showMsg('Aguardando sinal do GPS…',false,'wait');});
Array.prototype.forEach.call(panel.querySelectorAll('.nav-replay-btn'),function(b){b.addEventListener('click',function(){send('nav.replay','');});});
$('swap-route').addEventListener('click',function(){var value=from.value;from.value=to.value;to.value=value;request++;if(abort)abort.abort();clearRoute();status.textContent='Origem e destino invertidos. Toque em Traçar rota.';$('calculate-route').disabled=locked;});
$('fit-route').addEventListener('click',fit);
$('ck-cities-toggle').addEventListener('click',function(){setCities($('route-form').hidden);});
$('route-start').addEventListener('click',function(){
 if(!planState)return;
 var d=planState.destination;clearRoute();startNav({name:label(d),lat:d.lat,lon:d.lon});
});
$('ck-tab-home').addEventListener('click',close);
$('ck-tab-apps').addEventListener('click',function(){close();var a=$('open-apps');if(a)a.click();});
(function(){var n=$('network-short');if(n&&window.MutationObserver)new MutationObserver(syncNet).observe(n,{childList:true,characterData:true,subtree:true});})();
setInterval(function(){if(panel.hidden)return;tickClock();if(!result.hidden)updateStart();renderNearby(false);},3000);
$('route-external').addEventListener('click',function(){var destination=resolve(to.value);if(destination)window.harumiSend('assistant.ask','Trace uma rota para '+label(destination));});
window.harumiNav={fix:onFix,unavailable:unavailable,engine:engine,switchEngine:switchEngine};
window.harumiRoadMap={open:open,close:close,isOpen:function(){return !panel.hidden;},plan:function(a,b){open(false);if(navActive)stopNav();openCities();from.value=a;to.value=b;calculate();},navigateTo:navigateTo,navigatePoint:function(name,lat,lon){if(!isFinite(lat)||!isFinite(lon))return;open(false);startNav({name:String(name||'Destino'),lat:Number(lat),lon:Number(lon)});},destination:function(name){open();openCities();to.value=name;status.textContent='Escolha a origem e toque em Traçar rota.';from.focus();}};
if(new URLSearchParams(location.search).get('mapa')==='1')open();
})();

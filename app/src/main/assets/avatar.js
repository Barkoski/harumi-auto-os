'use strict';
(function(){
var video=document.getElementById('harumi-avatar');
var actor=document.getElementById('harumi-actor');
if(!video||!actor)return;
var badge=document.getElementById('avatar-state');
var clips={greeting:'media/harumi-greeting.mp4?v=038pink',idle:'media/harumi-idle.mp4?v=038pink',listening:'media/harumi-listening.mp4?v=038pink',thinking:'media/harumi-thinking.mp4?v=038pink',speaking:'media/harumi-speaking.mp4?v=038pink'};
var labels={greeting:'Olá!',idle:'Com você',listening:'Ouvindo',thinking:'Pensando',speaking:'Falando'};
var reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
var current='',active=true,obscured=false,demo=false,explicitMotion=false,demoTimer;
function play(){
 video.muted=true;
 if(current!=='speaking'||!active||obscured||document.hidden||(reduced.matches&&!explicitMotion)){video.pause();return;}
 var pending=video.play();if(pending&&pending.catch)pending.catch(function(){});
}
function setState(state){
 if(!Object.prototype.hasOwnProperty.call(clips,state))return;
 badge.textContent=(demo?'Demonstração · ':'')+labels[state];
 if(current===state){play();return;}
 current=state;actor.dataset.animation=state;
 video.loop=state==='speaking';var url=state==='speaking'?clips.speaking:clips.idle;if(video.getAttribute('src')!==url){video.src=url;video.load();}play();
}
function dock(where){
 var target=document.getElementById(where==='assistant'?'assistant-avatar-slot':'home-avatar-slot');
 if(target&&actor.parentElement!==target)target.appendChild(actor);
 obscured=false;play();
}
function stopDemo(){clearTimeout(demoTimer);demo=false;explicitMotion=false;}
function startDemo(){
 stopDemo();demo=true;explicitMotion=true;dock('home');
 var states=['idle','speaking','idle'];var index=0;
 function next(){setState(states[index]);index++;if(index<states.length)demoTimer=setTimeout(next,2100);else demoTimer=setTimeout(function(){demo=false;explicitMotion=false;badge.textContent=labels[current];play();},1800);}
 next();
}
video.addEventListener('loadeddata',play);
video.addEventListener('ended',function(){if(current==='greeting'&&!demo)setState('idle');});
document.addEventListener('visibilitychange',play);
if(reduced.addEventListener)reduced.addEventListener('change',play);else if(reduced.addListener)reduced.addListener(play);
window.harumiAvatar={state:function(state){if(demo)return;setState(state);},dock:dock,obscure:function(value){obscured=value;play();},demo:startDemo};
window.harumiVisibility=function(value){active=Boolean(value);play();};
var button=document.getElementById('avatar-demo');
if(button&&!window.HarumiNative){button.hidden=false;button.addEventListener('click',startDemo);}
setState('idle');
})();

"""Teste do mapa 3D (MapLibre + vetores OpenFreeMap) com Playwright/Edge headless. Requer: python scripts/serve_map_preview.py (porta 8871).
Cobre: motor 3D escolhido, tiles vetoriais carregados, rota Rondonopolis -> Londrina (km), navegacao simulada com trip.nmea
(pitch > 45, carro visivel, HUD, chegada), CSP sem violacoes e reserva automatica para o Leaflet quando o 3D e desligado,
lugares proximos (POIs dos tiles vetoriais), botao 2D/3D com rota/navegacao preservadas e aviso de origem x posicao atual.
A rota da navegacao e interceptada e buscada com steps=true (como em test_nav_hud.py)."""
from pathlib import Path
from urllib.parse import unquote
import json,sys,re,requests
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'docs/evidencias'
EDGE=next(p for p in [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',r'C:\Program Files (x86)\Microsoft Edge\Application\msedge.exe'] if Path(p).exists())
URL='http://127.0.0.1:8871/index.html?mapa=1'
ARGS=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl']
def trip():
 pts=[]
 for line in (root/'app/src/main/assets/debug/trip.nmea').read_text('utf-8').splitlines():
  if not line.startswith('$GPRMC'):continue
  f=line.split(',')
  if f[2]!='A':continue
  la=f[3];lo=f[5];lat=int(la[:2])+float(la[2:])/60;lon=int(lo[:3])+float(lo[3:])/60
  if f[4]=='S':lat=-lat
  if f[6]=='W':lon=-lon
  pts.append({'lat':lat,'lon':lon,'speedMps':float(f[7] or 0)*0.514444,'bearing':float(f[8] or 0),'quality':'OK','accuracyM':5})
 return pts
def osrm_steps(route):
 q=dict(x.split('=',1) for x in route.request.url.split('?',1)[1].split('&'))
 p=unquote(q['points']).split(',')
 url=f'https://router.project-osrm.org/route/v1/driving/{p[0]},{p[1]};{p[2]},{p[3]}?steps=true&overview=full&geometries=geojson&alternatives=false'
 if 'bearing' in q:url+=f"&bearings={q['bearing']},10;0,180"
 r=requests.get(url,timeout=25)
 route.fulfill(status=r.status_code,content_type='application/json',body=r.text)
def new_page(b,w,h,watch):
 page=b.new_page(viewport={'width':w,'height':h});errors=[];csp=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def on_console(m):
  t=m.text
  if 'Content Security Policy' in t or 'Refused to' in t:csp.append(t[:200])
  if m.type=='error' and watch and 'Failed to load resource' not in t:errors.append('console: '+t[:200])
 page.on('console',on_console)
 page.on('response',lambda r:errors.append(f'HTTP {r.status} {r.url}') if watch and r.status>=400 and 'favicon' not in r.url else None)
 return page,errors,csp
def wait_idle(page,timeout=60000):
 page.wait_for_function("()=>{const m=window.HarumiMap3D&&window.HarumiMap3D.current,mm=m&&m.map;return !!mm&&m.isReady()&&mm.loaded()&&mm.areTilesLoaded()}",timeout=timeout)
def planner(b,w,h,shot):
 page,errors,csp=new_page(b,w,h,True);res={'viewport':f'{w}x{h}'}
 page.goto(URL);page.locator('#road-map').wait_for(state='visible')
 page.wait_for_function("()=>window.harumiNav&&window.harumiNav.engine()==='3d'",timeout=20000)
 res['engine']=page.evaluate('window.harumiNav.engine()');assert res['engine']=='3d',res
 wait_idle(page)
 res['renderedFeatures']=page.evaluate("()=>window.HarumiMap3D.current.map.queryRenderedFeatures().length");assert res['renderedFeatures']>0,'sem feicoes vetoriais renderizadas'
 res['vectorSourceLoaded']=page.evaluate("()=>window.HarumiMap3D.current.map.isSourceLoaded('openmaptiles')");assert res['vectorSourceLoaded']
 # a abertura do painel nao pode ter pedido tiles raster do Leaflet
 page.evaluate("window.harumiRoadMap.plan('Rondonópolis, Mato Grosso','Londrina, no Paraná')")
 page.locator('#route-result').wait_for(state='visible',timeout=40000)
 km=int(re.sub(r'\D','',page.locator('#route-distance').inner_text()));res['km']=km;assert 1000<km<2200,km
 res['hours']=page.locator('#route-duration').inner_text()
 assert 'Rondonópolis / MT' in page.locator('#route-endpoints').inner_text() and 'Londrina / PR' in page.locator('#route-endpoints').inner_text()
 page.wait_for_timeout(1500);wait_idle(page)
 assert page.locator('.route-pin').count()==2
 res['routeRendered']=page.evaluate("()=>window.HarumiMap3D.current.map.queryRenderedFeatures({layers:['route-line','route-casing','route-glow']}).length");assert res['routeRendered']>0,'rota nao renderizada'
 res['pitch']=round(page.evaluate("window.HarumiMap3D.current.getState().pitch"),1);assert res['pitch']<=20,res
 res['attribution']=page.locator('.maplibregl-ctrl-attrib').inner_text();assert 'OpenStreetMap' in res['attribution'] and 'OpenFreeMap' in res['attribution'],res['attribution']
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path=str(out/shot))
 assert not csp,csp;assert not errors,errors
 page.close();return res
def nav(b,w,h,shot):
 pts=trip();page,errors,csp=new_page(b,w,h,True)
 page.route('**/map-api/route*',osrm_steps)
 page.goto(URL);page.locator('#road-map').wait_for(state='visible')
 page.wait_for_function("()=>window.harumiNav&&window.harumiNav.engine()==='3d'",timeout=20000)
 page.evaluate("window.__sent=[];window.harumiSend=function(a,m){window.__sent.push([a,m]);}")
 page.evaluate("window.harumiRoadMap.navigatePoint('Destino de teste',-23.3040,-51.1561)")
 res={'viewport':f'{w}x{h}','engine':'3d'};n=len(pts);target=int(n*0.4)
 for i,pt in enumerate(pts):
  page.evaluate("(p)=>window.harumiNav.fix(Object.assign({timeMs:Date.now()},p))",pt)
  page.wait_for_timeout(150)
  if i==target:
   page.wait_for_timeout(2500)
   wait_idle(page,90000)
   assert page.locator('#nav-arrow svg use').count()==1,'seta sem svg use'
   assert page.locator('#nav-dist').inner_text().strip() not in ('','—'),'dist vazio'
   wd=page.evaluate("parseFloat(document.querySelector('#nav-progress i').style.width)||0");assert wd>0,'progresso 0'
   assert page.locator('.m3-car').is_visible(),'carro invisivel'
   st=page.evaluate("window.HarumiMap3D.current.getState()")
   geo=page.evaluate("""()=>{const c=document.querySelector('.m3-car').getBoundingClientRect(),w=document.getElementById('road-map').getBoundingClientRect();return {carY:(c.top+c.height/2-w.top)/w.height,carX:(c.left+c.width/2-w.left)/w.width,builtFeatures:window.HarumiMap3D.current.map.queryRenderedFeatures({layers:['building-3d']}).length,routeFeatures:window.HarumiMap3D.current.map.querySourceFeatures('route').length,credit:document.getElementById('nav-credit').innerText}}""")
   assert st['pitch']>45,st
   small=page.evaluate("""()=>[...document.querySelectorAll('#road-map button')].filter(b=>b.offsetParent!==null&&!b.closest('[hidden]')).map(b=>{const r=b.getBoundingClientRect();return {id:b.id||b.className||b.textContent.trim().slice(0,12),w:Math.round(r.width),h:Math.round(r.height)}}).filter(x=>x.w<56||x.h<56)""")
   assert not small,small  # alvos tateis em navegacao >= 56 px
   assert 0.55<geo['carY']<0.9,geo   # carro no terco inferior
   assert geo['routeFeatures']>0,geo
   assert 'OpenFreeMap' in geo['credit'] and 'OpenStreetMap' in geo['credit'],geo
   res.update(progress_pct=round(wd,1),pitch=round(st['pitch'],1),zoom=round(st['zoom'],2),bearing=round(st['bearing'],1),**geo)
   page.screenshot(path=str(out/shot))
 page.wait_for_timeout(800)
 sent=page.evaluate('window.__sent');dist=page.locator('#nav-dist').inner_text()
 assert dist=='Chegou' or ['nav.say','arrive'] in sent,(dist,sent[-5:])
 res['arrival']=dist;res['says']=len(sent)
 assert not csp,csp;assert not errors,errors
 page.close();return res
def fallback(b):
 """3D desligado por localStorage -> Leaflet; e falha simulada do 3D (sessionStorage) tambem cai para o Leaflet."""
 res={}
 for name,script in [('ls_off',"localStorage.setItem('harumi.map3d','0')"),('session_failed',"sessionStorage.setItem('harumi.map3d.failed','1')")]:
  page,errors,csp=new_page(b,1024,600,False);page.add_init_script(script)
  page.goto(URL);page.locator('#road-map').wait_for(state='visible');page.wait_for_selector('.leaflet-container')
  res[name]=page.evaluate('window.harumiNav.engine()');assert res[name]=='2d',res
  page.wait_for_selector('img.leaflet-tile-loaded',timeout=30000);assert not errors,errors;page.close()
 # falha em tempo de execucao: o adaptador chama onFail e o Leaflet assume com a rota planejada preservada
 page,errors,csp=new_page(b,1024,600,False)
 page.goto(URL);page.wait_for_function("()=>window.harumiNav&&window.harumiNav.engine()==='3d'",timeout=20000)
 wait_idle(page)
 page.evaluate("window.harumiRoadMap.plan('Londrina, no Paraná','Cambé, no Paraná')")
 page.locator('#route-result').wait_for(state='visible',timeout=40000)
 page.evaluate("window.HarumiMap3D.current.map.getCanvas().dispatchEvent(new Event('webglcontextlost'))")
 page.wait_for_function("()=>window.harumiNav.engine()==='2d'",timeout=10000)
 page.wait_for_selector('.leaflet-overlay-pane path.leaflet-interactive',timeout=10000)
 res['runtime_fail']='2d com rota preservada';assert page.evaluate("sessionStorage.getItem('harumi.map3d.failed')")=='1'
 assert page.locator('.route-pin').count()==2
 page.close();return res
LONDRINA={'lat':-23.3105,'lon':-51.1630}
BRASILIA={'lat':-15.794,'lon':-47.882}
RONDONOPOLIS={'lat':-16.47083,'lon':-54.63556}
FIXJS="(p)=>window.harumiNav.fix(Object.assign({speedMps:0,bearing:-1,quality:'OK',accuracyM:5,timeMs:Date.now()},p))"
def fixp(pt):return FIXJS
def open_3d(b,w=1024,h=600):
 page,errors,csp=new_page(b,w,h,True)
 page.goto(URL);page.locator('#road-map').wait_for(state='visible')
 page.wait_for_function("()=>window.harumiNav&&window.harumiNav.engine()==='3d'",timeout=20000)
 wait_idle(page);return page,errors,csp
def nearby(b):
 """Lugares proximos: POIs reais dos tiles vetoriais em Londrina; cartao no planejador e na navegacao; tocar troca o destino."""
 page,errors,csp=open_3d(b);res={}
 page.route('**/map-api/route*',osrm_steps)
 assert page.locator('#ck-nearby').is_hidden(),'cartao nao deve aparecer sem fix'
 page.evaluate(fixp(LONDRINA),LONDRINA)
 page.evaluate("window.harumiRoadMap.open(false)")  # reabre o planejador com fix: enquadra a posicao (zoom com poi)
 page.wait_for_function("()=>{const m=window.HarumiMap3D.current;return m.getState().zoom>=13.5}",timeout=15000)
 page.wait_for_function("()=>window.HarumiMap3D.current.nearbyPlaces(-23.3105,-51.1630,3000,6).length>=3",timeout=40000)  # depende dos tiles z14 chegarem pelo gateway
 wait_idle(page)
 items=page.evaluate("()=>window.HarumiMap3D.current.nearbyPlaces(-23.3105,-51.1630,3000,6)")
 assert len(items)>=3,items
 assert all(i['name'] and i['label'] and 0<=i['dist']<=3000 for i in items),items
 assert [i['dist'] for i in items]==sorted(i['dist'] for i in items),'fora de ordem'
 assert len({i['name'].lower()+i['label'] for i in items})==len(items),'nomes repetidos'
 res['items']=[f"{i['name']} ({i['label']}, {round(i['dist'])} m)" for i in items]
 page.evaluate(fixp(LONDRINA),LONDRINA)  # fix fresco para o cartao
 page.locator('#ck-nearby').wait_for(state='visible',timeout=10000)
 n=page.locator('#ck-nearby .nav-result').count();assert 1<=n<=4,n
 assert page.locator('#ck-nearby .nav-result em').first.inner_text().strip()!='' and page.locator('#ck-nearby .nav-result strong').first.inner_text().strip()!=''
 assert page.locator('#ck-nearby .nav-result').first.bounding_box()['height']>=56
 # buscas e previa escondem o cartao
 page.evaluate("window.harumiRoadMap.plan('Londrina, no Paraná','Cambé, no Paraná')")
 page.locator('#route-result').wait_for(state='visible',timeout=40000)
 assert page.locator('#ck-nearby').is_hidden(),'cartao deve sumir com a previa'
 page.evaluate("window.harumiRoadMap.open(false)");page.locator('#route-result').wait_for(state='visible')
 res['plan_items']=n
 # volta ao estado limpo do planejador para a captura
 page2,errors2,csp2=open_3d(b)
 page2.evaluate(fixp(LONDRINA),LONDRINA);page2.evaluate("window.harumiRoadMap.open(false)")
 page2.wait_for_function("()=>window.HarumiMap3D.current.nearbyPlaces(-23.3105,-51.1630,3000,6).length>=3",timeout=40000);wait_idle(page2)
 page2.evaluate(fixp(LONDRINA),LONDRINA);page2.locator('#ck-nearby').wait_for(state='visible',timeout=10000);page2.wait_for_timeout(800)
 page2.screenshot(path=str(out/'cockpit-nearby-plan-1024x600.png'))
 # tocar num item inicia a navegacao ate ele
 first=page2.locator('#ck-nearby .nav-result strong').last.inner_text()  # o mais longe: o primeiro pode estar a poucos metros (chegada imediata)
 page2.route('**/map-api/route*',osrm_steps)
 page2.locator('#ck-nearby .nav-result').last.click()
 page2.wait_for_function("()=>document.getElementById('road-map').classList.contains('nav-on')",timeout=5000)
 assert page2.evaluate("(n)=>[...document.querySelectorAll('.route-pin')].map(e=>e.title).includes(n)",first),first  # o pino B e o item tocado
 res['tap_starts_nav']=first
 for _ in range(3):
  page2.evaluate(fixp(LONDRINA),LONDRINA);page2.wait_for_timeout(400)
 page2.wait_for_timeout(3000);wait_idle(page2,90000)
 page2.evaluate(fixp(LONDRINA),LONDRINA)
 page2.locator('#ck-nearby').wait_for(state='visible',timeout=10000)
 assert page2.evaluate("document.getElementById('ck-nearby').parentNode.id")=='nav-top','cartao deve ficar no #nav-top'
 n2=page2.locator('#ck-nearby .nav-result').count();assert 1<=n2<=3,n2
 page2.wait_for_timeout(600)
 page2.screenshot(path=str(out/'cockpit-nearby-nav-1024x600.png'))
 # trocar destino na navegacao
 if n2>=2:
  second=page2.locator('#ck-nearby .nav-result strong').nth(1).inner_text()
  page2.locator('#ck-nearby .nav-result').nth(1).click();page2.wait_for_timeout(300)
  assert page2.evaluate("(n)=>[...document.querySelectorAll('.route-pin')].map(e=>e.title).includes(n)",second),second  # o pino B passou para o novo destino
  res['nav_tap_changes_dest']=second
 res['nav_items']=n2
 # altura <= 560 em navegacao: cartao escondido
 page2.set_viewport_size({'width':1024,'height':540});page2.wait_for_timeout(300);page2.evaluate(fixp(LONDRINA),LONDRINA);page2.wait_for_timeout(300)
 assert page2.locator('#ck-nearby').is_hidden(),'cartao deve esconder com altura <= 560 em navegacao'
 assert not csp2,csp2
 page2.close();page.close()
 return res
def toggle(b):
 """Botao 2D/3D: troca o motor ao vivo e volta, preservando rota planejada e navegacao."""
 pts=trip();page,errors,csp=open_3d(b);res={}
 assert page.locator('#ck-view').is_visible() and page.locator('#ck-view').inner_text().strip()=='2D'
 assert page.locator('#ck-view').get_attribute('aria-label')=='Mudar para o mapa 2D'
 bb=page.locator('#ck-view').bounding_box();assert bb['width']>=56 and bb['height']>=56,bb
 zb=page.locator('.m3-zoom').bounding_box();assert bb['y']+bb['height']<=zb['y'],(bb,zb)  # acima do zoom
 page.evaluate("window.harumiRoadMap.plan('Londrina, no Paraná','Cambé, no Paraná')")
 page.locator('#route-result').wait_for(state='visible',timeout=40000)
 page.locator('#ck-view').click()
 page.wait_for_function("()=>window.harumiNav.engine()==='2d'",timeout=10000);page.wait_for_selector('.leaflet-overlay-pane path.leaflet-interactive',timeout=10000)
 assert page.locator('#ck-view').inner_text().strip()=='3D' and page.locator('#ck-engine').inner_text()=='2D'
 assert page.locator('.route-pin').count()==2 and page.locator('#route-result').is_visible()
 assert page.evaluate("localStorage.getItem('harumi.map3d')")=='0'
 page.wait_for_selector('img.leaflet-tile-loaded',timeout=30000);page.wait_for_timeout(500)
 page.screenshot(path=str(out/'cockpit-2d-toggle-1024x600.png'))
 page.locator('#ck-view').click()
 page.wait_for_function("()=>window.harumiNav.engine()==='3d'",timeout=10000);wait_idle(page);page.wait_for_timeout(1200);wait_idle(page)
 assert page.locator('#ck-view').inner_text().strip()=='2D' and page.locator('#ck-engine').inner_text()=='3D'
 assert page.locator('.route-pin').count()==2 and page.locator('.leaflet-container').count()==0
 assert page.evaluate("()=>window.HarumiMap3D.current.map.queryRenderedFeatures({layers:['route-line']}).length")>0,'rota planejada perdida na volta ao 3D'
 assert page.evaluate("localStorage.getItem('harumi.map3d')")=='1'
 res['plan']='rota preservada 3D->2D->3D'
 # navegacao em curso
 page.route('**/map-api/route*',osrm_steps)
 page.evaluate("window.harumiRoadMap.navigatePoint('Destino de teste',-23.3040,-51.1561)")
 for pt in pts[:6]:
  page.evaluate("(p)=>window.harumiNav.fix(Object.assign({timeMs:Date.now()},p))",pt);page.wait_for_timeout(200)
 page.wait_for_function("()=>{const t=document.querySelector('#nav-dist').innerText.trim();return t!==''&&t!=='—'}",timeout=40000)
 page.locator('#ck-view').click();page.wait_for_function("()=>window.harumiNav.engine()==='2d'",timeout=10000)
 for pt in pts[6:9]:
  page.evaluate("(p)=>window.harumiNav.fix(Object.assign({timeMs:Date.now()},p))",pt);page.wait_for_timeout(200)
 dbg=(page.locator('#road-map.nav-on').count(),page.locator('.nav-car').count(),page.locator('.leaflet-overlay-pane path').count())
 assert dbg[0]==1 and dbg[1]==1 and dbg[2]>=2,('navegacao perdida no 2D',dbg)
 assert page.locator('#nav-dist').inner_text().strip() not in ('','—')
 page.locator('#ck-view').click();page.wait_for_function("()=>window.harumiNav.engine()==='3d'",timeout=10000)
 for pt in pts[9:12]:
  page.evaluate("(p)=>window.harumiNav.fix(Object.assign({timeMs:Date.now()},p))",pt);page.wait_for_timeout(300)
 wait_idle(page,90000)
 assert page.locator('#road-map.nav-on').count()==1 and page.locator('.m3-car').is_visible()
 assert page.evaluate("window.HarumiMap3D.current.getState().pitch")>45
 assert page.evaluate("()=>window.HarumiMap3D.current.map.querySourceFeatures('route').length")>0
 assert page.locator('#nav-dist').inner_text().strip() not in ('','—')
 res['nav']='navegacao preservada 3D->2D->3D (pitch>45, carro e rota)'
 assert not csp,csp;assert not errors,errors
 page.close();return res
def origem(b):
 """Origem x posicao atual: aviso e rotulo do botao conforme a distancia do fix a cidade de origem; origem preenchida pelo fix."""
 res={}
 page,errors,csp=open_3d(b)
 assert page.locator('#route-from').input_value()=='' and page.locator('#route-from').get_attribute('placeholder')=='Sua cidade'
 page.evaluate(fixp(BRASILIA),BRASILIA);page.evaluate("window.harumiRoadMap.open(false)")
 assert page.locator('#route-from').input_value()=='Brasília / DF',page.locator('#route-from').input_value()
 page.evaluate("window.harumiRoadMap.plan('Rondonópolis / MT','Londrina / PR')")
 page.locator('#route-result').wait_for(state='visible',timeout=40000)
 page.evaluate(fixp(BRASILIA),BRASILIA)  # fix fresco (a rota demora)
 page.wait_for_function("()=>document.getElementById('route-start').innerText.indexOf('daqui')>=0",timeout=5000)
 note=page.locator('#route-origin-note').inner_text();btn=page.locator('#route-start').inner_text()
 assert 'posição atual' in note and 'Brasília' in note and 'Rondonópolis / MT' in note,note
 assert btn=='Navegar daqui até Londrina / PR',btn
 assert page.locator('#route-start').bounding_box()['height']>=56
 page.wait_for_timeout(1500);wait_idle(page);page.screenshot(path=str(out/'cockpit-origem-aviso-1024x600.png'))
 res['aviso_longe']={'note':note,'button':btn}
 page.evaluate(fixp(RONDONOPOLIS),RONDONOPOLIS)
 page.wait_for_function("()=>document.getElementById('route-start').innerText==='Iniciar navegação'",timeout=5000)
 assert page.locator('#route-origin-note').is_hidden()
 res['perto_da_origem']='Iniciar navegação, sem aviso'
 page.wait_for_function("()=>document.getElementById('route-start').innerText.indexOf('Navegar até')===0",timeout=12000)  # fix envelhece (>5 s): volta ao aviso de espera do GPS
 assert 'quando o GPS responder' in page.locator('#route-origin-note').inner_text()
 res['sem_fix']={'note':page.locator('#route-origin-note').inner_text(),'button':page.locator('#route-start').inner_text()}
 assert not csp,csp;assert not errors,errors
 page.close();return res
if __name__=='__main__':
 results={}
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=EDGE,headless=True,args=ARGS)
  results['planner']=planner(b,1024,600,'cockpit-plan3d-1024x600.png')
  results['nav1024']=nav(b,1024,600,'cockpit-nav-1024x600.png')
  results['nav800']=nav(b,800,480,'cockpit-nav-800x480.png')
  results['nav390']=nav(b,390,844,'cockpit-nav-390x844.png')
  results['fallback']=fallback(b)
  results['nearby']=nearby(b)
  results['toggle']=toggle(b)
  results['origem']=origem(b)
  b.close()
 (out/'map3d-tests.json').write_text(json.dumps(results,indent=1,ensure_ascii=False),'utf-8')
 print(json.dumps(results,ensure_ascii=False,indent=1))

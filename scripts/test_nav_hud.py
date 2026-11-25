"""Teste de navegacao (HUD + camera) com Playwright/Edge. Requer: python scripts/serve_map_preview.py (porta 8871).
O servidor local pede OSRM com steps=false; aqui a rota e interceptada e buscada com steps=true (sem alterar o servidor)."""
from pathlib import Path
import re,json,sys,requests
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'docs/evidencias'
EDGE=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
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
def osrm(route):
 q=dict(x.split('=',1) for x in route.request.url.split('?',1)[1].split('&'))
 from urllib.parse import unquote
 p=unquote(q['points']).split(',')
 url=f'https://router.project-osrm.org/route/v1/driving/{p[0]},{p[1]};{p[2]},{p[3]}?steps=true&overview=full&geometries=geojson&alternatives=false'
 if 'bearing' in q:url+=f"&bearings={q['bearing']},10;0,180"
 r=requests.get(url,timeout=25)
 route.fulfill(status=r.status_code,content_type='application/json',body=r.text)
def run(b,w,h,shot):
 pts=trip();page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script("localStorage.setItem('harumi.map3d','0')") # forca o 2D (Leaflet): o teste mede .nav-car e a rotacao do container
 page.route('**/map-api/route*',osrm)
 page.goto('http://127.0.0.1:8871/index.html?mapa=1');page.locator('#road-map').wait_for(state='visible')
 page.evaluate("window.__sent=[];window.harumiSend=function(a,m){window.__sent.push([a,m]);}")
 page.evaluate("window.harumiRoadMap.navigatePoint('Destino de teste',-23.3040,-51.1561)")
 res={'viewport':f'{w}x{h}'};n=len(pts);target=int(n*0.4)
 for i,pt in enumerate(pts):
  page.evaluate("(p)=>window.harumiNav.fix(Object.assign({timeMs:Date.now()},p))",pt)
  page.wait_for_timeout(150)
  if i==target:
   page.wait_for_timeout(3000)
   assert page.locator('#nav-arrow svg use').count()==1,'seta sem svg use'
   assert page.locator('#nav-dist').inner_text().strip() not in ('','—'),'dist vazio'
   wd=page.evaluate("parseFloat(document.querySelector('#nav-progress i').style.width)||0");assert wd>0,'progresso 0'
   assert page.locator('.nav-car').is_visible(),'carro invisivel'
   geo=page.evaluate("""()=>{const c=document.querySelector('.nav-car').getBoundingClientRect(),w=document.getElementById('road-map').getBoundingClientRect();return {carY:(c.top+c.height/2-w.top)/w.height,carX:(c.left+c.width/2-w.left)/w.width,transform:document.getElementById('route-canvas').style.transform,next:document.getElementById('nav-next').hidden?null:document.getElementById('nav-next').innerText,lanes:document.querySelectorAll('#nav-lanes .lane').length}}""")
   assert 0.4<geo['carY']<0.85,geo
   res.update(progress_pct=round(wd,1),**geo)
   page.screenshot(path=str(out/shot))
 page.wait_for_timeout(600)
 sent=page.evaluate('window.__sent');dist=page.locator('#nav-dist').inner_text()
 assert dist=='Chegou' or ['nav.say','arrive'] in sent,(dist,sent[-5:])
 res['arrival']=dist;res['says']=len(sent)
 assert not errors,errors
 page.close();return res
if __name__=='__main__':
 results=[]
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=EDGE,headless=True)
  for w,h in [(1024,600),(800,480),(390,844)]:results.append(run(b,w,h,f'cockpit-nav2d-{w}x{h}.png'))
  b.close()
 print(json.dumps(results,ensure_ascii=False,indent=1))

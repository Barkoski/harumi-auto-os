from pathlib import Path
import json,time,re
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'docs/evidencias';results=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for w,h in [(1024,600),(1024,480),(800,480),(390,844)]:
  page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script("localStorage.setItem('harumi.map3d','0')") # este teste valida a reserva Leaflet (2D); o 3D e coberto por test_map3d.py
  page.goto('http://127.0.0.1:8871/index.html?atlas=1');page.locator('#open-road-map').click()
  assert page.locator('#road-map').is_visible()
  assert page.locator('#road-map').evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth}')
  # cartoes de vidro e toggle de cidades
  assert page.locator('#route-form').is_hidden() and page.locator('#ck-cities-toggle').get_attribute('aria-expanded')=='false'
  assert page.locator('#nav-search-status').inner_text().strip()=='' and page.locator('.route-foot').count()==0
  assert page.locator('#ck-clock').inner_text().strip()!='--:--' and page.locator('#ck-engine').inner_text()=='2D'
  page.locator('#ck-cities-toggle').click();assert page.locator('#route-form').is_visible();page.locator('#ck-cities-toggle').click();assert page.locator('#route-form').is_hidden()
  # busca com resultados numerados (geocodificador interceptado) e distancia em linha reta so com fix
  page.route('**/map-api/geocode*',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps([{'name':'Praça Central, Londrina, Paraná','lat':-23.31,'lon':-51.16},{'name':'Praça da Matriz, Cambé, Paraná','lat':-23.27,'lon':-51.28},{'name':'Praça Sete, Rolândia, Paraná','lat':-23.31,'lon':-51.36}])))
  page.locator('#nav-dest').fill('Praça');page.locator('#nav-search').click();page.locator('#nav-results .nav-result').first.wait_for()
  assert page.locator('#nav-results .nav-result').count()==3 and page.locator('#nav-results .nav-result i').first.inner_text()=='1' and page.locator('#nav-results em').count()==0
  page.evaluate("window.harumiNav.fix({lat:-23.30,lon:-51.15,speedMps:0,bearing:0,quality:'OK',accuracyM:5})")
  page.locator('#nav-search').click();page.locator('#nav-results em').first.wait_for()
  assert 'km' in page.locator('#nav-results em').first.inner_text() or ' m' in page.locator('#nav-results em').first.inner_text()
  page.screenshot(path=str(out/f'cockpit-plan-results-{w}x{h}.png'))
  page.evaluate("window.harumiRoadMap.plan('Rondonópolis, Mato Grosso','Londrina, no Paraná')")
  page.locator('#route-result').wait_for(state='visible',timeout=35000)
  assert re.fullmatch(r'\d\d:\d\d',page.locator('#route-arrive').inner_text().strip()),page.locator('#route-arrive').inner_text()
  assert page.locator('#route-start').is_enabled() and page.locator('#route-start').inner_text()=='Navegar daqui até Londrina / PR'  # o fix injetado acima (Londrina) ainda e recente e esta a >25 km da origem (Rondonópolis)
  assert 'posição atual' in page.locator('#route-origin-note').inner_text() and 'Rondonópolis / MT' in page.locator('#route-origin-note').inner_text()
  assert 'Rondonópolis / MT' in page.locator('#route-endpoints').inner_text()
  assert 'Londrina / PR' in page.locator('#route-endpoints').inner_text()
  assert page.locator('.leaflet-overlay-pane path.leaflet-interactive').count()==1
  assert page.locator('.route-pin').count()==2
  time.sleep(1)
  loaded=page.locator('img.leaflet-tile-loaded').count();assert loaded>0,'No real street tiles loaded'
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(out/f'cockpit-plan-{w}x{h}.png'))
  observed=page.locator('#route-distance').inner_text()+' / '+page.locator('#route-duration').inner_text()
  assert page.locator('#route-form').is_hidden() and page.locator('#nav-results .nav-result').count()==0  # previa substitui formulario e lista
  page.locator('#ck-cities-toggle').click()
  page.wait_for_timeout(6000);assert page.locator('#route-start').is_enabled() and page.locator('#route-start').inner_text()=='Navegar até Londrina / PR'  # sem fix recente continua ativo: a navegacao aguarda o GPS e o aviso diz isso
  assert 'quando o GPS responder' in page.locator('#route-origin-note').inner_text()
  page.locator('#swap-route').click();assert page.locator('#route-result').is_hidden();assert page.locator('#route-from').input_value()=='Londrina / PR'
  page.locator('#route-from').fill('Cidade inexistente / MT');page.locator('#calculate-route').click();assert 'Escolha uma cidade' in page.locator('#route-status').inner_text()
  page.locator('#route-from').fill('Rondonópolis / MT');page.locator('#route-to').fill('Londrina / PR')
  page.route('**/map-api/route?*',lambda route:route.fulfill(status=503,body='unavailable'))
  page.locator('#calculate-route').click()
  page.get_by_text('Não foi possível calcular a rota.',exact=False).wait_for()
  assert page.locator('#route-result').is_hidden();assert page.locator('.leaflet-overlay-pane path.leaflet-interactive').count()==0
  page.keyboard.press('Escape');assert page.locator('#road-map').is_hidden()
  assert not errors,errors
  results.append({'viewport':f'{w}x{h}','real_osrm_route':observed,'loaded_street_tiles':loaded,'invalid_and_network_error_clear_route':'PASS'})
  page.close()
 b.close()
(out/'road-map-tests.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),'utf-8');print(json.dumps(results,ensure_ascii=True))

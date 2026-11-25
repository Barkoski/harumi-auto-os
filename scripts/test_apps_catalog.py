from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1];out=root/'docs/evidencias';results=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for w,h in [(1024,600),(1024,480),(800,480),(390,844)]:
  page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8871/index.html');page.locator('#open-apps').click();page.locator('.app-card').first.wait_for()
  assert page.locator('.app-card').count()==3  # segmento "Da Harumi" (sem Android nativo)
  page.locator('#apps-tab-more').click();assert page.locator('.app-card').count()==9
  assert 'Ver na loja' in page.locator('.app-availability').first.inner_text()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert page.locator('#apps-panel').evaluate('(e)=>{const r=e.getBoundingClientRect();return r.bottom<=innerHeight&&r.top>=0}')
  page.screenshot(path=str(out/f'apps-{w}x{h}.png'),full_page=True)
  page.evaluate("window.HarumiNative={dispatch:function(a,m){window.lastCatalog=[a,m]}}")
  page.get_by_role('button',name='Waze').click();assert page.evaluate('window.lastCatalog')==['catalog.open','waze']
  page.evaluate("window.harumiAppsUpdate([{id:'maps',installed:true,status:'Disponível neste Android',label:'Maps'}])")
  page.get_by_role('button',name='Google Maps').click();assert page.evaluate('window.lastCatalog')==['catalog.open','maps']
  assert 'Disponível neste Android' in page.get_by_role('button',name='Google Maps').inner_text()
  page.locator('#apps-oem-tab').click();assert page.locator('.app-card').count()==17
  page.get_by_role('button',name='Rádio AM/FM').click();assert page.evaluate('window.lastCatalog')==['catalog.open','radio']
  page.evaluate("window.harumiAppsUpdate([{id:'radio',installed:true,status:'Disponível neste Android',label:'Rádio'}])")
  page.get_by_role('button',name='Alterar app de Rádio AM/FM').click();assert page.evaluate('window.lastCatalog')==['catalog.assign','radio']
  page.locator('#apps-all').click();assert page.evaluate('window.lastCatalog')[0]=='catalog.all'
  page.locator('#apps-tab-own').click();assert page.locator('.app-card').count()==3
  page.get_by_role('button',name='Navegação própria').click();assert page.locator('#apps-panel').is_hidden() and page.locator('#road-map').is_visible()
  page.keyboard.press('Escape')
  page.locator('#open-apps').click();page.keyboard.press('Escape');assert page.locator('#apps-panel').is_hidden()
  assert not errors,errors
  results.append({'viewport':f'{w}x{h}','own':3,'android_apps':7,'oem_entries':17,'preview_does_not_claim_installation':True,'status_and_actions':'PASS'})
  page.close()
 b.close()
(out/'apps-catalog-tests.json').write_text(json.dumps(results,indent=2),'utf-8');print(results)

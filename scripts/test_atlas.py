from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
out=root/'docs/evidencias'
results=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for w,h in [(1024,600),(1024,480),(800,480),(390,844)]:
  page=b.new_page(viewport={'width':w,'height':h});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8871/index.html')
  assert not page.locator('#brazil-atlas').is_visible()
  page.locator('#open-atlas').click()
  assert page.locator('.atlas-state').count()==27
  states=page.evaluate('window.HARUMI_ATLAS_DATA.states')
  for state in states:
   page.select_option('#atlas-select',state['uf'])
   page.wait_for_function("() => document.getElementById('atlas-photo').complete && document.getElementById('atlas-photo').naturalWidth>0")
   assert page.locator('.atlas-state.selected').count()==1
   assert page.locator('#atlas-capital').inner_text()==state['capital']
   assert page.locator('#atlas-photo-license').text_content()
  page.select_option('#atlas-select','PR')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.wait_for_timeout(200)
  page.screenshot(path=str(out/f'atlas-{w}x{h}.png'),full_page=True)
  page.evaluate("window.HarumiNative={dispatch:function(a,m){window.lastCommand=[a,m]}}")
  page.locator('#atlas-route').click()
  assert page.evaluate('window.lastCommand')==['assistant.ask','Trace uma rota para Curitiba, Paraná, Brasil']
  page.locator('#atlas-native-nav').click()
  assert page.evaluate('window.lastCommand')[0]=='apps.open.nav'
  page.keyboard.press('Escape');assert not page.locator('#brazil-atlas').is_visible()
  page.locator('#talk').click();page.locator('#close-assistant').click()
  assert page.evaluate('window.lastCommand')[0]=='assistant.cancel.quiet'
  assert not errors,errors
  results.append({'viewport':f'{w}x{h}','photos':27,'selection_route_close':'PASS'})
  page.close()
 b.close()
(out/'atlas-tests.json').write_text(json.dumps(results,indent=2))
print(results)



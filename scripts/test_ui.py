from pathlib import Path
import threading, http.server, functools, json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
out=root/'docs/evidencias'
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root/'app/src/main/assets'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for width,height in [(1024,600),(1024,480),(800,480),(390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
  page.wait_for_timeout(200)
  assert not errors,errors
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Horizontal overflow'
  for label in ['Ajustes','Conversar com a Harumi','Diagnóstico','Telefone','Câmeras','Internet','Abrir música']:
   assert page.get_by_role('button',name=label).is_visible()
  page.get_by_role('button',name='Ajustes').click()
  assert page.get_by_role('heading',name='Ajustes').is_visible()
  page.get_by_role('button',name='Escolher mapas').click()
  assert 'Prévia visual' in page.get_by_role('status').inner_text()
  page.get_by_role('button',name='Fechar',exact=True).click()
  assert not page.locator('#settings').is_visible()
  page.evaluate("window.harumiUpdate({NAV:'<img src=x onerror=alert(1)>',MUSIC:'Meu app',CAMERA360:'OEM',device:'Android de teste'})")
  assert page.locator('#NAV img').count()==0
  assert '<img' in page.locator('#NAV').inner_text()
  page.evaluate("window.harumiUpdate({NAV:'Escolher aplicativo',MUSIC:'Escolher aplicativo',CAMERA360:'Escolher app OEM',device:'Prévia visual · sem conexão Android'})")
  page.locator('#message').evaluate('(e)=>e.hidden=true')
  page.screenshot(path=str(out/f'preview-{width}x{height}.png'),full_page=True)
  results.append({'viewport':f'{width}x{height}','status':'PASS','vertical_scroll':page.evaluate('document.documentElement.scrollHeight > innerHeight')})
  page.close()
 browser.close()
server.shutdown()
(out/'ui-test-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))

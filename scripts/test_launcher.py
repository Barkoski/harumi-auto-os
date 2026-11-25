from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1];out=root/'docs/evidencias';results=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for w,h in [(2000,1200),(1280,720),(1024,600),(1024,520),(800,480),(390,844)]:
  page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8871/index.html');page.wait_for_timeout(200)
  # Home em cartoes de vidro (sem icones coloridos de icons/)
  assert page.locator('#home .hu-grid>.ck-card').count()==5
  assert page.locator('#hu-tabs .ck-tab').count()==5
  assert page.locator('#home img').count()==0
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  for sel in ['#configure','#home-road-map','#hu-cities','#open-atlas','#voice-home','#talk','#connections']:assert page.locator(sel).is_visible(),sel
  page.screenshot(path=str(out/f'launcher-{w}x{h}.png'),full_page=True)
  page.locator('#talk').click();page.evaluate("window.harumiDictation('harumi trace uma rota de rondonópolis para londrina');window.harumiUpdate({assistantStatus:'Ouvindo…',assistantBusy:true})")
  assert page.locator('#finish-listening').is_visible();assert page.locator('#dictation-preview').is_visible()
  assert page.locator('#hu-harumi-status').inner_text().startswith('Ouvindo')
  page.evaluate("window.harumiDictation('');window.harumiUpdate({assistantStatus:'Pensando…',assistantBusy:true});window.harumiMessage('Você','O que você pode fazer?');window.harumiPartial('Posso conversar com você');window.harumiPartial('Posso conversar com você e mostrar rotas.');window.harumiMessage('Harumi','Posso conversar com você e mostrar rotas no mapa.')")
  assert page.locator('.streaming-message').count()==0
  assert 'mostrar rotas no mapa.' in page.locator('#conversation p').last.inner_text()
  page.evaluate("window.harumiUpdate({assistantStatus:'Resposta parcial · toque em Continuar',assistantBusy:false})");assert page.locator('#continue-answer').is_visible()
  page.screenshot(path=str(out/f'assistant-0315-{w}x{h}.png'),full_page=True)
  page.keyboard.press('Escape');assert page.locator('#assistant').is_hidden()
  page.locator('#home-road-map').click();assert page.locator('#road-map').is_visible();page.keyboard.press('Escape');assert page.locator('#road-map').is_hidden()
  page.locator('#open-apps').click();page.locator('.app-card').first.wait_for();assert page.locator('.app-card').count()==3
  page.locator('#apps-tab-more').click();assert page.locator('.app-card').count()==9
  page.locator('#apps-tab-installed').click();assert page.locator('#apps-installed-grid').is_visible()
  page.evaluate("window.harumiLauncherUpdate({apps:[{id:'a',name:'App A',icon:'icons/x.png'}]})");assert page.locator('#apps-installed-grid .app-card').count()==1
  page.keyboard.press('Escape');assert page.locator('#apps-panel').is_hidden()
  assert not errors,errors
  results.append({'viewport':f'{w}x{h}','home_streaming_dictation_panels':'PASS'})
  page.close()
 b.close()
(out/'launcher-tests.json').write_text(json.dumps(results,indent=2),'utf-8');print(results)

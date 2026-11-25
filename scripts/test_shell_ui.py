"""Casca da interface (Home, Conversa, Apps, Ajustes, Internet, Atlas, Cockpit) em 4 tamanhos.
Verifica: sem pageerror, sem overflow horizontal, alvos >= 56 px (largura >= 800), aba ativa correta
e Voltar (Escape) fechando tela por tela. Capturas em docs/evidencias/ui-nova/ e resultados.json.
Requer scripts/serve_map_preview.py na porta 8871."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1];out=root/'docs/evidencias/ui-nova';out.mkdir(parents=True,exist_ok=True);results=[];failures=[]
URL='http://127.0.0.1:8871/index.html'
SIZES=[(1024,600),(1024,480),(800,480),(390,844)]
SMALL_JS="""()=>{
 const sel='button,select,textarea,input,summary,[role=tab]';const bad=[];
 const root=document.querySelector('.hu-screen:not([hidden]),#assistant:not([hidden]),#road-map:not([hidden]),#home');
 const scope=[root,document.getElementById('hu-tabs')].filter(Boolean);
 for(const r of scope)for(const e of r.querySelectorAll(sel)){
  if(e.closest('#road-map')||e.closest('[hidden]'))continue;
  const b=e.getBoundingClientRect();if(!b.width&&!b.height)continue;
  const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none')continue;
  if(b.width<56||b.height<56)bad.push((e.id||e.className||e.tagName)+' '+Math.round(b.width)+'x'+Math.round(b.height));
 }
 return bad;}"""
ACTIVE_JS="()=>{const a=[...document.querySelectorAll('#hu-tabs .ck-tab.is-active')];return a.map(x=>x.id||x.dataset.action||x.textContent.trim())}"
def check(cond,msg):
 if not cond:failures.append(msg)
 return cond
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
 for w,h in SIZES:
  page=b.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(URL);page.wait_for_timeout(400)
  def shot(name,expected_tab,small=True,hidden_ok=False):
   page.wait_for_timeout(250);page.evaluate("document.getElementById('message').hidden=true")
   tag=f'{name}-{w}x{h}'
   page.screenshot(path=str(out/f'{tag}.png'))
   ov=page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.body.scrollWidth<=innerWidth')
   bad=page.evaluate(SMALL_JS) if (w>=800 and small) else []
   act=page.evaluate(ACTIVE_JS) if expected_tab else None
   row={'tela':name,'viewport':f'{w}x{h}','sem_overflow_horizontal':ov,'alvos_pequenos':bad,'aba_ativa':act}
   check(ov,f'{tag}: overflow horizontal')
   check(not bad,f'{tag}: alvos < 56px {bad}')
   if expected_tab:check(act==[expected_tab],f'{tag}: aba ativa {act} != {expected_tab}')
   results.append(row)
  # Inicio
  check(page.locator('#home').is_visible(),f'{w}x{h}: home visivel');shot('inicio','hu-tab-home')
  # Apps (e segmentos)
  page.locator('#open-apps').click();page.locator('.app-card').first.wait_for();shot('apps-da-harumi','open-apps')
  page.locator('#apps-oem-tab').click();shot('apps-central','open-apps')
  page.locator('#apps-tab-more').click();shot('apps-mais','open-apps')
  page.locator('#apps-tab-installed').click();shot('apps-instalados','open-apps')
  page.keyboard.press('Escape');check(page.locator('#apps-panel').is_hidden(),f'{w}x{h}: Escape fecha apps');check(page.locator('#home').is_visible(),f'{w}x{h}: volta ao inicio')
  # Conversa
  page.locator('#hu-tab-harumi').click();check(page.locator('#assistant').is_visible(),f'{w}x{h}: conversa abre');
  page.evaluate("window.harumiMessage('Você','Trace uma rota para Londrina');window.harumiMessage('Harumi','Posso traçar a rota no mapa. Para onde você quer ir?')");shot('conversa','hu-tab-harumi')
  page.evaluate("window.harumiDictation('trace uma rota de rondonópolis para londrina');window.harumiUpdate({assistantStatus:'Ouvindo…',assistantBusy:true,animation:'listening'})")
  check(page.evaluate("document.getElementById('assistant').dataset.voice")=='listening',f'{w}x{h}: data-voice espelhado')
  check(page.locator('#hu-harumi-status').inner_text().startswith('Ouvindo'),f'{w}x{h}: status espelhado');shot('conversa-ouvindo','hu-tab-harumi')
  page.evaluate("window.harumiDictation('');window.harumiUpdate({assistantStatus:'Pronta para conversar · IA local',assistantBusy:false,animation:'idle'})")
  page.keyboard.press('Escape');check(page.locator('#assistant').is_hidden(),f'{w}x{h}: Escape fecha conversa')
  # Ajustes
  page.locator('#configure').click();check(page.locator('#settings').is_visible(),f'{w}x{h}: ajustes abre');shot('ajustes','hu-tab-home')
  page.locator('#settings-internet').click();check(page.locator('#connectivity').is_visible(),f'{w}x{h}: internet pelos ajustes');check(page.locator('#settings').is_hidden(),f'{w}x{h}: ajustes fecha ao abrir internet')
  shot('internet','hu-tab-home')
  page.locator('#initial-network-setup summary').click();shot('internet-config','hu-tab-home')
  page.keyboard.press('Escape');check(page.locator('#connectivity').is_hidden(),f'{w}x{h}: Escape fecha internet')
  # Atlas
  page.locator('#open-atlas').click();check(page.locator('#brazil-atlas').is_visible(),f'{w}x{h}: atlas abre');shot('atlas','hu-tab-home')
  page.keyboard.press('Escape');check(page.locator('#brazil-atlas').is_hidden(),f'{w}x{h}: Escape fecha atlas')
  # Cockpit pela aba Navegar e pela Home
  page.locator('#hu-tab-nav').click();page.locator('#road-map').wait_for(state='visible');page.wait_for_timeout(600);shot('cockpit',None,small=False)
  check(page.locator('#ck-tab-nav.is-active').count()==1,f'{w}x{h}: aba Navegar ativa no cockpit')
  page.locator('#ck-tab-home').click();check(page.locator('#road-map').is_hidden(),f'{w}x{h}: cockpit fecha pelo Inicio');check(page.locator('#home').is_visible(),f'{w}x{h}: inicio apos cockpit')
  page.locator('#hu-cities').click();page.locator('#road-map').wait_for(state='visible');check(page.locator('#route-form').is_visible(),f'{w}x{h}: Entre duas cidades abre o formulario')
  page.keyboard.press('Escape')
  if page.locator('#road-map').is_visible():page.locator('#ck-tab-home').click()
  page.locator('#home-road-map').click();page.locator('#road-map').wait_for(state='visible');page.wait_for_timeout(250);check(page.evaluate("document.activeElement&&document.activeElement.id")=='nav-dest',f'{w}x{h}: busca da Home foca #nav-dest')
  page.locator('#ck-tab-home').click()
  # Aba Inicio fecha tudo
  page.locator('#open-apps').click();page.locator('#hu-tab-home').click();check(page.locator('#apps-panel').is_hidden(),f'{w}x{h}: aba Inicio fecha apps')
  check(not errors,f'{w}x{h}: pageerror {errors}')
  page.close()
 b.close()
(out/'resultados.json').write_text(json.dumps({'falhas':failures,'telas':results},indent=2,ensure_ascii=False),'utf-8')
print(json.dumps({'falhas':failures,'total_telas':len(results)},indent=2,ensure_ascii=False))
raise SystemExit(1 if failures else 0)

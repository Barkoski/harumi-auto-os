from pathlib import Path
import subprocess, json, time, urllib.request, re, xml.etree.ElementTree as ET
import websocket
base=Path(__file__).resolve().parents[2]
adb=base/'work/android-toolchain/android-sdk/platform-tools/adb.exe'
out=base/'Harumi Auto OS/docs/evidencias'
def run(*args):return subprocess.check_output([str(adb),'-s','emulator-5554',*args],text=True,encoding='utf-8',errors='replace').strip()
pid=run('shell','pidof','com.harumi.autoos')
run('forward','tcp:9229','localabstract:webview_devtools_remote_'+pid)
pages=json.load(urllib.request.urlopen('http://127.0.0.1:9229/json'))
ws=websocket.create_connection(pages[0]['webSocketDebuggerUrl'],suppress_origin=True,timeout=10)
seq=0
def js(expr):
 global seq
 seq+=1;ws.send(json.dumps({'id':seq,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}))
 while True:
  x=json.loads(ws.recv())
  if x.get('id')==seq:
   if 'error' in x or 'exceptionDetails' in x.get('result',{}):raise RuntimeError(x)
   return x.get('result',{}).get('result',{}).get('value')
def wait_idle(timeout=70):
 start=time.time()
 while time.time()-start<timeout:
  if not js("document.getElementById('send-question').disabled"):return
  time.sleep(.4)
 raise AssertionError('Assistant did not return to idle')
results=[]
js("document.getElementById('talk').click()")
assert not js("document.getElementById('assistant').hidden")
js("document.getElementById('question').value='Olá, Harumi. Como você pode me ajudar?';document.getElementById('send-question').click()")
time.sleep(.3);wait_idle()
conversation=js("document.getElementById('conversation').textContent")
assert 'Você' in conversation and 'Harumi' in conversation
assert 'Não consegui concluir a operação' not in conversation,conversation
results.append({'test':'Chat through actual WebView and native engines','status':'PASS','conversation':conversation})
run('shell','screencap','-p','/sdcard/chat.png');run('pull','/sdcard/chat.png',str(out/'assistant-chat-android.png'))
print('Chat UI passed',flush=True)
js("document.getElementById('question').value='trace uma rota para centro de Londrina';document.getElementById('send-question').click()")
time.sleep(.3);wait_idle()
run('shell','uiautomator','dump','/sdcard/route.xml');tree=ET.fromstring(run('shell','cat','/sdcard/route.xml'))
texts=[n.attrib.get('text','') for n in tree.iter('node')]
assert any('Confirmar destino' in t for t in texts),texts
assert any('centro de Londrina' in t for t in texts),texts
results.append({'test':'Route confirmation from conversation','status':'PASS','destination':'centro de Londrina'})
run('shell','screencap','-p','/sdcard/route.png');run('pull','/sdcard/route.png',str(out/'assistant-route-android.png'))
run('shell','input','keyevent','4')
print('Route confirmation passed',flush=True)
js("HarumiNative.dispatch('assistant.ask','Como está o carro?')")
time.sleep(.3);wait_idle()
assert 'DESCONECTADO' in js("document.getElementById('conversation').textContent")
results.append({'test':'Vehicle status without adapter','status':'PASS','details':'Explicitly disconnected; no fabricated readings'})
js("HarumiNative.dispatch('assistant.ask','Explique em três frases como funciona uma viagem longa.')")
time.sleep(.2);js("HarumiNative.dispatch('assistant.cancel','')")
wait_idle()
results.append({'test':'Cancel active turn','status':'PASS'})
js("document.getElementById('close-assistant').click()")
assert not js('document.documentElement.scrollHeight>innerHeight')
run('shell','input','tap','500','50');time.sleep(.3)
focus=run('shell','dumpsys','activity','activities')
assert re.search(r'mResumedActivity:.*com.android.launcher3',focus)
results.append({'test':'Native recovery after AI use','status':'PASS'})
run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity')
ws.close();run('forward','--remove','tcp:9229')
(out/'assistant-ui-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=True,indent=2))

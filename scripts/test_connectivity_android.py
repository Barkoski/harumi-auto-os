from pathlib import Path
import subprocess,json,time,urllib.request,re
import websocket
base=Path(__file__).resolve().parents[2]
adb=base/'work/android-toolchain/android-sdk/platform-tools/adb.exe'
out=base/'Harumi Auto OS/docs/evidencias'
def run(*args):return subprocess.check_output([str(adb),'-s','emulator-5554',*args],text=True,encoding='utf-8',errors='replace',timeout=120).strip()
assert run('shell','getprop','dev.bootcomplete')=='1'
print(run('install','-r',str(base/'Harumi Auto OS/app/build/outputs/apk/debug/app-debug.apk')),flush=True)
run('shell','svc','wifi','disable');run('shell','svc','data','disable')
run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity')
time.sleep(.6)
pid=run('shell','pidof','com.harumi.autoos');run('forward','tcp:9229','localabstract:webview_devtools_remote_'+pid)
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
def wait_for(expression,predicate,timeout=15):
 start=time.time()
 while time.time()-start<timeout:
  value=js(expression)
  if predicate(value):return value
  time.sleep(.3)
 raise AssertionError((expression,value))
results=[]
assert js("document.getElementById('voice-home').textContent")=='Falar com Harumi'
offline=wait_for("document.getElementById('network-short').textContent",lambda x:'Sem conexão' in x)
results.append({'test':'Offline status from Android','status':'PASS','observed':offline})
js("document.getElementById('connections').click()")
assert not js("document.getElementById('connectivity').hidden")
assert all(js("document.querySelector('[data-action=\""+a+"\"]').textContent") for a in ['connection.wifi','connection.bluetooth','connection.phone'])
run('shell','screencap','-p','/sdcard/connections.png');run('pull','/sdcard/connections.png',str(out/'connections-android.png'))
results.append({'test':'Connection panel and three setup paths','status':'PASS'})
for action in ['connection.wifi','connection.bluetooth','connection.phone']:
 js("HarumiNative.dispatch("+json.dumps(action)+",'')")
 time.sleep(.4)
 focus=run('shell','dumpsys','activity','activities')
 assert re.search(r'mResumedActivity:.*com.android.settings',focus),focus[-3000:]
 results.append({'test':'Settings launch '+action,'status':'PASS'})
 run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity');time.sleep(.3)
js("document.getElementById('close-connectivity').click()")
run('shell','svc','wifi','enable')
observed=wait_for("document.getElementById('network-short').textContent",lambda x:'Wi-Fi' in x,timeout=25)
results.append({'test':'Network callback updates Wi-Fi status','status':'PASS','observed':observed})
run('shell','screencap','-p','/sdcard/home.png');run('pull','/sdcard/home.png',str(out/'home-033-android.png'))
run('shell','pm','grant','com.harumi.autoos','android.permission.RECORD_AUDIO')
js("document.getElementById('voice-home').click()")
status=wait_for("document.getElementById('assistant-status').textContent",lambda x:x.startswith('Ouvindo'),timeout=20)
assert not js("document.getElementById('assistant').hidden")
results.append({'test':'HOME voice button opens assistant and starts offline capture','status':'PASS','observed':status})
js("HarumiNative.dispatch('assistant.cancel','')")
wait_for("document.getElementById('assistant-status').textContent",lambda x:x.startswith('Pronta'))
js("document.getElementById('close-assistant').click()")
assert not js('document.documentElement.scrollHeight>innerHeight')
results.append({'test':'Stop voice and return to HOME without overflow','status':'PASS'})
js("HarumiNative.dispatch('assistant.ask','abra o Wi-Fi')")
start=time.time()
while time.time()-start<30:
 focus=run('shell','dumpsys','activity','activities')
 if re.search(r'mResumedActivity:.*com.android.settings',focus):break
 time.sleep(.3)
else:raise AssertionError('Voice Wi-Fi command did not open settings')
results.append({'test':'Spoken-command route opens Wi-Fi settings after local reply','status':'PASS'})
run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity')
ws.close();run('forward','--remove','tcp:9229')
run('shell','pm','revoke','com.harumi.autoos','android.permission.RECORD_AUDIO')
(out/'connectivity-android-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=True,indent=2),flush=True)

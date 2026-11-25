from pathlib import Path
import subprocess,json,time,urllib.request,re,xml.etree.ElementTree as ET
import websocket
base=Path(__file__).resolve().parents[2]
adb=base/'work/android-toolchain/android-sdk/platform-tools/adb.exe'
out=base/'Harumi Auto OS/docs/evidencias'
results=[]
def run(*args):return subprocess.check_output([str(adb),'-s','emulator-5554',*args],text=True,encoding='utf-8',errors='replace').strip()
def connect():
 pid=run('shell','pidof','com.harumi.autoos')
 run('forward','tcp:9229','localabstract:webview_devtools_remote_'+pid)
 for _ in range(30):
  try:
   pages=json.load(urllib.request.urlopen('http://127.0.0.1:9229/json'))
   if pages:break
  except Exception:pass
  time.sleep(.2)
 ws=websocket.create_connection(pages[0]['webSocketDebuggerUrl'],suppress_origin=True,timeout=10)
 return ws
seq=0
ws=connect()
def cdp(method,params={}):
 global seq
 seq+=1;ws.send(json.dumps({'id':seq,'method':method,'params':params}))
 while True:
  obj=json.loads(ws.recv())
  if obj.get('id')==seq:
   if 'error' in obj:raise RuntimeError(obj)
   return obj.get('result',{})
def js(expr):
 obj=cdp('Runtime.evaluate',{'expression':expr,'returnByValue':True})
 if 'exceptionDetails' in obj:raise RuntimeError(obj)
 return obj.get('result',{}).get('value')
def record(name,details):results.append({'test':name,'status':'PASS','details':details})
assert js("typeof window.HarumiNative.dispatch")=='function'
assert js("document.getElementById('device').textContent").startswith('unknown') or js("document.getElementById('device').textContent")!='Prévia visual · sem conexão Android'
record('Native bridge and initial state',js("document.getElementById('device').textContent"))
assert js('innerWidth')==1024
assert not js('document.documentElement.scrollHeight>innerHeight')
record('1024x600 Android layout',{'webview_width':js('innerWidth'),'webview_height':js('innerHeight'),'scroll':False})
js("document.querySelector('[data-action=\\\"device.read.basic\\\"]').click()")
time.sleep(.3)
xml=run('shell','uiautomator','dump','/sdcard/check.xml');tree=ET.fromstring(run('shell','cat','/sdcard/check.xml'))
texts=[n.attrib.get('text','') for n in tree.iter('node')]
assert any('Diagnóstico do dispositivo' in t for t in texts),texts
record('Device profile dialog','Native profile displayed; MCU remains unknown')
run('shell','input','keyevent','4')
js("document.querySelector('[data-action=\\\"apps.open.nav\\\"]').click()")
time.sleep(.3)
run('shell','uiautomator','dump','/sdcard/check.xml');tree=ET.fromstring(run('shell','cat','/sdcard/check.xml'))
choices=[n for n in tree.iter('node') if 'com.android.settings' in n.attrib.get('text','')]
assert choices,[n.attrib.get('text') for n in tree.iter('node')]
bounds=[int(n) for n in re.findall(r'\d+',choices[0].attrib['bounds'])]
run('shell','input','tap',str((bounds[0]+bounds[2])//2),str((bounds[1]+bounds[3])//2));time.sleep(.3)
assert 'Settings' in js("document.getElementById('NAV').textContent")
record('App assignment','Settings assigned to NAV only as a bench test')
js("document.querySelector('[data-action=\\\"apps.open.nav\\\"]').click()")
time.sleep(.3)
focus=run('shell','dumpsys','activity','activities')
assert re.search(r'mResumedActivity:.*com.android.settings',focus),focus[-2000:]
record('Assigned app launch','Settings opened through stored, visible launcher activity')
run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity');time.sleep(.3)
run('shell','am','force-stop','com.harumi.autoos')
run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity');time.sleep(.5)
ws.close();ws=connect()
assert 'Settings' in js("document.getElementById('NAV').textContent")
record('Assignment persistence','Assignment preserved after force-stop and restart')
js("HarumiNative.dispatch('apps.clear','NAV')");time.sleep(.2)
assert js("document.getElementById('NAV').textContent")=='Escolher aplicativo'
record('Clear assignment','Stored mapping removed and UI refreshed')
js("HarumiNative.dispatch('shell.exec','NAV')");time.sleep(.2)
focus=run('shell','dumpsys','activity','activities');assert re.search(r'mResumedActivity:.*com.harumi.autoos',focus)
record('Unknown command rejection','shell.exec has no action; app remains active')
js("location.href='https://example.invalid/'");time.sleep(.3)
assert js('location.href')=='https://appassets.androidplatform.net/assets/index.html'
record('External top-level navigation','Navigation rejected; trusted local origin preserved')
run('shell','svc','wifi','disable');run('shell','svc','data','disable')
run('shell','am','force-stop','com.harumi.autoos');run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity');time.sleep(.5)
ws.close();ws=connect();assert js("document.querySelector('h1').textContent")=='Olá, Lucas.'
record('Offline launcher screen','Local interface loads with emulator Wi-Fi and data disabled')
run('shell','screencap','-p','/sdcard/harumi-screen.png');run('pull','/sdcard/harumi-screen.png',str(out/'android-api30.png'))
run('shell','input','tap','500','50');time.sleep(.3)
focus=run('shell','dumpsys','activity','activities');assert re.search(r'mResumedActivity:.*com.android.launcher3',focus),focus[-3000:]
record('Native recovery button','Returned to emulator launcher3; central OEM recovery still NOT_RUN')
run('shell','svc','wifi','enable');run('shell','svc','data','enable')
run('shell','am','start','-W','-n','com.harumi.autoos/.MainActivity')
ws.close();run('forward','--remove','tcp:9229')
(out/'android-smoke-results.json').write_text(json.dumps({'android_api':30,'webview':'83.0.4103.120','results':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=True,indent=2))

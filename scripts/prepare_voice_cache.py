from pathlib import Path
import re,json,struct,hashlib,time
import numpy as np,sherpa_onnx
ROOT=Path(__file__).resolve().parents[1];base=ROOT.parent
m=base/'work/voice-natural/sherpa-onnx-supertonic-3-tts-int8-2026-05-11'
out=ROOT/'app/src/main/assets/voice-cache';out.mkdir(exist_ok=True)
cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(duration_predictor=str(m/'duration_predictor.int8.onnx'),text_encoder=str(m/'text_encoder.int8.onnx'),vector_estimator=str(m/'vector_estimator.int8.onnx'),vocoder=str(m/'vocoder.int8.onnx'),tts_json=str(m/'tts.json'),unicode_indexer=str(m/'unicode_indexer.bin'),voice_style=str(m/'voice.bin')),num_threads=2,provider='cpu'))
assert cfg.validate();tts=sherpa_onnx.OfflineTts(cfg)
profile=(ROOT/'app/src/main/java/com/harumi/autoos/voice/VoiceProfile.java').read_text(encoding='utf-8')
greeting=re.search(r'GREETING="([^"]+)"',profile).group(1)
java=ROOT/'app/src/main/java/com/harumi/autoos'
def grab(rel,pattern):
 return re.search(pattern,(java/rel).read_text(encoding='utf-8')).group(1) # texto lido do proprio codigo para nunca divergir
ctl='ai/AssistantController.java'
texts={'wellbeing':'Oi, Lucas! Tudo bem por aqui. E você?','thanks':'Por nada, Lucas! Estou por aqui.','greeting':greeting,
 'wake_reply':grab(ctl,r'WAKE_REPLY="([^"]+)"'),
 'off_topic':grab('ai/DomainScope.java',r'OFF_TOPIC_REPLY\s*=\s*"([^"]+)"'),
 'music_open':grab(ctl,r'MUSIC_OPEN="([^"]+)"'),
 'music_missing':grab(ctl,r'MUSIC_MISSING="([^"]+)"'),
 'diag_disconnected':grab('diagnostics/DiagnosticMonitor.java',r'if\(!s\.connected\(\)\)\s*return "([^"]+)"')}
NAV={'d100':'Em cem metros,','d200':'Em duzentos metros,','d500':'Em quinhentos metros,','d1k':'Em um quilômetro,','now':'Agora,','left':'vire à esquerda.','right':'vire à direita.','slight_left':'mantenha-se levemente à esquerda.','slight_right':'mantenha-se levemente à direita.','sharp_left':'curva fechada à esquerda.','sharp_right':'curva fechada à direita.','straight':'siga em frente.','uturn':'faça o retorno.','keep_left':'mantenha-se à esquerda.','keep_right':'mantenha-se à direita.','arrive':'Você chegou ao destino.','recalc':'Recalculando a rota.','nav_start':'Vamos lá. Calculando o caminho.'}
for i,o in enumerate(['primeira','segunda','terceira','quarta','quinta'],1):NAV['roundabout_%d'%i]='na rotatória, pegue a %s saída.'%o
kb=(java/'ai/CarKnowledge.java').read_text(encoding='utf-8') # respostas conferidas do carro: ids kb_<chave>
for k,v in re.findall(r'K\("(\w+)",\s*"(?:\\.|[^"\\])*",\s*"([^"\\]+)"\)',kb):texts['kb_'+k]=v
for k,v in NAV.items():texts['nav_'+k if not k.startswith('nav_') else k]=v # contrato com NavigationVoice: ids nav_<codigo>
old={}
if (out/'manifest.json').exists():old={c['id']:c for c in json.loads((out/'manifest.json').read_text(encoding='utf-8'))['clips']}
manifest={'engine':'Supertonic 3 INT8 F3','speaker':2,'steps':24,'speed':1.25,'silence_scale':.72,'language':'pt','post_processing':'none','clips':[]}
for key,text in texts.items():
 if key in old and old[key]['text']==text and (out/(key+'.f32')).exists():manifest['clips'].append(old[key]);print(key+' kept',flush=True);continue # clipes aprovados e inalterados nao sao regerados
 gen=sherpa_onnx.GenerationConfig();gen.sid=2;gen.num_steps=24;gen.speed=1.25;gen.silence_scale=.72;gen.extra['lang']='pt'
 start=time.monotonic();audio=tts.generate(text.replace('Harumi','Rarumi'),gen)
 samples=np.asarray(audio.samples,dtype='<f4');assert np.isfinite(samples).all() and np.max(np.abs(samples))>.01
 path=out/(key+'.f32');path.write_bytes(b'HAU1'+struct.pack('<II',audio.sample_rate,len(samples))+samples.tobytes())
 manifest['clips'].append({'id':key,'text':text,'sample_rate':audio.sample_rate,'samples':len(samples),'seconds':len(samples)/audio.sample_rate,'generation_seconds':time.monotonic()-start,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()})
 print(key+' cached',flush=True)
for f in out.glob('*.f32'):
 if f.stem not in texts:f.unlink() # remove clipes obsoletos
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

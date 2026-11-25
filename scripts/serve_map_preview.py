"""Local Harumi preview with bounded, fixed-provider map requests. No tile prefetch."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
import requests,json,time,hashlib,re,argparse,threading,io,gzip
from urllib.parse import unquote,quote
from functools import lru_cache
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/brazil/map-preview-cache';CACHE.mkdir(exist_ok=True,parents=True)
LAND,WATER,GREEN,ROAD,MAJOR,BUILDING,LABEL=(0x26222b,0x232a33,0x2a2d2b,0x6b5c6e,0x8a7589,0x2d2831,0xb9a6b8)
def _mix(a,b,t):return ((((a>>16&255)*(256-t)+(b>>16&255)*t+128)>>8)<<16)|((((a>>8&255)*(256-t)+(b>>8&255)*t+128)>>8)<<8)|(((a&255)*(256-t)+(b&255)*t+128)>>8)
@lru_cache(maxsize=None)
def tint_rgb(r,g,b,far):
 """Unica LUT do mapa escuro (espelho de TileTint.java): classe por cor + tinta de rotulo por luminancia."""
 lum=(299*r+587*g+114*b)//1000;m=min(r,g,b)
 if g>r+10 and g>b:base=GREEN
 elif r>=200 and r-b>=40:base=MAJOR
 else:
  if m>=233:base=_mix(LAND,ROAD,min(256,(m-233)*256//22))
  elif m>=201:base=_mix(BUILDING,LAND,(m-201)*256//32)
  else:base=BUILDING
  base=_mix(base,WATER,min(256,max(0,b-r-4)*256//36))
 c=_mix(base,LABEL,max(0,130-lum)*256//130)
 return _mix(c,LAND,77) if far else c
def tint_png(data,z):
 im=Image.open(io.BytesIO(data)).convert('RGBA');far=z<12
 im.putdata([((c:=tint_rgb(r,g,b,far))>>16&255,c>>8&255,c&255,a) for r,g,b,a in im.getdata()])
 out=io.BytesIO();im.save(out,'PNG');return out.getvalue()
route_lock=threading.Lock();last_route=0
OFM='https://tiles.openfreemap.org/';UA='HarumiAutoOS/0.3.15-dev.1 (personal navigation prototype)'
TPL_RE=re.compile(r'https://tiles\.openfreemap\.org/[A-Za-z0-9_./-]+/\{z\}/\{x\}/\{y\}\.pbf')
def gunzip_if_needed(data,limit):
 """O WebView nao decodifica gzip sem Content-Encoding: se vier gzip (1f 8b), descomprime respeitando o limite."""
 if data[:2]!=b'\x1f\x8b':return data
 out=gzip.GzipFile(fileobj=io.BytesIO(data)).read(limit+1)
 if len(out)>limit:raise ValueError('Too large')
 return out
def ofm_template():
 """Modelo de URL dos tiles vetoriais (TileJSON do OpenFreeMap, cache de 1 dia; sem rede usa o arquivo antigo)."""
 file=CACHE/hashlib.sha256((OFM+'planet').encode()).hexdigest()
 def parse(raw):
  t=json.loads(raw)['tiles'][0]
  if len(t)>300 or not TPL_RE.fullmatch(t) or '..' in t:raise ValueError('Untrusted tile template')
  return t
 if file.exists() and time.time()-file.stat().st_mtime<86400:
  try:return parse(file.read_bytes())
  except (ValueError,KeyError,IndexError,OSError):pass
 try:
  r=requests.get(OFM+'planet',headers={'User-Agent':UA},timeout=(8,16));r.raise_for_status()
  data=gunzip_if_needed(r.content,256*1024);t=parse(data);file.write_bytes(data);return t
 except requests.RequestException:
  if not file.exists():raise
  return parse(file.read_bytes())
def provider(path,query):
 if path=='/map-api/route':
  parts=parse_qs(query).get('points',[''])[0].split(',')
  if len(parts)!=4:raise ValueError()
  points=[float(x) for x in parts]
  if not all((-75<=x<=-30 if i%2==0 else -35<=x<=6) for i,x in enumerate(points)):raise ValueError()
  url='https://router.project-osrm.org/route/v1/driving/'+','.join(f'{p:.6f}' for p in points[:2])+';'+','.join(f'{p:.6f}' for p in points[2:])+'?overview=full&geometries=geojson&steps=false&alternatives=false'
  return url,'application/json',86400,4*1024*1024
 v=re.fullmatch(r'/map-api/vt/(\d{1,2})/(\d{1,6})/(\d{1,6})\.pbf',path)
 if v:
  z,x,y=map(int,v.groups())
  if not (0<=z<=14 and 0<=x<2**z and 0<=y<2**z):raise ValueError()
  return ofm_template().replace('{z}',str(z)).replace('{x}',str(x)).replace('{y}',str(y)),'application/x-protobuf',30*86400,2*1024*1024
 g=re.fullmatch(r'/map-api/glyphs/([^/]+)/(\d{1,6}-\d{1,6})\.pbf',path)
 if g:
  font=unquote(g.group(1))
  if not re.fullmatch(r'[A-Za-z][A-Za-z ,]{0,79}',font):raise ValueError()
  return OFM+'fonts/'+quote(font,safe='')+'/'+g.group(2)+'.pbf','application/x-protobuf',30*86400,2*1024*1024
 m=re.fullmatch(r'/map-api/tiles/(\d{1,2})/(\d{1,6})/(\d{1,6})\.png',path)
 if not m:raise ValueError()
 z,x,y=map(int,m.groups())
 if not (3<=z<=18 and 0<=x<2**z and 0<=y<2**z):raise ValueError()
 return f'https://tile.openstreetmap.org/{z}/{x}/{y}.png','image/png',604800,512*1024
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'app/src/main/assets'),**kwargs)
 def do_GET(self):
  global last_route
  u=urlsplit(self.path)
  if not u.path.startswith('/map-api/'):return super().do_GET()
  try:
   url,mime,ttl,limit=provider(u.path,u.query);z=int(u.path.split('/')[3]) if mime=='image/png' else 0;file=CACHE/hashlib.sha256((url+'|tint2' if mime=='image/png' else url).encode()).hexdigest();cached=file.exists() and time.time()-file.stat().st_mtime<ttl
   if cached:data=file.read_bytes()
   else:
    try:
     if mime=='application/json':
      with route_lock:
       delay=1.1-(time.monotonic()-last_route)
       if delay>0:time.sleep(delay)
       last_route=time.monotonic()
     response=requests.get(url,headers={'User-Agent':UA,'Referer':'http://127.0.0.1:8871/'},timeout=(8,16),stream=True,allow_redirects=False)
     response.raise_for_status();chunks=[];size=0
     for chunk in response.iter_content(16384):
      size+=len(chunk)
      if size>limit:raise ValueError('Too large')
      chunks.append(chunk)
     data=b''.join(chunks)
     if mime=='application/x-protobuf':data=gunzip_if_needed(data,limit)
     if mime=='image/png':data=tint_png(data,z)
     temp=file.with_suffix('.'+str(threading.get_ident())+'.tmp');temp.write_bytes(data);temp.replace(file)
    except requests.RequestException:
     if not file.exists():raise
     data=file.read_bytes();cached=True
   if mime=='application/json':
    body=json.loads(data);body.update(cached=cached,computedAt=int(file.stat().st_mtime*1000));data=json.dumps(body).encode()
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control',f'private, max-age={ttl}');self.end_headers();self.wfile.write(data)
  except ValueError:self.send_error(400)
  except (requests.RequestException,OSError):self.send_error(503)
 def log_message(self,*args):pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8871);a=p.parse_args();print(f'Harumi map preview http://127.0.0.1:{a.port}/index.html?mapa=1',flush=True);ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()

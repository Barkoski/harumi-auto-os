"""Public Brazil datasets, resumable downloads, integrity checks and local provenance."""
from pathlib import Path
import requests,time,json,hashlib,zipfile,shutil,concurrent.futures,threading
ROOT=Path(__file__).resolve().parents[1]/'data/brazil'
RAW=ROOT/'raw';RAW.mkdir(parents=True,exist_ok=True)
lock=threading.Lock()
sources=[
 ('osm-brazil','https://download.geofabrik.de/south-america/brazil-261101.osm.pbf','brazil-261101.osm.pbf','ODbL-1.0; © OpenStreetMap contributors; Geofabrik extract'),
 ('osm-md5','https://download.geofabrik.de/south-america/brazil-261101.osm.pbf.md5','brazil-261101.osm.pbf.md5','Geofabrik metadata'),
 ('geonames-br','https://download.geonames.org/export/dump/BR.zip','geonames-BR.zip','CC-BY-4.0; GeoNames'),
 ('geonames-readme','https://download.geonames.org/export/dump/readme.txt','geonames-readme.txt','GeoNames documentation'),
 ('geonames-admin1','https://download.geonames.org/export/dump/admin1CodesASCII.txt','geonames-admin1.txt','CC-BY-4.0; GeoNames'),
 ('ibge-municipalities','https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome','ibge-municipios.json','Fonte: IBGE / API de Localidades; retain attribution'),
 ('ibge-states','https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome','ibge-estados.json','Fonte: IBGE / API de Localidades; retain attribution'),
 ('wikivoyage-pt','https://dumps.wikimedia.org/ptwikivoyage/latest/ptwikivoyage-latest-pages-articles.xml.bz2','ptwikivoyage-pages-articles.xml.bz2','Wikimedia / Wikivoyage; retain page revision URLs and applicable CC-BY-SA attribution'),
 ('wikivoyage-md5','https://dumps.wikimedia.org/ptwikivoyage/latest/ptwikivoyage-latest-md5sums.txt','ptwikivoyage-md5sums.txt','Wikimedia dump metadata'),
]
manifest={'scope':'Brazil national public OSM extract; IBGE localities; GeoNames Brazil; Portuguese Wikivoyage source dump (worldwide, Brazil selection during indexing)','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sources':{},'status':'downloading'}
def save():
 with lock:
  tmp=ROOT/'download-manifest.tmp';tmp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(ROOT/'download-manifest.json')
def fetch(item):
 key,url,name,license=item;dst=RAW/name;part=RAW/(name+'.part')
 record={'url':url,'file':name,'attribution':license,'status':'downloading'}
 with lock:manifest['sources'][key]=record
 save()
 if not dst.exists():
  for attempt in range(4):
   try:
    offset=part.stat().st_size if part.exists() else 0
    response=requests.get(url,headers={'User-Agent':'HarumiAutoOS-DataPreparation/1.0 (local personal research)','Range':f'bytes={offset}-'} if offset else {'User-Agent':'HarumiAutoOS-DataPreparation/1.0 (local personal research)'},stream=True,timeout=(20,60))
    response.raise_for_status()
    if offset and response.status_code!=206:offset=0
    total=offset+int(response.headers.get('Content-Length','0'))
    if shutil.disk_usage(ROOT).free<max(0,total-offset)+6*1024**3:raise RuntimeError('Insufficient reserve: need download plus 6 GiB free')
    record.update(expected_bytes=total,last_modified=response.headers.get('Last-Modified'),etag=response.headers.get('ETag'),resolved_url=response.url)
    mode='ab' if offset else 'wb';done=offset;reported=offset
    with part.open(mode) as f:
     for chunk in response.iter_content(1024*1024):
      if not chunk:continue
      f.write(chunk);done+=len(chunk)
      if done-reported>=64*1024**2:
       record['downloaded_bytes']=done;save();print(f'{key}: {done/1024**2:.0f} / {total/1024**2:.0f} MiB',flush=True);reported=done
    if total and part.stat().st_size!=total:raise IOError('Incomplete response')
    part.replace(dst);break
   except Exception:
    if attempt==3:raise
    time.sleep(2*(attempt+1))
 if name.endswith('.zip'):
  with zipfile.ZipFile(dst) as z:assert z.testzip() is None
 if name.endswith('.json'):
  data=json.loads(dst.read_text(encoding='utf-8-sig'));assert isinstance(data,list) and len(data)>20
 record.update(status='downloaded',bytes=dst.stat().st_size,sha256=hashlib.file_digest(dst.open('rb'),'sha256').hexdigest(),completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 save();print(key+': downloaded and hashed',flush=True)
 return key
def main():
 failures=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  tasks={pool.submit(fetch,item):item[0] for item in sources}
  for future in concurrent.futures.as_completed(tasks):
   try:future.result()
   except Exception as e:
    key=tasks[future];manifest['sources'][key].update(status='failed',error=str(e));failures.append(key);save();print(key+': '+str(e),flush=True)
 if failures:raise RuntimeError('Failed: '+', '.join(failures))
 osm=RAW/'brazil-261101.osm.pbf';expected=(RAW/'brazil-261101.osm.pbf.md5').read_text().split()[0]
 assert hashlib.file_digest(osm.open('rb'),'md5').hexdigest()==expected,'OSM publisher checksum mismatch'
 manifest['sources']['osm-brazil']['publisher_md5_verified']=True
 wiki=RAW/'ptwikivoyage-pages-articles.xml.bz2'
 line=next(l for l in (RAW/'ptwikivoyage-md5sums.txt').read_text().splitlines() if l.split()[-1].endswith('-pages-articles.xml.bz2'))
 assert hashlib.file_digest(wiki.open('rb'),'md5').hexdigest()==line.split()[0],'Wikivoyage publisher checksum mismatch'
 manifest['sources']['wikivoyage-pt']['publisher_md5_verified']=True
 manifest.update(status='complete',completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));save();print('ALL DATASETS COMPLETE',flush=True)
if __name__=='__main__':main()

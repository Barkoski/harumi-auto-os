"""Offline UF atlas: IBGE geometry + Commons capital photographs with attribution."""
from pathlib import Path
import requests,json,math,re,html,hashlib,sqlite3,unicodedata,concurrent.futures
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/brazil/raw';ASSETS=ROOT/'app/src/main/assets';OUT=ASSETS/'atlas';OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'HarumiAutoOS-Atlas/1.0 (offline local app)'}
CAPITALS={'AC':('Rio Branco','Rio Branco (Acre)'),'AL':('Maceió','Maceió'),'AP':('Macapá','Macapá'),'AM':('Manaus','Manaus'),'BA':('Salvador','Salvador'),'CE':('Fortaleza','Fortaleza'),'DF':('Brasília','Brasília'),'ES':('Vitória','Vitória (Espírito Santo)'),'GO':('Goiânia','Goiânia'),'MA':('São Luís','São Luís (Maranhão)'),'MT':('Cuiabá','Cuiabá'),'MS':('Campo Grande','Campo Grande (Mato Grosso do Sul)'),'MG':('Belo Horizonte','Belo Horizonte'),'PA':('Belém','Belém (Pará)'),'PB':('João Pessoa','João Pessoa'),'PR':('Curitiba','Curitiba'),'PE':('Recife','Recife'),'PI':('Teresina','Teresina'),'RJ':('Rio de Janeiro','Rio de Janeiro'),'RN':('Natal','Natal (Rio Grande do Norte)'),'RS':('Porto Alegre','Porto Alegre'),'RO':('Porto Velho','Porto Velho'),'RR':('Boa Vista','Boa Vista (Roraima)'),'SC':('Florianópolis','Florianópolis'),'SP':('São Paulo','São Paulo'),'SE':('Aracaju','Aracaju'),'TO':('Palmas','Palmas')}
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if unicodedata.category(c)!='Mn')
def clean(s):return html.unescape(re.sub('<[^>]*>','',s or '')).strip()
def getjson(url,params=None):
 r=requests.get(url,params=params,headers=HEADERS,timeout=30);r.raise_for_status();return r.json()
def main():
 geom_url='https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF'
 if not (RAW/'brazil-uf.geojson').exists():(RAW/'brazil-uf.geojson').write_text(json.dumps(getjson(geom_url)),encoding='utf-8')
 geo=json.loads((RAW/'brazil-uf.geojson').read_text(encoding='utf-8'));assert len(geo['features'])==27
 states=json.loads((RAW/'ibge-estados.json').read_text(encoding='utf-8'));byid={str(s['id']):s for s in states}
 wiki=getjson('https://pt.wikipedia.org/w/api.php',{'action':'query','titles':'|'.join(t[1] for t in CAPITALS.values()),'prop':'pageimages','piprop':'thumbnail|original','pithumbsize':800,'redirects':1,'format':'json'})
 (RAW/'atlas-wikipedia-image-sources.json').write_text(json.dumps(wiki,ensure_ascii=False,indent=2),encoding='utf-8')
 aliases={n['from']:n['to'] for n in wiki['query'].get('normalized',[])+wiki['query'].get('redirects',[])};pages={p['title']:p for p in wiki['query']['pages'].values()}
 def canonical(title):
  for _ in range(5):
   if title not in aliases:return title
   title=aliases[title]
  return title
 chosen={uf:pages[canonical(value[1])] for uf,value in CAPITALS.items()}
 files={uf:unquote(urlparse(p['original']['source']).path.split('/')[-1]) for uf,p in chosen.items()}
 metadata=getjson('https://commons.wikimedia.org/w/api.php',{'action':'query','titles':'|'.join('File:'+v for v in files.values()),'prop':'imageinfo','iiprop':'url|extmetadata','format':'json'})
 (RAW/'atlas-commons-rights.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
 rights={p['title'].replace('_',' '):p['imageinfo'][0] for p in metadata['query']['pages'].values() if p.get('imageinfo')}
 def photo(uf):
  p=chosen[uf];url=p['thumbnail']['source'];assert urlparse(url).hostname in {'thumb.wikimedia.org','upload.wikimedia.org'}
  assert '/wikipedia/commons/' in p['original']['source'],'Only freely licensed Commons photographs are accepted'
  info=rights['File:'+files[uf].replace('_',' ')];ext=info.get('extmetadata',{})
  license=clean(ext.get('LicenseShortName',{}).get('value',''));assert license,'Missing license'
  response=requests.get(url,headers=HEADERS,timeout=30);response.raise_for_status();mime=response.headers.get('Content-Type','').split(';')[0]
  suffix={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}.get(mime);assert suffix,'Photo must be raster, got '+mime
  assert len(response.content)<4*1024**2
  path=OUT/(uf+suffix);path.write_bytes(response.content)
  from PIL import Image
  with Image.open(path) as image:assert image.width>300 and image.height>150
  print(uf+' capital photo downloaded',flush=True)
  return uf,{'file':'atlas/'+path.name,'author':clean(ext.get('Artist',{}).get('value','')),'credit':clean(ext.get('Credit',{}).get('value','')),'license':license,'license_url':clean(ext.get('LicenseUrl',{}).get('value','')),'source_url':info.get('descriptionurl'),'file_title':'File:'+files[uf],'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:photos=dict(pool.map(photo,CAPITALS))
 rings=[]
 for f in geo['features']:
  polygons=[f['geometry']['coordinates']] if f['geometry']['type']=='Polygon' else f['geometry']['coordinates']
  rings.extend(r for polygon in polygons for r in polygon)
 points=[pt for ring in rings for pt in ring];cos=math.cos(math.radians(15));xs=[p[0]*cos for p in points];ys=[-p[1] for p in points];xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys);scale=min(580/(xmax-xmin),560/(ymax-ymin));left=(620-(xmax-xmin)*scale)/2;top=(600-(ymax-ymin)*scale)/2
 def project(lon,lat):return [round(left+(lon*cos-xmin)*scale,2),round(top+(-lat-ymin)*scale,2)]
 c=sqlite3.connect(ROOT/'data/brazil/harumi-brazil.sqlite');data=[]
 for f in geo['features']:
  s=byid[f['properties']['codarea']];uf=s['sigla'];capital=CAPITALS[uf][0]
  rows=c.execute('SELECT ibge_id FROM municipality WHERE state=? AND name_key=?',(uf,norm(capital))).fetchall();assert len(rows)==1,(uf,capital,rows)
  point=c.execute("SELECT id,lat,lon FROM geoname WHERE name_key=? AND feature_class='P' ORDER BY CASE feature_code WHEN 'PPLC' THEN 0 WHEN 'PPLA' THEN 1 ELSE 2 END,population DESC LIMIT 1",(norm(capital),)).fetchone();assert point
  polygons=[f['geometry']['coordinates']] if f['geometry']['type']=='Polygon' else f['geometry']['coordinates'];parts=[]
  for polygon in polygons:
   for ring in polygon:
    xy=[project(*p) for p in ring];parts.append('M'+' L'.join(str(x)+','+str(y) for x,y in xy)+' Z')
  data.append({'uf':uf,'id':s['id'],'name':s['nome'],'capital':capital,'capital_ibge_id':rows[0][0],'capital_geoname_id':point[0],'capital_point':project(point[2],point[1]),'municipalities':c.execute('SELECT COUNT(*) FROM municipality WHERE state=?',(uf,)).fetchone()[0],'path':' '.join(parts),'photo':photos[uf]})
 c.close();data.sort(key=lambda s:s['name'])
 result={'geometry_source':geom_url,'geometry_attribution':'Fonte: IBGE / API de Malhas simplificadas','photo_sources':'Wikimedia Commons; per-photo author and license retained','viewbox':'0 0 620 600','states':data}
 (OUT/'atlas-data.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 (ASSETS/'atlas-data.js').write_text('window.HARUMI_ATLAS_DATA='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 print('27-state atlas ready',flush=True)
if __name__=='__main__':main()

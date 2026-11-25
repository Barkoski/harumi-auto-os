from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import sqlite3,json,re,unicodedata
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/brazil';DB=DATA/'harumi-brazil.sqlite';WEB=ROOT/'scripts/data-review'
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if unicodedata.category(c)!='Mn')
def search(q,kind):
 if not 1<=len(q)<=100:raise ValueError('Informe de 1 a 100 caracteres.')
 tokens=re.findall(r'\w+',q,flags=re.UNICODE)[:8]
 if not tokens:raise ValueError('Informe um nome.')
 fts=' '.join('"'+t+'"' for t in tokens);key=norm(q)
 c=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True,timeout=2);c.row_factory=sqlite3.Row
 try:
  if kind=='cities':
   rows=c.execute('SELECT name,state,state_name,ibge_id FROM municipality WHERE name_key LIKE ? ORDER BY name,state LIMIT 40',(key+'%',)).fetchall()
   result=[dict(r,source='IBGE',url='https://servicodados.ibge.gov.br/api/v1/localidades/municipios/'+str(r['ibge_id'])) for r in rows]
  elif kind=='geonames':
   rows=c.execute("SELECT id,name,lat,lon,feature_class,feature_code,population,modified FROM geoname WHERE name_key LIKE ? ORDER BY CASE WHEN feature_class='P' THEN 0 ELSE 1 END,population DESC LIMIT 40",(key+'%',)).fetchall()
   result=[dict(r,source='GeoNames / CC-BY-4.0',url='https://www.geonames.org/'+str(r['id'])) for r in rows]
  elif kind=='guides':
   rows=c.execute("SELECT a.id,a.title AS name,a.modified,a.url,a.scope,substr(a.body,1,1300) AS excerpt,a.review_status FROM wiki_search JOIN wiki_article a ON a.rowid=wiki_search.rowid WHERE wiki_search MATCH ? AND a.scope LIKE 'BR%' ORDER BY CASE WHEN a.title_key=? THEN 0 ELSE 1 END,a.title LIMIT 20",(fts,key)).fetchall()
   result=[]
   for row in rows:
    item=dict(row,source='Wikivoyage / CC-BY-SA-4.0');item['listings']=[dict(x) for x in c.execute('SELECT kind,name,description FROM guide_listing WHERE article_id=? LIMIT 30',(row['id'],))];result.append(item)
  elif kind in {'poi','roads'}:
   table='poi_search' if kind=='poi' else 'road_search'
   if not c.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():return {'status':'indexing','results':[],'message':'O mapa nacional ainda está sendo indexado.'}
   if kind=='poi':
    rows=c.execute('SELECT p.osm_type,p.osm_id,p.name,p.category,p.subcategory,p.city,p.lat,p.lon,p.coordinate_method FROM poi_search JOIN poi p ON p.rowid=poi_search.rowid WHERE poi_search MATCH ? LIMIT 40',(fts,)).fetchall()
    result=[dict(r,source='© OpenStreetMap contributors / ODbL-1.0',url='https://www.openstreetmap.org/'+r['osm_type']+'/'+str(r['osm_id'])) for r in rows]
   else:
    rows=c.execute('SELECT p.osm_id,p.name,p.kind,p.ref FROM road_search JOIN road p ON p.rowid=road_search.rowid WHERE road_search MATCH ? LIMIT 40',(fts,)).fetchall()
    result=[dict(r,source='© OpenStreetMap contributors / ODbL-1.0',url='https://www.openstreetmap.org/way/'+str(r['osm_id'])) for r in rows]
  else:raise ValueError('Categoria inválida.')
  return {'status':'ok','results':result,'query':q,'category':kind}
 finally:c.close()
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  u=urlparse(self.path)
  try:
   if u.path=='/api/search':
    params=parse_qs(u.query);value=search(params.get('q',[''])[0],params.get('kind',['cities'])[0]);payload=json.dumps(value,ensure_ascii=False).encode();mime='application/json; charset=utf-8'
   elif u.path=='/api/status':
    value={}
    for name in ['download-manifest.json','index-report.json']:
     if (DATA/name).exists():value[name]=json.loads((DATA/name).read_text(encoding='utf-8'))
    payload=json.dumps(value,ensure_ascii=False).encode();mime='application/json; charset=utf-8'
   elif u.path in ['/','/index.html','/review.js','/review.css']:
    name='index.html' if u.path in ['/','/index.html'] else u.path[1:];payload=(WEB/name).read_bytes();mime={'html':'text/html; charset=utf-8','js':'application/javascript; charset=utf-8','css':'text/css; charset=utf-8'}[name.split('.')[-1]]
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'");self.end_headers();self.wfile.write(payload)
  except (ValueError,sqlite3.Error) as e:self.send_error(400,str(e))
 def log_message(self,*args):pass
if __name__=='__main__':
 print('Harumi data review: http://127.0.0.1:8872',flush=True);ThreadingHTTPServer(('127.0.0.1',8872),Handler).serve_forever()

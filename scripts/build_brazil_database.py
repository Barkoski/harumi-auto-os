"""Stream public sources into a provenance-aware SQLite/FTS4 knowledge base. No model training."""
from pathlib import Path
import sqlite3,json,zipfile,bz2,xml.etree.ElementTree as ET,re,time,unicodedata,argparse
from urllib.parse import quote
import mwparserfromhell
ROOT=Path(__file__).resolve().parents[1]/'data/brazil';RAW=ROOT/'raw';DB=ROOT/'harumi-brazil.sqlite'
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if unicodedata.category(c)!='Mn').strip()
def connection():
 c=sqlite3.connect(DB);c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA synchronous=NORMAL');c.execute('PRAGMA cache_size=-32000');return c
SCHEMA='''
CREATE TABLE IF NOT EXISTS source(id TEXT PRIMARY KEY,url TEXT,attribution TEXT,sha256 TEXT,data_date TEXT);
CREATE TABLE IF NOT EXISTS municipality(ibge_id INTEGER PRIMARY KEY,name TEXT,name_key TEXT,state TEXT,state_name TEXT,source_id TEXT DEFAULT 'ibge-municipalities');
CREATE TABLE IF NOT EXISTS geoname(id INTEGER PRIMARY KEY,name TEXT,name_key TEXT,alternate_names TEXT,lat REAL,lon REAL,feature_class TEXT,feature_code TEXT,admin1 TEXT,population INTEGER,modified TEXT,source_id TEXT DEFAULT 'geonames-br');
CREATE TABLE IF NOT EXISTS wiki_article(id INTEGER PRIMARY KEY,title TEXT,title_key TEXT,revision TEXT,modified TEXT,url TEXT,scope TEXT,body TEXT,wikitext TEXT,review_status TEXT DEFAULT 'unreviewed',source_id TEXT DEFAULT 'wikivoyage-pt');
CREATE TABLE IF NOT EXISTS guide_listing(id INTEGER PRIMARY KEY,article_id INTEGER,kind TEXT,name TEXT,description TEXT,fields_json TEXT,source_url TEXT,review_status TEXT DEFAULT 'unreviewed');
CREATE TABLE IF NOT EXISTS poi(osm_type TEXT,osm_id INTEGER,name TEXT,category TEXT,subcategory TEXT,description TEXT,city TEXT,state TEXT,lat REAL,lon REAL,coordinate_method TEXT,mid_ref INTEGER,tags_json TEXT,source_id TEXT DEFAULT 'osm-brazil',PRIMARY KEY(osm_type,osm_id));
CREATE TABLE IF NOT EXISTS road(osm_id INTEGER PRIMARY KEY,kind TEXT,name TEXT,ref TEXT,nodes_json TEXT,tags_json TEXT,source_id TEXT DEFAULT 'osm-brazil');
CREATE TABLE IF NOT EXISTS build_state(key TEXT PRIMARY KEY,value TEXT);
'''
def sources(c):
 m=json.loads((ROOT/'download-manifest.json').read_text(encoding='utf-8'))
 for key,v in m['sources'].items():c.execute('INSERT OR REPLACE INTO source VALUES(?,?,?,?,?)',(key,v['url'],v['attribution'],v.get('sha256'),v.get('last_modified') or v.get('completed_utc')))
def set_state(c,key,value):c.execute('INSERT OR REPLACE INTO build_state VALUES(?,?)',(key,json.dumps(value,ensure_ascii=False)));c.commit()
def small():
 c=connection();c.executescript(SCHEMA);sources(c)
 states=json.loads((RAW/'ibge-estados.json').read_text(encoding='utf-8'))
 municipalities=json.loads((RAW/'ibge-municipios.json').read_text(encoding='utf-8'))
 for m in municipalities:
  uf=(m.get('microrregiao') or {}).get('mesorregiao',{}).get('UF') or (m.get('regiao-imediata') or {}).get('regiao-intermediaria',{}).get('UF')
  if not uf:raise ValueError('Missing UF in IBGE record '+str(m['id']))
  c.execute('INSERT OR REPLACE INTO municipality(ibge_id,name,name_key,state,state_name) VALUES(?,?,?,?,?)',(m['id'],m['nome'],norm(m['nome']),uf['sigla'],uf['nome']))
 with zipfile.ZipFile(RAW/'geonames-BR.zip') as z:
  import io
  for line in io.TextIOWrapper(z.open('BR.txt'),encoding='utf-8'):
   f=line.rstrip('\n').split('\t');assert f[8]=='BR'
   c.execute('INSERT OR REPLACE INTO geoname(id,name,name_key,alternate_names,lat,lon,feature_class,feature_code,admin1,population,modified) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(int(f[0]),f[1],norm(f[1]),f[3],float(f[4]),float(f[5]),f[6],f[7],f[10],int(f[14] or 0),f[18]))
 c.commit();c.execute('DELETE FROM guide_listing')
 state_keys={norm(s['nome']) for s in states}
 pages=[]
 for _,e in ET.iterparse(bz2.open(RAW/'ptwikivoyage-pages-articles.xml.bz2'),events=['end']):
  if not e.tag.endswith('}page'):continue
  ns={'m':e.tag.split('}')[0][1:]}
  if e.findtext('m:ns',namespaces=ns)!='0':e.clear();continue
  title=e.findtext('m:title',namespaces=ns);raw=e.findtext('m:revision/m:text',default='',namespaces=ns) or ''
  pid=int(e.findtext('m:id',namespaces=ns));revision=e.findtext('m:revision/m:id',namespaces=ns);modified=e.findtext('m:revision/m:timestamp',namespaces=ns)
  code=mwparserfromhell.parse(raw);parents=[]
  for t in code.filter_templates():
   if norm(str(t.name)) in {'ispartof','isin','estaem','esta em','parte de','partede'} and t.params:parents.append(str(t.params[0].value).strip())
  links={norm(str(l.title).split('#')[0]) for l in mwparserfromhell.parse(raw[:2000]).filter_wikilinks()}
  scope='BR-evidence' if norm(title)=='brasil' or 'brasil' in links or state_keys.intersection(links) else 'unresolved'
  # Keep template values: listings often hold all useful attraction descriptions.
  template_values=[' '.join(str(p.value).strip() for p in t.params) for t in code.filter_templates()]
  plain=str(code.strip_code())+'\n'+'\n'.join(template_values)
  plain=re.sub(r'\n{3,}','\n\n',plain).strip()
  url='https://pt.wikivoyage.org/w/index.php?title='+quote(title)+'&oldid='+str(revision)
  c.execute('INSERT OR REPLACE INTO wiki_article(id,title,title_key,revision,modified,url,scope,body,wikitext) VALUES(?,?,?,?,?,?,?,?,?)',(pid,title,norm(title),revision,modified,url,scope,plain,raw))
  for t in code.filter_templates():
   fields={norm(str(p.name)):str(p.value).strip() for p in t.params};name=fields.get('nome') or fields.get('name')
   if name and norm(str(t.name)) in {'veja','ver','faca','see','do','eat','drink','sleep','buy','comer','beba','durma','compre','listing'}:
    c.execute('INSERT INTO guide_listing(article_id,kind,name,description,fields_json,source_url) VALUES(?,?,?,?,?,?)',(pid,str(t.name).strip(),name,fields.get('sobre') or fields.get('content') or '',json.dumps(fields,ensure_ascii=False),url))
  pages.append((pid,parents));e.clear()
 # Conservative scope propagation from declared travel parents; unresolved remains explicit.
 for _ in range(8):
  changed=0
  for pid,parents in pages:
   for parent in parents:
    found=c.execute('SELECT scope FROM wiki_article WHERE title_key=?',(norm(parent),)).fetchone()
    if found and found[0].startswith('BR'):
     changed+=c.execute("UPDATE wiki_article SET scope='BR-parent' WHERE id=? AND scope='unresolved'",(pid,)).rowcount;break
  if not changed:break
 c.executescript('''CREATE INDEX IF NOT EXISTS municipality_name ON municipality(name_key,state);
 CREATE INDEX IF NOT EXISTS geoname_name ON geoname(name_key,feature_class,population);
 CREATE INDEX IF NOT EXISTS wiki_title ON wiki_article(title_key);
 CREATE INDEX IF NOT EXISTS listings_article ON guide_listing(article_id);
 DROP TABLE IF EXISTS wiki_search;
 CREATE VIRTUAL TABLE wiki_search USING fts4(title,body,content='wiki_article',tokenize=unicode61);
 INSERT INTO wiki_search(wiki_search) VALUES('rebuild');''')
 set_state(c,'small_sources_complete',True);c.close();print('Small datasets indexed',flush=True);report()
def osm():
 import osmium
 c=connection();c.executescript(SCHEMA);sources(c)
 manifest=json.loads((ROOT/'download-manifest.json').read_text(encoding='utf-8'))
 assert manifest['status']=='complete' and manifest['sources']['osm-brazil']['publisher_md5_verified']
 if c.execute("SELECT value FROM build_state WHERE key='osm_complete'").fetchone()==('true',):print('OSM already indexed');return
 c.execute('DELETE FROM poi');c.execute('DELETE FROM road');c.commit()
 pool=osmium.io.ThreadPool(2,8);keys=osmium.filter.KeyFilter('tourism','amenity','leisure','historic','natural','place','highway')
 selected=0;started=time.monotonic();needed=set();pbf=RAW/'brazil-261101.osm.pbf'
 for obj in osmium.FileProcessor(pbf,thread_pool=pool).with_filter(keys):
  tags=dict(obj.tags);selected+=1
  if obj.is_way() and 'highway' in tags:
   c.execute('INSERT INTO road(osm_id,kind,name,ref,nodes_json,tags_json) VALUES(?,?,?,?,?,?)',(obj.id,tags['highway'],tags.get('name',''),tags.get('ref',''),json.dumps([n.ref for n in obj.nodes]),json.dumps(tags,ensure_ascii=False)))
  category=next((k for k in ['tourism','historic','leisure','amenity','natural','place'] if k in tags),None)
  if category and (tags.get('name') or category=='tourism'):
   lat=lon=None;mid=None;method='unlocated'
   if obj.is_node() and obj.location.valid():lat=obj.location.lat;lon=obj.location.lon;method='source-node'
   elif obj.is_way() and len(obj.nodes):mid=obj.nodes[len(obj.nodes)//2].ref;needed.add(mid);method='representative-way-node-pending'
   c.execute('INSERT OR IGNORE INTO poi(osm_type,osm_id,name,category,subcategory,description,city,state,lat,lon,coordinate_method,mid_ref,tags_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',('node' if obj.is_node() else 'way' if obj.is_way() else 'relation',obj.id,tags.get('name',''),category,tags[category],tags.get('description:pt') or tags.get('description',''),tags.get('addr:city',''),tags.get('addr:state',''),lat,lon,method,mid,json.dumps(tags,ensure_ascii=False)))
  if selected%10000==0:c.commit()
  if selected%100000==0:print(f'OSM selected objects {selected:,}; elapsed {time.monotonic()-started:.0f}s',flush=True)
 c.commit();print(f'Looking up {len(needed):,} representative node coordinates',flush=True)
 c.execute('CREATE INDEX IF NOT EXISTS poi_mid ON poi(mid_ref)')
 for node in osmium.FileProcessor(pbf,entities=osmium.osm.NODE,thread_pool=pool).with_filter(osmium.filter.IdFilter(needed)):
  if node.location.valid():c.execute("UPDATE poi SET lat=?,lon=?,coordinate_method='representative-way-node' WHERE mid_ref=?",(node.location.lat,node.location.lon,node.id))
 c.commit();c.executescript('''CREATE INDEX IF NOT EXISTS poi_coordinates ON poi(lat,lon);
 CREATE INDEX IF NOT EXISTS poi_category ON poi(category,subcategory);
 CREATE INDEX IF NOT EXISTS road_ref ON road(ref);
 DROP TABLE IF EXISTS poi_search;
 CREATE VIRTUAL TABLE poi_search USING fts4(name,description,city,content='poi',tokenize=unicode61);
 INSERT INTO poi_search(poi_search) VALUES('rebuild');
 DROP TABLE IF EXISTS road_search;
 CREATE VIRTUAL TABLE road_search USING fts4(name,ref,content='road',tokenize=unicode61);
 INSERT INTO road_search(road_search) VALUES('rebuild');''')
 set_state(c,'osm_complete',True);set_state(c,'osm_selected_objects',selected);c.execute('ANALYZE');c.commit();c.execute('PRAGMA wal_checkpoint(TRUNCATE)');c.close();report()
def report():
 c=connection();stats={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['municipality','geoname','wiki_article','guide_listing','poi','road']}
 stats.update(wiki_brazil_evidence=c.execute("SELECT COUNT(*) FROM wiki_article WHERE scope LIKE 'BR%'").fetchone()[0],poi_with_coordinates=c.execute('SELECT COUNT(*) FROM poi WHERE lat IS NOT NULL AND lon IS NOT NULL').fetchone()[0],database_bytes=DB.stat().st_size,integrity=c.execute('PRAGMA quick_check').fetchone()[0],state=dict(c.execute('SELECT key,value FROM build_state')))
 c.close();(ROOT/'index-report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(stats,ensure_ascii=True),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--osm',action='store_true');a=p.parse_args();osm() if a.osm else small()

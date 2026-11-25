"""Match IBGE municipality names/UF to GeoNames populated places. Never invent coordinates."""
from pathlib import Path
import sqlite3,json,unicodedata
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if unicodedata.category(c)!='Mn')
def main():
 raw=ROOT/'data/brazil/raw';states=json.loads((raw/'ibge-estados.json').read_text('utf-8'));byname={norm(s['nome']):s['sigla'] for s in states};admin={'07':'DF'}
 for line in (raw/'geonames-admin1.txt').read_text('utf-8').splitlines():
  f=line.split('\t')
  if f[0].startswith('BR.') and norm(f[1]) in byname:admin[f[0][3:]]=byname[norm(f[1])]
 c=sqlite3.connect(ROOT/'data/brazil/harumi-brazil.sqlite');municipal={(x[0],x[1]) for x in c.execute('select name_key,state from municipality')};cities=[];seen=set()
 for id,name,key,lat,lon,code,pop,feat in c.execute("SELECT id,name,name_key,lat,lon,admin1,population,feature_code FROM geoname WHERE feature_class='P' ORDER BY CASE WHEN feature_code IN ('PPLC','PPLA','PPLA2') THEN 0 ELSE 1 END,population DESC"):
  uf=admin.get(code);pair=(key,uf)
  if pair in municipal and pair not in seen:
   cities.append({'id':id,'name':name,'uf':uf,'lat':lat,'lon':lon,'population':pop});seen.add(pair)
 (ROOT/'app/src/main/assets/cities-data.js').write_text('window.HARUMI_CITIES='+json.dumps(cities,ensure_ascii=False,separators=(',',':'))+';','utf-8')
 report={'matched':len(cities),'unmatched':[{'name_key':n,'uf':uf} for n,uf in sorted(municipal-seen)],'sources':['IBGE municipality names and UF','GeoNames populated places; source coordinate'], 'limits':'City centers only; no street address geocoding. Exact name+UF matches; some centers may need review.'}
 (ROOT/'data/brazil/city-centers-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print('Matched city centers:',len(cities))
if __name__=='__main__':main()

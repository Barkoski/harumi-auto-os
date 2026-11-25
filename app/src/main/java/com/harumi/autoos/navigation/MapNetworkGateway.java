package com.harumi.autoos.navigation;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.util.Log;
import android.webkit.WebResourceResponse;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.*;
import org.json.JSONObject;

/** Fixed providers only. No arbitrary URL proxy and no network access for the assistant. */
public final class MapNetworkGateway {
    private static final String PREFIX="/assets/map-api/";
    private static final long DAY=86400000L,ROUTE_TTL=5*60*1000L;
    private final File cache;
    private static long lastProviderRequest;
    private static synchronized void pace() throws IOException {long wait=1100-(System.currentTimeMillis()-lastProviderRequest);if(wait>0)try{Thread.sleep(wait);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException(e);}lastProviderRequest=System.currentTimeMillis();}
    private final String userAgent;
    private final OfflineTiles offline;
    private final OfflineRouter offlineRouter;
    private final OfflineSearch offlineSearch;
    private final File forceOfflineFlag; // so em build debuggable: arquivo rotas/forcar-offline pula a rede (teste do roteador local)
    public MapNetworkGateway(Context context,String version){cache=new File(context.getCacheDir(),"maps");cache.mkdirs();offline=new OfflineTiles(context);offlineRouter=new OfflineRouter(context);offlineSearch=new OfflineSearch(context);offlineRouter.warmUp();{File ext=context.getExternalFilesDir(null);boolean dbg=(context.getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0;forceOfflineFlag=dbg&&ext!=null?new File(new File(ext,"rotas"),"forcar-offline"):null;}userAgent=userAgent(version);pruneAsync(cache);}
    static String userAgent(String version){return "HarumiAutoOS/"+(version==null||version.isBlank()?"unknown":version)+" (com.harumi.autoos; personal navigation prototype)";}
    public WebResourceResponse intercept(Uri uri){
        String path=uri.getPath();if(path==null||!path.startsWith(PREFIX))return null;
        try{
            String sub=path.substring(PREFIX.length()),url,mime;long ttl;int limit;boolean isTile=false,unzip=false;int tz=0,vz=-1,vx=0,vy=0;
            boolean route=sub.equals("route"),geocode=sub.equals("geocode");
            if(route){
                url=routeUrl(uri.getQueryParameter("points"),RouteCoordinates.parseBearing(uri.getQueryParameter("bearing")));
                mime="application/json";ttl=ROUTE_TTL;limit=2*1024*1024;
            }else if(geocode){
                url=geocodeUrl(uri.getQueryParameter("q"),uri.getQueryParameter("lat"),uri.getQueryParameter("lon"));
                mime="application/json";ttl=30*DAY;limit=64*1024;
            }else if(sub.matches("tiles/\\d{1,2}/\\d{1,6}/\\d{1,6}\\.png")){
                String[] tile=sub.substring(6,sub.length()-4).split("/");
                int z=Integer.parseInt(tile[0]),x=Integer.parseInt(tile[1]),y=Integer.parseInt(tile[2]);
                if(z<3||z>18||x<0||y<0||x>=(1<<z)||y>=(1<<z))throw new IllegalArgumentException();
                url="https://tile.openstreetmap.org/"+z+"/"+x+"/"+y+".png";
                mime="image/png";ttl=7*DAY;limit=512*1024;isTile=true;tz=z;
            }else if(sub.matches("vt/\\d{1,2}/\\d{1,6}/\\d{1,6}\\.pbf")){
                String[] t=sub.substring(3,sub.length()-4).split("/");
                vz=Integer.parseInt(t[0]);vx=Integer.parseInt(t[1]);vy=Integer.parseInt(t[2]);
                if(vz>14||vx>=(1<<vz)||vy>=(1<<vz))throw new IllegalArgumentException("Invalid tile");
                // Internet primeiro (mapa atualizado); sem rede, o MBTiles local do Brasil.
                try{url=vectorTileUrl(openFreeMapTemplate(),vz,vx,vy);}
                catch(IOException|RuntimeException e){WebResourceResponse local=offlineVectorTile(vz,vx,vy);if(local!=null)return local;throw e;}
                mime="application/x-protobuf";ttl=30*DAY;limit=2*1024*1024;unzip=true;
            }else if(sub.startsWith("glyphs/")){
                String[] g=sub.substring(7).split("/");
                if(g.length!=2||!g[1].endsWith(".pbf"))throw new IllegalArgumentException();
                url=glyphsUrl(g[0],g[1].substring(0,g[1].length()-4));
                mime="application/x-protobuf";ttl=30*DAY;limit=2*1024*1024;unzip=true;
            }else return error(400);
            File file=new File(cache,hex(MessageDigest.getInstance("SHA-256").digest((isTile?url+"|tint2":url).getBytes(StandardCharsets.UTF_8))));
            byte[] bytes=null;long computedAt=0;boolean viaOffline=false;boolean force=(route||geocode)&&forceOfflineFlag!=null&&forceOfflineFlag.isFile();boolean cached=!force&&file.isFile()&&System.currentTimeMillis()-file.lastModified()<ttl;
            if(cached){try{computedAt=file.lastModified();bytes=Files.readAllBytes(file.toPath());}catch(IOException e){bytes=null;cached=false;}} // arquivo podado/sumido: baixa normalmente
            if(bytes==null){
                try{if(force)throw new IOException("forcar-offline");if(route||geocode)pace();bytes=(route||geocode)?download(url,limit,ROUTE_CONNECT_MS,ROUTE_READ_MS):download(url,limit);if(unzip)bytes=gunzipIfNeeded(bytes,limit);if(isTile)bytes=tintPng(bytes,tz<12);computedAt=System.currentTimeMillis();
                    try{save(file,bytes);if(file.isFile())computedAt=file.lastModified();pruneAsync(cache);}catch(IOException|RuntimeException ignored){} // falha de disco nao derruba resposta ja baixada
                }catch(IOException e){
                    if(force||!file.isFile()){
                        if(vz>=0){WebResourceResponse local=offlineVectorTile(vz,vx,vy);if(local!=null)return local;}
                        // Internet falhou e nao ha copia em cache: roteador/busca locais (nunca gravados no cache de disco).
                        byte[] off=route?offlineRoute(uri.getQueryParameter("points"),RouteCoordinates.parseBearing(uri.getQueryParameter("bearing"))):geocode?offlineGeocode(uri.getQueryParameter("q"),uri.getQueryParameter("lat"),uri.getQueryParameter("lon")):null;
                        if(off==null){if(force&&file.isFile()){computedAt=file.lastModified();bytes=Files.readAllBytes(file.toPath());cached=true;}else throw e;}else{
                        bytes=off;computedAt=System.currentTimeMillis();viaOffline=true;}
                    }else{computedAt=file.lastModified();bytes=Files.readAllBytes(file.toPath());cached=true;}
                }
            }
            if(route){JSONObject json=new JSONObject(new String(bytes,StandardCharsets.UTF_8));json.put("cached",cached);json.put("computedAt",computedAt);bytes=json.toString().getBytes(StandardCharsets.UTF_8);}
            if(geocode&&!viaOffline)bytes=normalizeGeocode(new String(bytes,StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8);
            return new WebResourceResponse(mime,"UTF-8",200,"OK",Map.of("Cache-Control","private, max-age="+(ttl/1000)),new ByteArrayInputStream(bytes));
        }catch(IllegalArgumentException e){return error(400);}catch(Exception e){return error(503);}
    }
    /** Rota local (GraphHopper) quando a Internet falha; null se indisponivel ou sem rota. points ja foi validado por routeUrl. */
    private byte[] offlineRoute(String points,Integer bearing){
        try{
            if(!offlineRouter.available())return null;
            String[] p=RouteCoordinates.toProviderPath(points).split("[,;]");
            String json=offlineRouter.routeJson(Double.parseDouble(p[1]),Double.parseDouble(p[0]),Double.parseDouble(p[3]),Double.parseDouble(p[2]),bearing==null?null:Double.valueOf(bearing));
            return json.getBytes(StandardCharsets.UTF_8);
        }catch(IOException|RuntimeException e){Log.w("HarumiRoute","rota offline indisponivel: "+e);return null;}
    }
    /** Busca local quando a Internet falha; ja no formato normalizado [{name,lat,lon}]. null se indisponivel. */
    private byte[] offlineGeocode(String q,String lat,String lon){
        try{
            String json=offlineSearch.searchJson(validateQuery(q),parseCoord(lat,-35,6),parseCoord(lon,-75,-30),5);
            return json==null?null:json.getBytes(StandardCharsets.UTF_8);
        }catch(RuntimeException e){Log.w("HarumiRoute","busca offline indisponivel: "+e);return null;}
    }
    /** MBTiles local, usado quando a Internet falha e nao ha copia em cache (sem gravar no cache de disco). Achou: serve. Nao achou mas dentro dos bounds: tile vazio legitimo (200, corpo vazio), sem Internet. Fora dos bounds, erro ou sem arquivo: null -> online. */
    private WebResourceResponse offlineVectorTile(int z,int x,int y){
        try{
            OfflineTiles.Lookup l=offline.lookup(z,x,y);
            if(l.data!=null)return vtResponse(gunzipIfNeeded(l.data,2*1024*1024));
            if(!l.failed&&offline.coversMissing(z,x,y))return vtResponse(new byte[0]);
        }catch(IOException|RuntimeException e){Log.w("HarumiMap","offline tile "+z+"/"+x+"/"+y+" invalido, usando Internet: "+e);}
        return null;
    }
    private static WebResourceResponse vtResponse(byte[] bytes){return new WebResourceResponse("application/x-protobuf","UTF-8",200,"OK",Map.of("Cache-Control","private, max-age=86400"),new ByteArrayInputStream(bytes));}
    static final int MAX_QUERY=120;
    static final String OFM_HOST="https://tiles.openfreemap.org/",OFM_TILEJSON=OFM_HOST+"planet";
    /** Modelo de URL de tiles vetoriais (TileJSON do OpenFreeMap, cache de 1 dia; se a rede falhar, usa o arquivo antigo). */
    private String openFreeMapTemplate()throws IOException{
        File f=new File(cache,hex(sha256(OFM_TILEJSON)));
        if(f.isFile()&&System.currentTimeMillis()-f.lastModified()<DAY){try{return parseTileTemplate(new String(Files.readAllBytes(f.toPath()),StandardCharsets.UTF_8));}catch(IOException ignored){}}
        try{
            byte[] b=gunzipIfNeeded(download(OFM_TILEJSON,256*1024),256*1024);String tpl=parseTileTemplate(new String(b,StandardCharsets.UTF_8));
            try{save(f,b);}catch(IOException|RuntimeException ignored){}
            return tpl;
        }catch(IOException e){
            if(!f.isFile())throw e;
            return parseTileTemplate(new String(Files.readAllBytes(f.toPath()),StandardCharsets.UTF_8));
        }
    }
    /** Extrai tiles[0] do TileJSON e so aceita https://tiles.openfreemap.org/...{z}/{x}/{y}.pbf; IOException se invalido. */
    static String parseTileTemplate(String tileJson)throws IOException{
        Object root=new MiniJson(tileJson).parseRoot();
        if(!(root instanceof Map))throw new IOException("Unexpected TileJSON");
        Object tiles=((Map<?,?>)root).get("tiles");
        if(!(tiles instanceof List)||((List<?>)tiles).isEmpty()||!(((List<?>)tiles).get(0) instanceof String))throw new IOException("TileJSON without tiles");
        String t=(String)((List<?>)tiles).get(0);
        if(t.length()>300||!t.matches("https://tiles\\.openfreemap\\.org/[A-Za-z0-9_./-]+/\\{z\\}/\\{x\\}/\\{y\\}\\.pbf")||t.contains(".."))throw new IOException("Untrusted tile template");
        return t;
    }
    /** URL final do tile vetorial; z 0..14 e x/y dentro da grade, senao IllegalArgumentException. */
    static String vectorTileUrl(String template,int z,int x,int y){
        if(template==null||z<0||z>14||x<0||y<0||x>=(1<<z)||y>=(1<<z))throw new IllegalArgumentException("Invalid tile");
        return template.replace("{z}",Integer.toString(z)).replace("{x}",Integer.toString(x)).replace("{y}",Integer.toString(y));
    }
    /** URL dos glifos (fontes do mapa): fontstack so com letras, espaco e virgula; range no formato 0-255. */
    static String glyphsUrl(String fontstack,String range){
        if(fontstack==null||!fontstack.matches("[A-Za-z][A-Za-z ,]{0,79}")||range==null||!range.matches("\\d{1,6}-\\d{1,6}"))throw new IllegalArgumentException("Invalid glyphs");
        return OFM_HOST+"fonts/"+urlEncode(fontstack).replace("+","%20")+"/"+range+".pbf";
    }
    /** O WebView nao decodifica gzip sem Content-Encoding: se o servidor mandou gzip (1f 8b), descomprime respeitando o limite. */
    static byte[] gunzipIfNeeded(byte[] data,int limit)throws IOException{
        if(data.length<2||(data[0]&255)!=0x1f||(data[1]&255)!=0x8b)return data;
        try(java.util.zip.GZIPInputStream in=new java.util.zip.GZIPInputStream(new ByteArrayInputStream(data));ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] chunk=new byte[16384];int n,total=0;while((n=in.read(chunk))!=-1){total+=n;if(total>limit)throw new IOException("Response too large");out.write(chunk,0,n);}return out.toByteArray();
        }
    }
    private static byte[] sha256(String v){try{return MessageDigest.getInstance("SHA-256").digest(v.getBytes(StandardCharsets.UTF_8));}catch(java.security.NoSuchAlgorithmException e){throw new IllegalStateException(e);}}
    /** Valida e devolve a consulta de geocodificacao (aparada); IllegalArgumentException se invalida. */
    static String validateQuery(String q){
        if(q==null)throw new IllegalArgumentException("Missing q");
        String t=q.trim();if(t.isEmpty()||t.length()>MAX_QUERY)throw new IllegalArgumentException("Invalid q length");
        if(t.toLowerCase(Locale.ROOT).contains("http"))throw new IllegalArgumentException("URL not allowed");
        for(int i=0;i<t.length();i++)if(Character.isISOControl(t.charAt(i)))throw new IllegalArgumentException("Control character");
        return t;
    }
    static String routeUrl(String points,Integer bearing){
        String url="https://router.project-osrm.org/route/v1/driving/"+RouteCoordinates.toProviderPath(points)+"?steps=true&overview=full&geometries=geojson&alternatives=false";
        if(bearing!=null)url+="&bearings="+bearing+",45;";
        return url;
    }
    static String geocodeUrl(String q,String lat,String lon){
        String t=validateQuery(q);
        String url="https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=br&limit=5&q="+urlEncode(t);
        Double la=parseCoord(lat,-35,6),lo=parseCoord(lon,-75,-30);
        if(la!=null&&lo!=null)url+=String.format(Locale.ROOT,"&viewbox=%.4f,%.4f,%.4f,%.4f&bounded=0",lo-0.5,la+0.5,lo+0.5,la-0.5);
        return url;
    }
    private static String urlEncode(String v){try{return URLEncoder.encode(v,"UTF-8");}catch(UnsupportedEncodingException e){throw new IllegalStateException(e);}}
    private static Double parseCoord(String v,double min,double max){
        if(v==null||v.length()>20||!v.matches("-?[0-9]+(\\.[0-9]+)?"))return null;
        double d=Double.parseDouble(v);return d>=min&&d<=max?d:null;
    }
    /** Converte a resposta do Nominatim em [{"name":..,"lat":..,"lon":..}]. */
    static String normalizeGeocode(String json)throws IOException{
        Object root=new MiniJson(json).parseRoot();
        if(!(root instanceof List))throw new IOException("Unexpected geocode response");
        StringBuilder out=new StringBuilder("[");boolean first=true;
        for(Object o:(List<?>)root){
            if(!(o instanceof Map))continue;
            Map<?,?> m=(Map<?,?>)o;
            Object dn=m.get("display_name"),la=m.get("lat"),lo=m.get("lon");
            if(!(dn instanceof String)||la==null||lo==null)continue;
            double lat,lon;
            try{lat=Double.parseDouble(la.toString());lon=Double.parseDouble(lo.toString());}catch(NumberFormatException e){continue;}
            if(!Double.isFinite(lat)||!Double.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)continue;
            String name=((String)dn).trim();if(name.isEmpty())continue;
            if(name.length()>MAX_QUERY){int end=MAX_QUERY;if(Character.isHighSurrogate(name.charAt(end-1)))end--;name=name.substring(0,end);}
            if(!first)out.append(',');first=false;
            out.append("{\"name\":\"").append(escape(name)).append("\",\"lat\":").append(num(lat)).append(",\"lon\":").append(num(lon)).append('}');
        }
        return out.append(']').toString();
    }
    private static String num(double d){return new java.math.BigDecimal(d).setScale(6,java.math.RoundingMode.HALF_UP).stripTrailingZeros().toPlainString();}
    private static String escape(String s){
        StringBuilder b=new StringBuilder();
        for(int i=0;i<s.length();i++){char c=s.charAt(i);
            if(c=='"'||c=='\\')b.append('\\').append(c);else if(c<0x20)b.append(String.format(Locale.ROOT,"\\u%04x",(int)c));else b.append(c);}
        return b.toString();
    }
    /** Parser JSON minimo (JVM puro; org.json e stub nos testes unitarios). Objetos -> Map, arrays -> List. */
    private static final class MiniJson{
        private final String s;private int i;
        MiniJson(String s){this.s=s==null?"":s;}
        Object parseRoot()throws IOException{Object v=value(0);ws();if(i!=s.length())throw bad();return v;}
        private IOException bad(){return new IOException("Invalid JSON");}
        private void ws(){while(i<s.length()&&Character.isWhitespace(s.charAt(i)))i++;}
        private Object value(int depth)throws IOException{
            if(depth>8)throw bad();ws();if(i>=s.length())throw bad();char c=s.charAt(i);
            if(c=='{'){i++;Map<String,Object> m=new HashMap<>();ws();if(peek('}')){i++;return m;}
                while(true){ws();if(!peek('"'))throw bad();String k=string();ws();if(!peek(':'))throw bad();i++;m.put(k,value(depth+1));ws();
                    if(peek(',')){i++;continue;}if(peek('}')){i++;return m;}throw bad();}}
            if(c=='['){i++;List<Object> l=new ArrayList<>();ws();if(peek(']')){i++;return l;}
                while(true){l.add(value(depth+1));ws();if(peek(',')){i++;continue;}if(peek(']')){i++;return l;}throw bad();}}
            if(c=='"')return string();
            int st=i;while(i<s.length()&&",]} \t\r\n".indexOf(s.charAt(i))<0)i++;
            String tok=s.substring(st,i);
            if(tok.equals("true"))return Boolean.TRUE;if(tok.equals("false"))return Boolean.FALSE;if(tok.equals("null"))return null;
            try{return Double.valueOf(tok);}catch(NumberFormatException e){throw bad();}
        }
        private boolean peek(char c){return i<s.length()&&s.charAt(i)==c;}
        private String string()throws IOException{
            i++;StringBuilder b=new StringBuilder();
            while(i<s.length()){char c=s.charAt(i++);
                if(c=='"')return b.toString();
                if(c!='\\'){b.append(c);continue;}
                if(i>=s.length())throw bad();char e=s.charAt(i++);
                switch(e){case 'n':b.append('\n');break;case 't':b.append('\t');break;case 'r':b.append('\r');break;case 'b':b.append('\b');break;case 'f':b.append('\f');break;
                    case 'u':if(i+4>s.length())throw bad();try{b.append((char)Integer.parseInt(s.substring(i,i+4),16));}catch(NumberFormatException x){throw bad();}i+=4;break;
                    default:b.append(e);}}
            throw bad();
        }
    }
    /** Recolore o PNG uma vez antes do cache; se nao decodificar, devolve o original. */
    private byte[] tintPng(byte[] png,boolean far){
        try{long t0=System.nanoTime();Bitmap src=BitmapFactory.decodeByteArray(png,0,png.length);if(src==null)return png;
            int w=src.getWidth(),h=src.getHeight();int[] px=new int[w*h];src.getPixels(px,0,w,0,0,w,h);src.recycle();
            Bitmap dst=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);dst.setPixels(TileTint.tint(px,far),0,w,0,0,w,h);
            ByteArrayOutputStream out=new ByteArrayOutputStream();boolean ok=dst.compress(Bitmap.CompressFormat.PNG,100,out);dst.recycle();
            Log.d("HarumiMap","tint "+w+"x"+h+" "+(System.nanoTime()-t0)/1000000+"ms");
            return ok?out.toByteArray():png;
        }catch(RuntimeException|OutOfMemoryError e){return png;}
    }
    static final int ROUTE_CONNECT_MS=2500,ROUTE_READ_MS=4000; // rota e busca: no maximo ~6,5 s antes de cair para o roteador local
    private byte[] download(String url,int limit)throws IOException{return download(url,limit,8000,16000);}
    private byte[] download(String url,int limit,int connectMs,int readMs)throws IOException{
        HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();c.setConnectTimeout(connectMs);c.setReadTimeout(readMs);c.setInstanceFollowRedirects(false);
        c.setRequestProperty("User-Agent",userAgent);
        try{if(c.getResponseCode()!=200)throw new IOException("Map provider unavailable");
            try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
                byte[] chunk=new byte[16384];int n,total=0;while((n=in.read(chunk))!=-1){total+=n;if(total>limit)throw new IOException("Response too large");out.write(chunk,0,n);}return out.toByteArray();
            }
        }finally{c.disconnect();}
    }
    private static void save(File file,byte[] bytes)throws IOException{
        File temp=File.createTempFile("map-",".tmp",file.getParentFile());try{Files.write(temp.toPath(),bytes);Files.move(temp.toPath(),file.toPath(),java.nio.file.StandardCopyOption.REPLACE_EXISTING);}finally{temp.delete();}
    }
    private static final Object PRUNE_LOCK=new Object();
    private static boolean pruning;
    private static void pruneAsync(File cache){synchronized(PRUNE_LOCK){if(pruning)return;pruning=true;}Thread t=new Thread(()->{try{prune(cache);}catch(RuntimeException ignored){}finally{synchronized(PRUNE_LOCK){pruning=false;}}},"map-cache-prune");t.setDaemon(true);t.start();}
    private static void prune(File cache){synchronized(PRUNE_LOCK){prune0(cache);}}
    private static void prune0(File cache){File[] files=cache.listFiles(f->!f.getName().endsWith(".tmp"));if(files==null)return;long total=0;for(File f:files)total+=f.length();if(total<64*1024*1024)return;Arrays.sort(files,Comparator.comparingLong(File::lastModified));for(File f:files){long size=f.length();if(f.delete())total-=size;if(total<48*1024*1024)break;}}
    private static String hex(byte[] value){StringBuilder s=new StringBuilder();for(byte b:value)s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();}
    private static WebResourceResponse error(int status){return new WebResourceResponse("application/json","UTF-8",status,status==400?"Bad Request":"Unavailable",Map.of("Cache-Control","no-store"),new ByteArrayInputStream("{\"code\":\"Unavailable\"}".getBytes(StandardCharsets.UTF_8)));}
}

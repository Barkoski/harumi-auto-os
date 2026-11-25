package com.harumi.autoos.oem;
import android.app.*;
import android.content.*;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.widget.Toast;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Apps remain independent Android packages. Only fixed catalog IDs can reach the store. */
public final class AppCatalogGateway {
    private final Activity activity;
    private final OemAppGateway apps;
    private final android.content.SharedPreferences prefs;
    private final java.util.concurrent.ConcurrentHashMap<String,String> launcherComponents=new java.util.concurrent.ConcurrentHashMap<>();
    private final Map<String,JSONObject> entries=new LinkedHashMap<>();
    public AppCatalogGateway(Activity activity,OemAppGateway apps){
        this.activity=activity;this.apps=apps;prefs=activity.getSharedPreferences("catalog_assignments_v1",Context.MODE_PRIVATE);
        try(java.io.InputStream input=activity.getAssets().open("apps-catalog.json");java.io.ByteArrayOutputStream output=new java.io.ByteArrayOutputStream()){
            byte[] buffer=new byte[8192];int n;while((n=input.read(buffer))!=-1)output.write(buffer,0,n);
            JSONArray list=new JSONObject(output.toString(StandardCharsets.UTF_8.name())).getJSONArray("apps");
            for(int i=0;i<list.length();i++){JSONObject e=list.getJSONObject(i);entries.put(e.getString("id"),e);}
        }catch(Exception e){android.util.Log.e("HarumiApps","Cannot load catalog",e);}
    }
    private ResolveInfo installed(JSONObject entry,List<ResolveInfo> list){
        JSONArray packages=entry.optJSONArray("packages");String assigned=prefs.getString(entry.optString("id"),null);
        for(ResolveInfo info:list){if(apps.component(info).flattenToString().equals(assigned))return info;
            if(packages!=null)for(int i=0;i<packages.length();i++)if(info.activityInfo.packageName.equals(packages.optString(i)))return info;}
        return null;
    }
    public JSONArray inventory(){
        JSONArray result=new JSONArray();List<ResolveInfo> list=apps.list();
        for(JSONObject entry:entries.values())try{
            ResolveInfo found=installed(entry,list);JSONObject state=new JSONObject();state.put("id",entry.getString("id"));state.put("installed",found!=null);
            state.put("label",found==null?"":found.loadLabel(activity.getPackageManager()).toString());
            state.put("status",found!=null?"Disponível neste Android":entry.has("store")?"Não instalado ou sem atividade disponível":"Selecione o app original da central");result.put(state);
        }catch(JSONException ignored){}
        return result;
    }
    public void open(String id){
        JSONObject entry=entries.get(id);if(entry==null)return;
        ResolveInfo found=installed(entry,apps.list());
        if(found!=null){if(!apps.open(apps.component(found).flattenToString()))toast("O aplicativo não está disponível.");return;}
        if(entry.has("store"))store(id);else assign(id);
    }
    public void store(String id){
        JSONObject entry=entries.get(id);if(entry==null||!entry.has("store"))return;
        String packageName=entry.optString("store");
        try{activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("market://details?id="+packageName)).setPackage("com.android.vending"));}
        catch(ActivityNotFoundException|SecurityException e){try{activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://play.google.com/store/apps/details?id="+packageName)));}catch(ActivityNotFoundException|SecurityException absent){toast("Play Store e navegador indisponíveis. Use a loja/interface original da central.");}}
    }
    public void assign(String id){
        JSONObject entry=entries.get(id);if(entry==null||!"oem".equals(entry.optString("group")))return;
        List<ResolveInfo> list=apps.list();if(list.isEmpty()){toast("Nenhum app original acessível neste Android. Use a interface de fábrica.");return;}
        String[] labels=new String[list.size()+1];for(int i=0;i<list.size();i++)labels[i]=list.get(i).loadLabel(activity.getPackageManager())+" ("+list.get(i).activityInfo.packageName+")";labels[list.size()]="Limpar associação";
        new AlertDialog.Builder(activity).setTitle("Associar: "+entry.optString("name")).setItems(labels,(d,which)->{if(which==list.size())prefs.edit().remove(id).apply();else prefs.edit().putString(id,apps.component(list.get(which)).flattenToString()).apply();toast("Associação atualizada. Abra o atalho para testar.");}).setNegativeButton("Cancelar",null).show();
    }
    public void all(){
        List<ResolveInfo> list=apps.list();if(list.isEmpty()){toast("Nenhum aplicativo acessível.");return;}
        String[] labels=new String[list.size()];for(int i=0;i<list.size();i++)labels[i]=list.get(i).loadLabel(activity.getPackageManager()).toString();
        new AlertDialog.Builder(activity).setTitle("Aplicativos deste Android").setItems(labels,(d,i)->apps.open(apps.component(list.get(i)).flattenToString())).setNegativeButton("Fechar",null).show();
    }
    public JSONArray launcherInventory(){
        JSONArray result=new JSONArray();
        for(ResolveInfo info:apps.list())try{
            String component=apps.component(info).flattenToString();byte[] hash=java.security.MessageDigest.getInstance("SHA-256").digest(component.getBytes(StandardCharsets.UTF_8));StringBuilder token=new StringBuilder("i");for(int i=0;i<12;i++)token.append(String.format(java.util.Locale.ROOT,"%02x",hash[i]&255));String id=token.toString();launcherComponents.put(id,component);
            JSONObject row=new JSONObject();row.put("id",id);row.put("name",info.loadLabel(activity.getPackageManager()).toString());row.put("icon","app-icons/"+id+".png");result.put(row);
        }catch(Exception ignored){}return result;
    }
    public void launchInstalled(String id){String component=launcherComponents.get(id);if(component!=null&&!apps.open(component))toast("O app não está mais disponível. Atualize a lista.");}
    private List<ResolveInfo> cachedList;private long cachedAt;
    private synchronized List<ResolveInfo> cachedList(){long now=android.os.SystemClock.elapsedRealtime();if(cachedList==null||now-cachedAt>5000){cachedList=apps.list();cachedAt=now;}return cachedList;}
    public byte[] icon(String id){
        ResolveInfo found=null;JSONObject entry=entries.get(id);List<ResolveInfo> list=cachedList();if(entry!=null)found=installed(entry,list);
        if(found==null){String component=launcherComponents.get(id);if(component!=null)for(ResolveInfo info:list)if(apps.component(info).flattenToString().equals(component)){found=info;break;}}
        if(found==null)return null;
        android.graphics.drawable.Drawable drawable=found.loadIcon(activity.getPackageManager());android.graphics.Bitmap bitmap=android.graphics.Bitmap.createBitmap(144,144,android.graphics.Bitmap.Config.ARGB_8888);android.graphics.Canvas canvas=new android.graphics.Canvas(bitmap);drawable.setBounds(0,0,144,144);drawable.draw(canvas);
        java.io.ByteArrayOutputStream output=new java.io.ByteArrayOutputStream();bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,output);bitmap.recycle();return output.toByteArray();
    }
    private void toast(String message){Toast.makeText(activity,message,Toast.LENGTH_LONG).show();}
}

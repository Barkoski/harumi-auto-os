package com.harumi.autoos.oem;
import android.app.Activity;
import android.os.Build;
import android.util.DisplayMetrics;
import android.webkit.WebView;
import android.content.pm.PackageInfo;
import org.json.JSONObject;
public final class DeviceProfileCollector {
    public static JSONObject collect(Activity a) {
        JSONObject j = new JSONObject();
        try {
            DisplayMetrics m = a.getResources().getDisplayMetrics();
            PackageInfo w = WebView.getCurrentWebViewPackage();
            j.put("Fabricante", Build.MANUFACTURER); j.put("Modelo", Build.MODEL);
            j.put("Android declarado", Build.VERSION.RELEASE); j.put("API", Build.VERSION.SDK_INT);
            j.put("Área do app", m.widthPixels + " × " + m.heightPixels + " px");
            j.put("Densidade", m.densityDpi + " dpi");
            j.put("WebView", w == null ? "Não identificada" : w.packageName + " " + w.versionName);
            j.put("Arquiteturas Android",android.text.TextUtils.join(", ",Build.SUPPORTED_ABIS));
            j.put("Processo 64 bits",android.os.Process.is64Bit());
            j.put("Compatibilidade Harumi",com.harumi.autoos.domain.CompatibilityPolicy.evaluate(Build.VERSION.SDK_INT,java.util.Arrays.asList(Build.SUPPORTED_ABIS),android.os.Process.is64Bit()));
            j.put("Placa declarada",Build.BOARD);j.put("Hardware declarado",Build.HARDWARE);j.put("Build declarado",Build.DISPLAY);
            if(Build.VERSION.SDK_INT>=31)j.put("SoC declarado",Build.SOC_MANUFACTURER+" / "+Build.SOC_MODEL);
            j.put("Identidade do hardware","Valores declarados pelo Android; não autenticam a especificação comercial.");
            android.app.ActivityManager.MemoryInfo mem=new android.app.ActivityManager.MemoryInfo();
            ((android.app.ActivityManager)a.getSystemService(android.content.Context.ACTIVITY_SERVICE)).getMemoryInfo(mem);
            j.put("RAM disponível",(mem.availMem/1024/1024)+" MB");
            j.put("RAM total declarada",(mem.totalMem/1024/1024)+" MB");
            j.put("Pouca memória sinalizada",mem.lowMemory);
            android.os.StatFs disk=new android.os.StatFs(a.getFilesDir().getAbsolutePath());
            j.put("Armazenamento livre",disk.getAvailableBytes()/1024/1024+" MB");
            j.put("Reserva para modelos",disk.getAvailableBytes()<3L*1024*1024*1024?"Atenção: menos de 3 GiB livres; conferir preparação dos modelos":"Acima da reserva de bancada de 3 GiB; não é benchmark de IA");
            j.put("Página de memória",android.system.Os.sysconf(android.system.OsConstants._SC_PAGESIZE)+" bytes; 16 KiB ainda não homologados");
            android.content.pm.PackageManager pm=a.getPackageManager();
            j.put("GPS declarado",pm.hasSystemFeature(android.content.pm.PackageManager.FEATURE_LOCATION_GPS));
            j.put("Bluetooth declarado",pm.hasSystemFeature(android.content.pm.PackageManager.FEATURE_BLUETOOTH));
            OemAppGateway gateway=new OemAppGateway(a);
            java.util.Set<String> seen=new java.util.HashSet<>();
            org.json.JSONArray inventory=new org.json.JSONArray(),nav=new org.json.JSONArray(),music=new org.json.JSONArray();
            for(android.content.pm.ResolveInfo i:gateway.list())if(seen.add(i.activityInfo.packageName)){
                JSONObject app=new JSONObject();app.put("nome",i.loadLabel(pm).toString());app.put("pacote",i.activityInfo.packageName);
                try{app.put("versao",pm.getPackageInfo(i.activityInfo.packageName,0).versionName);}catch(android.content.pm.PackageManager.NameNotFoundException ignored){}
                inventory.put(app);
            }
            for(android.content.pm.ResolveInfo i:gateway.listFor("NAV"))nav.put(i.loadLabel(pm).toString());
            for(android.content.pm.ResolveInfo i:gateway.listFor("MUSIC"))music.put(i.loadLabel(pm).toString());
            j.put("Apps com ícone detectados",inventory);j.put("Navegadores detectados",nav);j.put("Players detectados",music);
            j.put("Play Store presente",present(pm,"com.android.vending"));j.put("Play Services presente",present(pm,"com.google.android.gms"));
            j.put("Certificação Google","Presença dos pacotes não comprova certificação. Conferir Play Store > Configurações > Sobre.");
            j.put("MCU", "Não identificada"); j.put("Câmeras / áudio / ACC", "Homologação física pendente");
        } catch (Exception ignored) { }
        return j;
    }
    private static boolean present(android.content.pm.PackageManager pm,String name){
        try{pm.getPackageInfo(name,0);return true;}catch(android.content.pm.PackageManager.NameNotFoundException e){return false;}
    }
}

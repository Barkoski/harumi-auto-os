package com.harumi.autoos.navigation;
import android.app.*;
import android.content.*;
import android.net.Uri;
public final class NavigationGateway {
    private final Activity activity;
    public NavigationGateway(Activity a) { activity=a; }
    /** Algum app instalado aceita destino (geo: ou google.navigation:)? */
    public static boolean available(Context c) {
        android.content.pm.PackageManager pm=c.getPackageManager();
        return new Intent(Intent.ACTION_VIEW,Uri.parse("geo:0,0?q=Londrina")).resolveActivity(pm)!=null
            || new Intent(Intent.ACTION_VIEW,Uri.parse("google.navigation:q=Londrina")).resolveActivity(pm)!=null;
    }
    public void confirm(String destination) {
        new AlertDialog.Builder(activity).setTitle("Confirmar destino").setMessage("Abrir navegação para:\n\n"+destination+"\n\nConfira o local no aplicativo de mapas antes de iniciar o trajeto.")
            .setPositiveButton("Abrir mapas",(dialog,which)->open(destination)).setNegativeButton("Cancelar",null).show();
    }
    private void open(String destination) {
        String q=Uri.encode(destination);
        Intent route=new Intent(Intent.ACTION_VIEW,Uri.parse("geo:0,0?q="+q));
        try {
            if(route.resolveActivity(activity.getPackageManager())!=null) activity.startActivity(Intent.createChooser(route,"Escolher aplicativo de mapas"));
            else {
                Intent fallback=new Intent(Intent.ACTION_VIEW,Uri.parse("google.navigation:q="+q));
                if (fallback.resolveActivity(activity.getPackageManager())==null) throw new ActivityNotFoundException();
                activity.startActivity(Intent.createChooser(fallback,"Escolher aplicativo de mapas"));
            }
        } catch(ActivityNotFoundException|SecurityException e) {
            new AlertDialog.Builder(activity).setMessage("Nenhum aplicativo de mapas compatível foi encontrado. Instale ou habilite seu navegador de mapas.").setPositiveButton("Entendi",null).show();
        }
    }
}

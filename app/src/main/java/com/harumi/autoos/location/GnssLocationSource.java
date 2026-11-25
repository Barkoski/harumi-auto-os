package com.harumi.autoos.location;
import android.content.Context;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Looper;
/**
 * GPS via LocationManager.GPS_PROVIDER. NAO ligada a UI nem ao manifest.
 * So sera ativada quando o kit confirmar o receptor GNSS da central e o Lucas
 * aprovar a permissao ACCESS_FINE_LOCATION.
 */
public final class GnssLocationSource implements LocationSource {
    private static final long MIN_TIME_MS=1000; // provisório
    private final LocationManager manager;
    private LocationListener active;
    public GnssLocationSource(Context context){manager=(LocationManager)context.getSystemService(Context.LOCATION_SERVICE);}
    // Permissão ainda não declarada de propósito; a falta dela é tratada no catch abaixo.
    @android.annotation.SuppressLint("MissingPermission")
    @Override public void start(Listener l){
        stop();
        try{
            if(manager==null||!manager.isProviderEnabled(LocationManager.GPS_PROVIDER)){l.onUnavailable("GPS indisponivel");return;}
            LocationListener ll=new LocationListener(){
                @Override public void onLocationChanged(Location x){l.onFix(toFix(x));}
                @Override public void onStatusChanged(String p,int s,Bundle e){}
                @Override public void onProviderEnabled(String p){}
                @Override public void onProviderDisabled(String p){l.onUnavailable("GPS desligado");}
            };
            manager.requestLocationUpdates(LocationManager.GPS_PROVIDER,MIN_TIME_MS,0f,ll,Looper.getMainLooper());
            active=ll;
        }catch(SecurityException e){l.onUnavailable("Permissao de localizacao ausente");}
    }
    @Override public void stop(){
        if(active!=null&&manager!=null)manager.removeUpdates(active);
        active=null;
    }
    static Fix toFix(Location x){
        Bundle ex=x.getExtras();
        Integer sats=ex!=null&&ex.containsKey("satellites")?ex.getInt("satellites"):null;
        return new Fix(x.getLatitude(),x.getLongitude(),
            x.hasAltitude()?x.getAltitude():null,
            x.hasSpeed()?(double)x.getSpeed():null,
            x.hasBearing()?(double)x.getBearing():null,
            x.hasAccuracy()?(double)x.getAccuracy():null,
            sats,x.getTime(),"GNSS");
    }
}

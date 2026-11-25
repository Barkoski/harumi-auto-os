package com.harumi.autoos.location;
import java.util.Locale;
import java.util.function.LongSupplier;
/** Liga uma LocationSource ao mapa: avalia cada Fix, limita a ~1 Hz e entrega JSON no contrato harumiNav.fix. Sem Android: testavel na JVM. */
public final class NavigationFeed {
    public interface Sink{void fix(String json);void unavailable(String reason);}
    static final long MIN_INTERVAL_MS=900; // 1 Hz com tolerancia a jitter
    private final LocationSource source;
    private final FixAssessor assessor;
    private final LongSupplier clock;
    private final Sink sink;
    private boolean running;
    private long lastEmit;
    private boolean emitted;
    public NavigationFeed(LocationSource source,LongSupplier clock,Sink sink){this.source=source;this.clock=clock;this.sink=sink;this.assessor=new FixAssessor(clock);}
    public boolean isRunning(){return running;}
    /** Primeiro centro (ultima posicao conhecida do GPS); ignorado se null. */
    public void seed(Fix last){if(last!=null)deliver(last);}
    public void start(){
        stop();running=true;emitted=false;
        source.start(new LocationSource.Listener(){
            @Override public void onFix(Fix f){if(running)deliver(f);}
            @Override public void onUnavailable(String reason){if(running)sink.unavailable(reason==null?"GPS indisponivel":reason);}
        });
    }
    public void stop(){running=false;source.stop();}
    private void deliver(Fix f){
        long now=clock.getAsLong();
        if(emitted&&now-lastEmit<MIN_INTERVAL_MS)return;
        emitted=true;lastEmit=now;
        sink.fix(toJson(f,assessor.assess(f)));
    }
    /** Ultima posicao conhecida do GPS (nunca rede/fused); null se nao houver ou sem permissao. Nao usado nos testes JVM. */
    @android.annotation.SuppressLint("MissingPermission")
    public static Fix lastKnown(android.content.Context context){
        try{
            android.location.LocationManager m=(android.location.LocationManager)context.getSystemService(android.content.Context.LOCATION_SERVICE);
            android.location.Location x=m==null?null:m.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
            return x==null?null:GnssLocationSource.toFix(x);
        }catch(RuntimeException e){return null;}
    }
    /** JSON {lat,lon,speedMps,bearing,accuracyM,quality,timeMs}; opcionais ausentes viram null. */
    public static String toJson(Fix f,FixQuality q){
        return "{\"lat\":"+num(f.lat())+",\"lon\":"+num(f.lon())+",\"speedMps\":"+num(f.speedMps())+",\"bearing\":"+num(f.bearing())+",\"accuracyM\":"+num(f.accuracyM())+",\"quality\":\""+(q==null?FixQuality.SEM_FIX:q).name()+"\",\"timeMs\":"+f.timeMs()+"}";
    }
    private static String num(Double d){return d==null||d.isNaN()||d.isInfinite()?"null":String.format(Locale.ROOT,"%s",d);}
}

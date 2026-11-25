package com.harumi.autoos.diagnostics;
import java.util.*;
import java.util.concurrent.*;
/** Read-only boundary. No Subaru protocol or OBD-II support is assumed. */
public final class DiagnosticMonitor implements AutoCloseable {
    public record Reading(double value,String unit) { }
    public record Snapshot(boolean connected,String source,long observedAtMs,Map<String,Reading> readings) {
        public Snapshot { readings=Collections.unmodifiableMap(new HashMap<>(readings)); }
    }
    public interface ReadOnlyAdapter { Snapshot readSnapshot() throws Exception; }
    private final ReadOnlyAdapter adapter;
    private volatile Snapshot latest=new Snapshot(false,"Nenhum adaptador validado",0,Collections.emptyMap());
    private ScheduledExecutorService poller;
    public DiagnosticMonitor() { this(()->new Snapshot(false,"Nenhum adaptador validado",0,Collections.emptyMap())); }
    public DiagnosticMonitor(ReadOnlyAdapter adapter) { this.adapter=Objects.requireNonNull(adapter); }
    public synchronized void start() {
        if(poller!=null)return;
        poller=Executors.newSingleThreadScheduledExecutor();
        poller.scheduleWithFixedDelay(()->{
            try { Snapshot result=adapter.readSnapshot();if(result!=null)latest=result; }
            catch(Exception e) { latest=new Snapshot(false,"Adaptador indisponível",0,Collections.emptyMap()); }
        },0,2,TimeUnit.SECONDS);
    }
    public String summary() {
        Snapshot s=latest;
        if(!s.connected()) return "Sem adaptador de diagnóstico conectado. Não tenho leituras reais de motor, temperatura, bateria ou falhas, então não consigo avaliar o carro agora.";
        long age=System.currentTimeMillis()-s.observedAtMs();
        if(age<0||age>5000) return "Os dados do adaptador estão desatualizados. Não consigo afirmar o estado atual do carro.";
        StringBuilder result=new StringBuilder("Leituras observadas, fonte: ").append(s.source()).append(". Idade: ").append(age).append(" ms. ");
        for(var e:s.readings().entrySet()) result.append(e.getKey()).append(": ").append(e.getValue().value()).append(" ").append(e.getValue().unit()).append("; ");
        return result.toString();
    }
    public String status() { return latest.connected()?"Diagnóstico: adaptador conectado; confira atualidade das leituras":"Diagnóstico: sem adaptador conectado"; }
    @Override public synchronized void close() { if(poller!=null) { poller.shutdownNow();poller=null; } }
}

package com.harumi.autoos.location;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.LongSupplier;
import java.util.function.Supplier;
/** Reproduz frases NMEA ou Fix (testes/emulador). Sem threads proprias: o agendador e injetado. */
public final class ReplayLocationSource implements LocationSource {
    public interface Scheduler{void schedule(Runnable task,long delayMs);}
    private final List<Supplier<Optional<Fix>>> items=new ArrayList<>();
    private final long intervalMs;
    private final Scheduler scheduler;
    private boolean running;
    private int generation;
    private ReplayLocationSource(long intervalMs,Scheduler scheduler){this.intervalMs=intervalMs;this.scheduler=scheduler;}
    public static ReplayLocationSource fromNmea(List<String> sentences,long intervalMs,LongSupplier clock,Scheduler scheduler){
        ReplayLocationSource r=new ReplayLocationSource(intervalMs,scheduler);
        NmeaParser p=new NmeaParser();
        for(String s:sentences)r.items.add(()->p.feed(s,clock.getAsLong()));
        return r;
    }
    public static ReplayLocationSource fromFixes(List<Fix> fixes,long intervalMs,Scheduler scheduler){
        ReplayLocationSource r=new ReplayLocationSource(intervalMs,scheduler);
        for(Fix f:fixes)r.items.add(()->Optional.of(f));
        return r;
    }
    @Override public void start(Listener l){
        stop();running=true;final int g=++generation;
        for(int i=0;i<items.size();i++){
            Supplier<Optional<Fix>> it=items.get(i);
            scheduler.schedule(()->{if(running&&g==generation)it.get().ifPresent(l::onFix);},i*intervalMs);
        }
    }
    @Override public void stop(){running=false;}
}

package com.harumi.autoos.diagnostics;
import org.junit.After;
import org.junit.Test;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Predicate;
import static org.junit.Assert.*;
/** DiagnosticMonitor usa apenas java.util.concurrent (sem Android), entao roda em JVM. */
public class DiagnosticMonitorTest {
    private final List<DiagnosticMonitor> monitors=new ArrayList<>();
    private DiagnosticMonitor track(DiagnosticMonitor m){monitors.add(m);return m;}
    @After public void closeAll(){for(DiagnosticMonitor m:monitors)m.close();}

    private static DiagnosticMonitor.Snapshot snap(long observedAtMs){
        return new DiagnosticMonitor.Snapshot(true,"Fonte teste",observedAtMs,Map.of("rpm",new DiagnosticMonitor.Reading(900.0,"rpm")));
    }
    private static void waitFor(DiagnosticMonitor m,Predicate<String> cond,long timeoutMs) throws InterruptedException{
        long end=System.currentTimeMillis()+timeoutMs;
        while(System.currentTimeMillis()<end){ if(cond.test(m.summary()))return; Thread.sleep(20); }
        fail("Timeout aguardando summary; ultimo: "+m.summary());
    }

    @Test public void defaultAdapterIsDisconnected() throws Exception{
        DiagnosticMonitor m=track(new DiagnosticMonitor());
        assertTrue(m.summary().startsWith("Sem adaptador"));
        assertEquals("Diagnóstico: sem adaptador conectado",m.status());
        m.start();
        Thread.sleep(150);
        assertTrue(m.summary().startsWith("Sem adaptador"));
    }
    @Test(expected=NullPointerException.class) public void nullAdapterRejected(){new DiagnosticMonitor(null);}

    @Test public void freshReadingIsReportedWithSourceAndValues() throws Exception{
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->snap(System.currentTimeMillis())));
        m.start();
        waitFor(m,s->s.startsWith("Leituras observadas"),3000);
        String s=m.summary();
        assertTrue(s,s.contains("Fonte teste"));
        assertTrue(s,s.contains("rpm: 900.0 rpm"));
        assertTrue(m.status().contains("conectado"));
    }
    @Test public void readingOlderThan5000msIsStale() throws Exception{
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->snap(System.currentTimeMillis()-6000)));
        m.start();
        waitFor(m,s->s.startsWith("Os dados do adaptador estão desatualizados"),3000);
    }
    @Test public void readingWithFutureTimestampIsStale() throws Exception{
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->snap(System.currentTimeMillis()+60000)));
        m.start();
        waitFor(m,s->s.startsWith("Os dados do adaptador estão desatualizados"),3000);
    }
    @Test public void connectedFalseSnapshotIsDisconnectedEvenIfRecent() throws Exception{
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->new DiagnosticMonitor.Snapshot(false,"x",System.currentTimeMillis(),Map.of())));
        m.start();
        Thread.sleep(150);
        assertTrue(m.summary().startsWith("Sem adaptador"));
    }
    @Test public void nullSnapshotKeepsPreviousState() throws Exception{
        AtomicInteger calls=new AtomicInteger();
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->{calls.incrementAndGet();return null;}));
        m.start();
        Thread.sleep(150);
        assertTrue(calls.get()>=1);
        assertTrue(m.summary().startsWith("Sem adaptador"));
    }
    /** Primeira leitura valida; segunda (apos ~2 s) lanca excecao e deve derrubar o estado para "Sem adaptador". */
    @Test public void adapterThrowingAfterGoodReadDropsToDisconnected() throws Exception{
        AtomicInteger calls=new AtomicInteger();
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->{
            if(calls.getAndIncrement()==0)return snap(System.currentTimeMillis());
            throw new IllegalStateException("adaptador fora");
        }));
        m.start();
        waitFor(m,s->s.startsWith("Leituras observadas"),3000);
        waitFor(m,s->s.startsWith("Sem adaptador"),6000);
        assertEquals("Diagnóstico: sem adaptador conectado",m.status());
        assertFalse(m.summary().contains("rpm"));
    }
    @Test public void adapterThrowingFromStartIsDisconnected() throws Exception{
        AtomicInteger calls=new AtomicInteger();
        DiagnosticMonitor m=track(new DiagnosticMonitor(()->{calls.incrementAndGet();throw new Exception("indisponivel");}));
        m.start();
        Thread.sleep(200);
        assertTrue(calls.get()>=1);
        assertTrue(m.summary().startsWith("Sem adaptador"));
    }
    @Test public void startAndCloseCanBeRepeated(){
        DiagnosticMonitor m=track(new DiagnosticMonitor());
        m.close(); // sem start
        m.start();m.start();
        m.close();m.close();
        m.start(); // reinicia apos close
        m.close();
    }
    @Test public void snapshotReadingsAreImmutableCopy(){
        Map<String,DiagnosticMonitor.Reading> src=new HashMap<>();
        src.put("a",new DiagnosticMonitor.Reading(1,"u"));
        DiagnosticMonitor.Snapshot s=new DiagnosticMonitor.Snapshot(true,"f",0,src);
        src.put("b",new DiagnosticMonitor.Reading(2,"u"));
        assertEquals(1,s.readings().size());
        try{s.readings().put("c",new DiagnosticMonitor.Reading(3,"u"));fail();}catch(UnsupportedOperationException expected){}
    }
}

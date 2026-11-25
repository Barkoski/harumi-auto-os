package com.harumi.autoos.location;
import static org.junit.Assert.*;
import java.util.ArrayList;
import java.util.List;
import org.junit.Test;
public class NavigationFeedTest {
    static class Fake implements LocationSource {
        Listener l;boolean stopped;
        public void start(Listener x){l=x;stopped=false;}
        public void stop(){stopped=true;}
    }
    static class Out implements NavigationFeed.Sink {
        final List<String> fixes=new ArrayList<>(),reasons=new ArrayList<>();
        public void fix(String j){fixes.add(j);}
        public void unavailable(String r){reasons.add(r);}
    }
    private static Fix fix(long t){return new Fix(-23.31,-51.16,null,10.5,90.0,5.0,8,t,"T");}
    @Test public void jsonFormat(){
        assertEquals("{\"lat\":-23.31,\"lon\":-51.16,\"speedMps\":10.5,\"bearing\":90.0,\"accuracyM\":5.0,\"quality\":\"OK\",\"timeMs\":1000}",NavigationFeed.toJson(fix(1000),FixQuality.OK));
    }
    @Test public void jsonNullsAndQuality(){
        Fix f=new Fix(1,2,null,null,Double.NaN,null,null,7,"T");
        assertEquals("{\"lat\":1.0,\"lon\":2.0,\"speedMps\":null,\"bearing\":null,\"accuracyM\":null,\"quality\":\"VELHO\",\"timeMs\":7}",NavigationFeed.toJson(f,FixQuality.VELHO));
        assertTrue(NavigationFeed.toJson(f,null).contains("\"quality\":\"SEM_FIX\""));
    }
    @Test public void limitsToOneHzAndAssesses(){
        long[] now={10_000};Fake src=new Fake();Out out=new Out();
        NavigationFeed feed=new NavigationFeed(src,()->now[0],out);
        feed.start();
        src.l.onFix(fix(10_000));now[0]=10_300;src.l.onFix(fix(10_300));now[0]=10_400;src.l.onFix(fix(10_400));
        assertEquals(1,out.fixes.size());
        now[0]=11_000;src.l.onFix(fix(11_000));
        assertEquals(2,out.fixes.size());
        now[0]=20_000;src.l.onFix(fix(11_000));
        assertEquals(3,out.fixes.size());
        assertTrue(out.fixes.get(2).contains("\"quality\":\"VELHO\""));
    }
    @Test public void stopSilencesAndUnavailableForwarded(){
        long[] now={0};Fake src=new Fake();Out out=new Out();
        NavigationFeed feed=new NavigationFeed(src,()->now[0],out);
        feed.start();src.l.onUnavailable("GPS desligado");
        assertEquals(1,out.reasons.size());
        feed.stop();assertTrue(src.stopped);assertFalse(feed.isRunning());
        src.l.onFix(fix(0));src.l.onUnavailable("x");
        assertTrue(out.fixes.isEmpty());assertEquals(1,out.reasons.size());
    }
    @Test public void seedDelivers(){
        Fake src=new Fake();Out out=new Out();
        new NavigationFeed(src,()->1000L,out).seed(fix(1000));
        assertEquals(1,out.fixes.size());
    }
}

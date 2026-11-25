package com.harumi.autoos.location;
import static org.junit.Assert.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;
public class LocationBaseTest {
    static final String GGA="$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47";
    static final String RMC="$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A";
    static final String GGA_BR="$GNGGA,140000.00,2318.600,S,05109.600,W,1,09,1.1,585.0,M,-4.0,M,,*65";
    static final String RMC_BR="$GNRMC,140000.00,A,2318.600,S,05109.600,W,10.00,90.0,031126,,,A*70";
    static final String RMC_V="$GNRMC,140000.00,V,,,,,,,031126,,,N*61";
    static final String GGA_NOFIX="$GPGGA,140000,,,,,0,00,99.9,,M,,M,,*74";
    private static Fix fix(Double speed,Double acc,Integer sats,long t){return new Fix(-23.31,-51.16,null,speed,null,acc,sats,t,"T");}

    @Test public void parsesGgaAndRmcCombined(){
        NmeaParser p=new NmeaParser();
        Fix a=p.feed(GGA,1000).get();
        assertEquals(48.1173,a.lat(),1e-6);
        assertEquals(11.516667,a.lon(),1e-6);
        assertEquals(545.4,a.altitude(),1e-9);
        assertEquals(8,(int)a.satellites());
        assertNull(a.speedMps());
        Fix b=p.feed(RMC,2000).get();
        assertEquals(22.4*0.514444,b.speedMps(),1e-6);
        assertEquals(84.4,b.bearing(),1e-9);
        assertEquals(545.4,b.altitude(),1e-9);
        assertEquals(2000,b.timeMs());
    }
    @Test public void southWestAreNegative(){
        NmeaParser p=new NmeaParser();
        p.feed(GGA_BR,0);
        Fix f=p.feed(RMC_BR,0).get();
        assertEquals(-23.31,f.lat(),1e-6);
        assertEquals(-51.16,f.lon(),1e-6);
        assertEquals(5.14444,f.speedMps(),1e-5);
    }
    @Test public void badChecksumRejected(){
        assertFalse(new NmeaParser().feed(GGA.replace("*47","*48"),0).isPresent());
        assertFalse(new NmeaParser().feed(GGA.replace("545.4","545.5"),0).isPresent());
    }
    @Test public void invalidSentencesRejected(){
        NmeaParser p=new NmeaParser();
        assertFalse(p.feed(null,0).isPresent());
        assertFalse(p.feed("",0).isPresent());
        assertFalse(p.feed("lixo",0).isPresent());
        assertFalse(p.feed("$GPGGA,sem,checksum",0).isPresent());
        assertFalse(p.feed(GGA_NOFIX,0).isPresent());
    }
    @Test public void rmcVoidGivesNoPosition(){
        assertFalse(new NmeaParser().feed(RMC_V,0).isPresent());
    }
    @Test public void assessorQuality(){
        long[] now={10_000};
        FixAssessor a=new FixAssessor(()->now[0]);
        assertEquals(FixQuality.SEM_FIX,a.assess(null));
        assertEquals(FixQuality.OK,a.assess(fix(null,5.0,8,10_000)));
        assertEquals(FixQuality.OK,a.assess(fix(null,null,null,5_000)));
        assertEquals(FixQuality.VELHO,a.assess(fix(null,5.0,8,4_999)));
        assertEquals(FixQuality.FRACO,a.assess(fix(null,30.1,8,10_000)));
        assertEquals(FixQuality.FRACO,a.assess(fix(null,5.0,3,10_000)));
        assertEquals(FixQuality.OK,a.assess(fix(null,30.0,4,10_000)));
        now[0]=20_000;
        assertEquals(FixQuality.VELHO,a.assess(fix(null,5.0,8,10_000)));
    }
    @Test public void speedHysteresis(){
        SpeedPolicy s=new SpeedPolicy();
        double ms=1/3.6;
        assertFalse(s.isMovingAbove(fix(9.0*ms,null,null,0),10));
        assertFalse(s.isMovingAbove(fix(9.9*ms,null,null,0),10));
        assertTrue(s.isMovingAbove(fix(11.0*ms,null,null,0),10));
        assertTrue(s.isMovingAbove(fix(8.0*ms,null,null,0),10));   // dentro da histerese
        assertTrue(s.isMovingAbove(fix(null,null,null,0),10));     // sem velocidade mantem
        assertTrue(s.isMovingAbove(null,10));
        assertFalse(s.isMovingAbove(fix(6.0*ms,null,null,0),10));  // abaixo de 7
        assertFalse(s.isMovingAbove(fix(9.0*ms,null,null,0),10));
    }
    static class Manual implements ReplayLocationSource.Scheduler {
        final List<Runnable> tasks=new ArrayList<>();final List<Long> delays=new ArrayList<>();
        public void schedule(Runnable r,long d){tasks.add(r);delays.add(d);}
        void runAll(){for(Runnable r:new ArrayList<>(tasks))r.run();}
    }
    static class Collect implements LocationSource.Listener {
        final List<Fix> fixes=new ArrayList<>();
        public void onFix(Fix f){fixes.add(f);}
        public void onUnavailable(String r){}
    }
    @Test public void replayNmeaEmitsInOrder(){
        Manual m=new Manual();Collect c=new Collect();
        ReplayLocationSource r=ReplayLocationSource.fromNmea(Arrays.asList("lixo",GGA_BR,RMC_BR),500,()->42L,m);
        r.start(c);
        assertEquals(Arrays.asList(0L,500L,1000L),m.delays);
        m.runAll();
        assertEquals(2,c.fixes.size());
        assertNull(c.fixes.get(0).speedMps());
        assertNotNull(c.fixes.get(1).speedMps());
        assertEquals(42L,c.fixes.get(1).timeMs());
    }
    @Test public void replayFixesAndStop(){
        Manual m=new Manual();Collect c=new Collect();
        Fix f1=fix(1.0,1.0,5,1),f2=fix(2.0,1.0,5,2);
        ReplayLocationSource r=ReplayLocationSource.fromFixes(Arrays.asList(f1,f2),100,m);
        r.start(c);
        m.tasks.get(0).run();
        r.stop();
        m.tasks.get(1).run();
        assertEquals(Arrays.asList(f1),c.fixes);
    }
}

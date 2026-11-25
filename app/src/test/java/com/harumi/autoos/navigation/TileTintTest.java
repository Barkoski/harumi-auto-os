package com.harumi.autoos.navigation;
import org.junit.Test;
import static org.junit.Assert.*;
public class TileTintTest {
    private static int one(int argb,boolean far){return TileTint.tint(new int[]{argb},far)[0];}
    private static void near(int expectedRgb,int actual){for(int s=16;s>=0;s-=8)assertTrue(Integer.toHexString(actual),Math.abs(((expectedRgb>>s)&255)-((actual>>s)&255))<=12);}
    @Test public void landBecomesDarkLand(){near(0x26222b,one(0xfff2efe9,false));}
    @Test public void whiteRoadBecomesRoad(){near(0x6b5c6e,one(0xffffffff,false));}
    @Test public void waterBecomesWater(){near(0x232a33,one(0xffaad3df,false));}
    @Test public void blackBecomesLabel(){near(0xb9a6b8,one(0xff000000,false));}
    @Test public void greenBuildingAndMajorRoad(){near(0x2a2d2b,one(0xffc8facc,false));near(0x2a2d2b,one(0xffadd19e,false));near(0x2d2831,one(0xffd9d0c9,false));near(0x8a7589,one(0xfff7fabf,false));near(0x8a7589,one(0xfffcd6a4,false));near(0x8a7589,one(0xffe892a2,false));}
    @Test public void alphaIsPreserved(){assertEquals(0x80,one(0x80ffffff,false)>>>24);assertEquals(0,one(0x00000000,true)>>>24);}
    @Test public void farReducesContrast(){int near=one(0xffffffff,false),far=one(0xffffffff,true),land=0x26222b;assertTrue(Math.abs(((far>>16)&255)-((land>>16)&255))<Math.abs(((near>>16)&255)-((land>>16)&255)));}
}

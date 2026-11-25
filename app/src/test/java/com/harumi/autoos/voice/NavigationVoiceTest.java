package com.harumi.autoos.voice;
import static org.junit.Assert.*;
import java.nio.file.*;
import org.junit.Test;
public class NavigationVoiceTest {
    @Test public void acceptsOnlyWhitelistedCodes() {
        for(String c:new String[]{"d100","d200","d500","d1k","now","left","right","slight_left","slight_right","sharp_left","sharp_right","straight","uturn","keep_left","keep_right","roundabout_1","roundabout_5","arrive","recalc","nav_start"})assertTrue(c,NavigationVoice.validCode(c));
        for(String c:new String[]{null,"","LEFT","roundabout_0","roundabout_6","../left","left ","d300","nav_left"})assertFalse(String.valueOf(c),NavigationVoice.validCode(c));
        assertEquals(23,NavigationVoice.codes().size()); // 5 distancias + 10 manobras + 5 rotatorias + arrive, recalc, nav_start
    }
    @Test public void mapsCodesToPrefixedClipIds() {
        assertEquals("nav_d200",NavigationVoice.clipId("d200"));assertEquals("nav_roundabout_3",NavigationVoice.clipId("roundabout_3"));
        assertEquals("nav_start",NavigationVoice.clipId("nav_start"));assertNull(NavigationVoice.clipId("x"));
    }
    @Test public void everyClipExistsInAssetsAndManifest() throws Exception {
        Path dir=Paths.get("src/main/assets/voice-cache");String manifest=new String(Files.readAllBytes(dir.resolve("manifest.json")),"UTF-8");
        for(String c:NavigationVoice.codes()){String id=NavigationVoice.clipId(c);assertTrue(id,Files.exists(dir.resolve(id+".f32")));assertTrue(id,manifest.contains("\""+id+"\""));}
    }
}

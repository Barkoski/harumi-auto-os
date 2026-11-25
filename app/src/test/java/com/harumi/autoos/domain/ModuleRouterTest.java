package com.harumi.autoos.domain;
import org.junit.Test;
import static org.junit.Assert.*;
public class ModuleRouterTest {
    private final ModuleRouter r = new ModuleRouter();
    @Test public void rejectsArbitraryCommands() { for (String a : new String[]{"shell.exec", "mcu.write", "ecu.write", "firmware.flash", "package.uninstall", "apps.open.evil", "connection.phone", "", null}) assertFalse(r.permits(a)); }
    @Test public void onlyKnownModules() { assertTrue(r.validModule("NAV")); assertTrue(r.validModule("MUSIC")); assertTrue(r.validModule("CAMERA360")); assertFalse(r.validModule("com.example.evil")); assertFalse(r.validModule(null)); }
    @Test public void permitsNavActions() { for (String a : new String[]{"nav.start", "nav.stop", "nav.say", "nav.replay"}) { assertTrue(r.permits(a)); assertNull(r.moduleFor(a)); } assertFalse(r.permits("nav.exec")); }
    @Test public void mapsOnlyLaunchActions() { assertEquals("NAV", r.moduleFor("apps.open.nav")); assertEquals("MUSIC", r.moduleFor("apps.open.music")); assertEquals("CAMERA360", r.moduleFor("apps.open.camera360")); assertNull(r.moduleFor("settings.open.android")); assertNull(r.moduleFor(null)); }
}

package com.harumi.autoos.domain;
import java.util.Set;
public final class ModuleRouter {
    private static final Set<String> MODULES = Set.of("NAV", "MUSIC", "CAMERA360");
    private static final Set<String> ACTIONS = Set.of("assistant.finish.listen", "media.previous", "media.playpause", "media.next", "launcher.list", "launcher.open", "catalog.open", "catalog.store", "catalog.assign", "catalog.list", "catalog.all", "apps.open.nav", "apps.open.music", "apps.open.camera360", "apps.choose", "apps.clear", "settings.open.android", "settings.open.home", "device.read.basic", "voice.greet", "oem.home", "assistant.ask", "assistant.listen", "assistant.cancel", "assistant.cancel.quiet", "connection.wifi", "connection.bluetooth", "wake.toggle", "wake.learn", "wake.test", "nav.start", "nav.stop", "nav.say", "nav.replay");
    public boolean permits(String action) { return action != null && ACTIONS.contains(action); }
    public boolean validModule(String module) { return module != null && MODULES.contains(module); }
    public String moduleFor(String action) {
        if (action == null) return null;
        return switch (action) {
            case "apps.open.nav" -> "NAV";
            case "apps.open.music" -> "MUSIC";
            case "apps.open.camera360" -> "CAMERA360";
            default -> null;
        };
    }
}

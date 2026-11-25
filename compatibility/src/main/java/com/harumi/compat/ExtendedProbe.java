package com.harumi.compat;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.FeatureInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.os.Build;
import android.util.DisplayMetrics;
import android.view.Display;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Coleta extra de diagnóstico. Só leitura local: sem rede, sem localização, sem contatos/contas/números. Cada bloco falha sozinho. */
final class ExtendedProbe {
    private ExtendedProbe() { }

    static JSONObject collect(Activity a) {
        JSONObject j = new JSONObject();
        PackageManager pm = a.getPackageManager();
        screen(a, j); home(a, pm, j); cameras(a, j); features(pm, j); packages(pm, j);
        dialer(a, pm, j); audio(a, j); build(j);
        return j;
    }

    private static void fail(JSONObject j, String key, Exception e) {
        try { j.put(key, "Falhou: " + e.getClass().getSimpleName()); } catch (Exception ignored) { }
    }

    @SuppressWarnings("deprecation")
    private static void screen(Activity a, JSONObject j) {
        try {
            Display d = a.getWindowManager().getDefaultDisplay();
            DisplayMetrics m = new DisplayMetrics();
            d.getRealMetrics(m);
            JSONObject s = new JSONObject();
            s.put("largura_px", m.widthPixels); s.put("altura_px", m.heightPixels);
            s.put("densityDpi", m.densityDpi); s.put("density", m.density);
            s.put("xdpi", m.xdpi); s.put("ydpi", m.ydpi);
            s.put("refresh_hz", d.getRefreshRate());
            j.put("Tela real", s);
        } catch (Exception e) { fail(j, "Tela real", e); }
    }

    private static void home(Activity a, PackageManager pm, JSONObject j) {
        try {
            Intent home = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME);
            JSONObject h = new JSONObject();
            JSONArray list = new JSONArray();
            for (ResolveInfo r : pm.queryIntentActivities(home, 0)) {
                JSONObject o = new JSONObject();
                o.put("pacote", r.activityInfo.packageName); o.put("activity", r.activityInfo.name);
                o.put("nome", r.loadLabel(pm).toString());
                list.put(o);
            }
            h.put("lista", list);
            ResolveInfo def = pm.resolveActivity(home, PackageManager.MATCH_DEFAULT_ONLY);
            if (def == null || def.activityInfo == null) h.put("padrao", "Não identificada");
            else h.put("padrao", def.activityInfo.packageName + "/" + def.activityInfo.name);
            j.put("HOME (tela inicial)", h);
        } catch (Exception e) { fail(j, "HOME (tela inicial)", e); }
    }

    private static void cameras(Activity a, JSONObject j) {
        try {
            CameraManager cm = (CameraManager) a.getSystemService(Context.CAMERA_SERVICE);
            JSONArray arr = new JSONArray();
            if (cm != null) for (String id : cm.getCameraIdList()) {
                JSONObject o = new JSONObject();
                o.put("id", id);
                try {
                    CameraCharacteristics c = cm.getCameraCharacteristics(id);
                    Integer facing = c.get(CameraCharacteristics.LENS_FACING);
                    o.put("lente", facing == null ? "desconhecida" : facing == CameraCharacteristics.LENS_FACING_FRONT ? "frontal"
                            : facing == CameraCharacteristics.LENS_FACING_BACK ? "traseira" : facing == CameraCharacteristics.LENS_FACING_EXTERNAL ? "externa" : "código " + facing);
                    Integer lvl = c.get(CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL);
                    o.put("nivel_hardware", lvl == null ? "desconhecido" : level(lvl));
                } catch (Exception e) { o.put("erro", e.getClass().getSimpleName()); }
                arr.put(o);
            }
            j.put("Câmeras", arr);
        } catch (Exception e) { fail(j, "Câmeras", e); }
    }

    private static String level(int v) {
        switch (v) {
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_LEGACY: return "LEGACY";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_LIMITED: return "LIMITED";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_FULL: return "FULL";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_3: return "LEVEL_3";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_EXTERNAL: return "EXTERNAL";
            default: return "código " + v;
        }
    }

    private static void features(PackageManager pm, JSONObject j) {
        try {
            JSONArray arr = new JSONArray();
            FeatureInfo[] f = pm.getSystemAvailableFeatures();
            if (f != null) for (FeatureInfo i : f) if (i.name != null) arr.put(i.name);
            j.put("Recursos do sistema (features)", arr);
        } catch (Exception e) { fail(j, "Recursos do sistema (features)", e); }
    }

    private static void packages(PackageManager pm, JSONObject j) {
        try {
            Set<String> withLauncher = new HashSet<>();
            try {
                Intent l = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
                for (ResolveInfo r : pm.queryIntentActivities(l, 0)) withLauncher.add(r.activityInfo.packageName);
            } catch (Exception ignored) { }
            JSONArray arr = new JSONArray();
            List<PackageInfo> all = pm.getInstalledPackages(0);
            for (PackageInfo p : all) {
                JSONObject o = new JSONObject();
                o.put("pacote", p.packageName);
                o.put("versao", p.versionName == null ? "" : p.versionName);
                boolean sys = p.applicationInfo != null && (p.applicationInfo.flags & (ApplicationInfo.FLAG_SYSTEM | ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)) != 0;
                o.put("sistema", sys);
                o.put("tem_launcher", withLauncher.contains(p.packageName));
                arr.put(o);
            }
            JSONObject pk = new JSONObject();
            pk.put("total", arr.length()); pk.put("lista", arr);
            j.put("Pacotes instalados", pk);
        } catch (Exception e) { fail(j, "Pacotes instalados", e); }
    }

    private static void dialer(Activity a, PackageManager pm, JSONObject j) {
        JSONObject d = new JSONObject();
        try {
            android.telecom.TelecomManager tm = (android.telecom.TelecomManager) a.getSystemService(Context.TELECOM_SERVICE);
            String p = tm == null ? null : tm.getDefaultDialerPackage();
            d.put("discador_padrao", p == null ? "Não identificado" : p);
        } catch (SecurityException e) { try { d.put("discador_padrao", "Bloqueado pelo sistema (SecurityException)"); } catch (Exception ignored) { } }
        catch (Exception e) { try { d.put("discador_padrao", "Falhou: " + e.getClass().getSimpleName()); } catch (Exception ignored) { } }
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                android.app.role.RoleManager rm = (android.app.role.RoleManager) a.getSystemService(Context.ROLE_SERVICE);
                JSONObject roles = new JSONObject();
                String[] names = {android.app.role.RoleManager.ROLE_HOME, android.app.role.RoleManager.ROLE_DIALER, android.app.role.RoleManager.ROLE_SMS,
                        android.app.role.RoleManager.ROLE_BROWSER, android.app.role.RoleManager.ROLE_ASSISTANT, android.app.role.RoleManager.ROLE_CALL_REDIRECTION,
                        android.app.role.RoleManager.ROLE_CALL_SCREENING, android.app.role.RoleManager.ROLE_EMERGENCY};
                for (String n : names) {
                    try { roles.put(n, rm != null && rm.isRoleAvailable(n) ? "disponível" : "indisponível"); }
                    catch (Exception e) { roles.put(n, "Falhou: " + e.getClass().getSimpleName()); }
                }
                d.put("roles_disponiveis", roles);
            } else d.put("roles_disponiveis", "API < 29");
        } catch (Exception e) { try { d.put("roles_disponiveis", "Falhou: " + e.getClass().getSimpleName()); } catch (Exception ignored) { } }
        try {
            ResolveInfo b = pm.resolveActivity(new Intent(Intent.ACTION_VIEW, android.net.Uri.parse("http://example.com")), PackageManager.MATCH_DEFAULT_ONLY);
            d.put("navegador_padrao", b == null || b.activityInfo == null ? "Não identificado" : b.activityInfo.packageName);
        } catch (Exception e) { try { d.put("navegador_padrao", "Falhou: " + e.getClass().getSimpleName()); } catch (Exception ignored) { } }
        try { j.put("Discador e funções padrão", d); } catch (Exception ignored) { }
    }

    private static void audio(Activity a, JSONObject j) {
        try {
            AudioManager am = (AudioManager) a.getSystemService(Context.AUDIO_SERVICE);
            JSONObject o = new JSONObject();
            o.put("saidas", devices(am, AudioManager.GET_DEVICES_OUTPUTS));
            o.put("entradas", devices(am, AudioManager.GET_DEVICES_INPUTS));
            j.put("Dispositivos de áudio", o);
        } catch (Exception e) { fail(j, "Dispositivos de áudio", e); }
    }

    private static JSONArray devices(AudioManager am, int flag) throws Exception {
        JSONArray arr = new JSONArray();
        if (am == null) return arr;
        for (AudioDeviceInfo d : am.getDevices(flag)) {
            JSONObject o = new JSONObject();
            o.put("tipo", typeName(d.getType())); o.put("tipo_codigo", d.getType());
            CharSequence n = d.getProductName();
            o.put("nome", n == null ? "" : n.toString());
            arr.put(o);
        }
        return arr;
    }

    private static String typeName(int t) {
        switch (t) {
            case AudioDeviceInfo.TYPE_BUILTIN_EARPIECE: return "BUILTIN_EARPIECE";
            case AudioDeviceInfo.TYPE_BUILTIN_SPEAKER: return "BUILTIN_SPEAKER";
            case AudioDeviceInfo.TYPE_BUILTIN_MIC: return "BUILTIN_MIC";
            case AudioDeviceInfo.TYPE_WIRED_HEADSET: return "WIRED_HEADSET";
            case AudioDeviceInfo.TYPE_WIRED_HEADPHONES: return "WIRED_HEADPHONES";
            case AudioDeviceInfo.TYPE_LINE_ANALOG: return "LINE_ANALOG";
            case AudioDeviceInfo.TYPE_BLUETOOTH_SCO: return "BLUETOOTH_SCO";
            case AudioDeviceInfo.TYPE_BLUETOOTH_A2DP: return "BLUETOOTH_A2DP";
            case AudioDeviceInfo.TYPE_HDMI: return "HDMI";
            case AudioDeviceInfo.TYPE_USB_DEVICE: return "USB_DEVICE";
            case AudioDeviceInfo.TYPE_USB_HEADSET: return "USB_HEADSET";
            case AudioDeviceInfo.TYPE_TELEPHONY: return "TELEPHONY";
            case AudioDeviceInfo.TYPE_BUS: return "BUS";
            case AudioDeviceInfo.TYPE_FM_TUNER: return "FM_TUNER";
            case AudioDeviceInfo.TYPE_AUX_LINE: return "AUX_LINE";
            default: return "código " + t;
        }
    }

    private static void build(JSONObject j) {
        try {
            JSONObject b = new JSONObject();
            b.put("PRODUCT", Build.PRODUCT); b.put("DEVICE", Build.DEVICE); b.put("BOARD", Build.BOARD); b.put("HARDWARE", Build.HARDWARE);
            b.put("BRAND", Build.BRAND); b.put("FINGERPRINT", Build.FINGERPRINT);
            b.put("SUPPORTED_ABIS", android.text.TextUtils.join(", ", Build.SUPPORTED_ABIS));
            if (Build.VERSION.SDK_INT >= 31) { b.put("SOC_MANUFACTURER", Build.SOC_MANUFACTURER); b.put("SOC_MODEL", Build.SOC_MODEL); }
            b.put("tamanho_pagina_bytes", android.system.Os.sysconf(android.system.OsConstants._SC_PAGESIZE));
            j.put("Build (extra)", b);
        } catch (Exception e) { fail(j, "Build (extra)", e); }
    }
}

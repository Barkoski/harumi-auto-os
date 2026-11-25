package com.harumi.autoos.oem;
import android.app.Activity;
import android.content.*;
import android.content.pm.*;
import java.util.*;
public final class OemAppGateway {
    private final Activity activity;
    public OemAppGateway(Activity a) { activity = a; }
    public List<ResolveInfo> list() {
        Intent query = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> result = new ArrayList<>();
        for (ResolveInfo info : activity.getPackageManager().queryIntentActivities(query, 0)) {
            ActivityInfo ai = info.activityInfo;
            if (ai != null && ai.exported && ai.enabled && ai.applicationInfo.enabled && !activity.getPackageName().equals(ai.packageName)) result.add(info);
        }
        PackageManager pm = activity.getPackageManager();
        Map<ResolveInfo, String> labels = new IdentityHashMap<>();
        for (ResolveInfo i : result) labels.put(i, String.valueOf(i.loadLabel(pm)));
        result.sort((a, b) -> String.CASE_INSENSITIVE_ORDER.compare(labels.get(a), labels.get(b)));
        return result;
    }
    public String label(String saved) {
        if (saved == null) return "Escolher aplicativo";
        ComponentName c = ComponentName.unflattenFromString(saved);
        if (c != null) try { PackageManager pm = activity.getPackageManager(); return pm.getActivityInfo(c, 0).loadLabel(pm).toString(); } catch (PackageManager.NameNotFoundException | RuntimeException e) { }
        return "App indisponível · escolher outro";
    }
    public List<ResolveInfo> listFor(String module) {
        Set<String> packages = new HashSet<>();
        Intent query;
        if ("NAV".equals(module)) {
            query = new Intent(Intent.ACTION_VIEW, android.net.Uri.parse("geo:0,0?q=destino"));
            packages.addAll(Arrays.asList("com.google.android.apps.maps", "com.waze"));
        } else if ("MUSIC".equals(module)) {
            query = new Intent("android.intent.action.MUSIC_PLAYER");
            packages.addAll(Arrays.asList("com.spotify.music", "com.google.android.apps.youtube.music", "org.videolan.vlc", "com.apple.android.music"));
        } else return list();
        for (ResolveInfo i : activity.getPackageManager().queryIntentActivities(query, 0))
            if (i.activityInfo != null) packages.add(i.activityInfo.packageName);
        List<ResolveInfo> result = new ArrayList<>();
        for (ResolveInfo i : list()) if (packages.contains(i.activityInfo.packageName)) result.add(i);
        return result;
    }
    public ComponentName component(ResolveInfo i) { return new ComponentName(i.activityInfo.packageName, i.activityInfo.name); }
    public boolean open(String saved) {
        if (saved == null) return false;
        for (ResolveInfo i : list()) {
            ComponentName c = component(i);
            if (c.flattenToString().equals(saved)) {
                try { activity.startActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER).setComponent(c).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED)); return true; }
                catch (ActivityNotFoundException | SecurityException e) { return false; }
            }
        }
        return false;
    }
}

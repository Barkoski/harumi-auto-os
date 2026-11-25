package com.harumi.autoos.oem;
import android.content.Context;
import android.content.SharedPreferences;
import com.harumi.autoos.domain.ModuleRouter;
public final class AppAssignmentStore {
    private final SharedPreferences prefs;
    private final ModuleRouter policy = new ModuleRouter();
    public AppAssignmentStore(Context c) { prefs = c.getSharedPreferences("assignments_v1", Context.MODE_PRIVATE); }
    public String get(String module) { return policy.validModule(module) ? prefs.getString(module, null) : null; }
    public void set(String module, String component) { if (!policy.validModule(module)) throw new IllegalArgumentException("Módulo inválido"); prefs.edit().putString(module, component).apply(); }
    public void clear(String module) { if (policy.validModule(module)) prefs.edit().remove(module).apply(); }
}

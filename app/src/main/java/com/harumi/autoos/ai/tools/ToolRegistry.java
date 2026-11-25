package com.harumi.autoos.ai.tools;
import java.util.*;
/** Allowlist imutavel de ferramentas. O que nao esta aqui nao existe para a IA. */
public final class ToolRegistry {
    private final Map<String,ToolSpec> specs;
    public ToolRegistry(Collection<ToolSpec> list) { Map<String,ToolSpec> m=new LinkedHashMap<>();for(ToolSpec s:list)m.put(s.id(),s);specs=Collections.unmodifiableMap(m); }
    public Optional<ToolSpec> get(String id) { return id==null?Optional.empty():Optional.ofNullable(specs.get(id)); }
    public Set<String> ids() { return specs.keySet(); }
    private static ToolSpec t(String id,RiskClass r,Object... kv) { Map<String,SlotSpec> m=new LinkedHashMap<>();for(int i=0;i<kv.length;i+=2)m.put((String)kv[i],(SlotSpec)kv[i+1]);return new ToolSpec(id,r,m); }
    public static ToolRegistry defaults() {
        return new ToolRegistry(List.of(
            t("nav.open",RiskClass.UI),
            t("nav.route",RiskClass.UI,"destination",SlotSpec.string(160)),
            t("nav.route_between",RiskClass.UI,"origin",SlotSpec.string(160),"destination",SlotSpec.string(160)),
            t("media.open",RiskClass.UI),
            t("media.play_pause",RiskClass.MEDIA),
            t("media.volume",RiskClass.MEDIA,"level",SlotSpec.integer(0,100)),
            t("diagnostics.read",RiskClass.INFO),
            t("settings.wifi",RiskClass.UI),
            t("settings.bluetooth",RiskClass.UI),
            t("lights.aux",RiskClass.PHYSICAL,"state",SlotSpec.enumOf("on","off")),
            t("assistant.greet",RiskClass.INFO),
            t("assistant.quick_reply",RiskClass.INFO),
            t("assistant.cancel",RiskClass.INFO)));
    }
}

package com.harumi.autoos.ai.tools;
import com.harumi.autoos.ai.LocalCommandParser;
import java.util.Map;
import java.util.Optional;
/** Converte comandos do parser deterministico em ToolCall (Origin.VOICE_RULE). CHAT nao tem ferramenta: vai ao LLM. */
public final class CommandToolAdapter {
    public Optional<ToolCall> adapt(LocalCommandParser.Command c,String requestId) {
        String d=c.destination()==null?"":c.destination();
        switch(c.action()) {
            case MAP: return call("nav.open",Map.of(),requestId);
            case MUSIC: return call("media.open",Map.of(),requestId);
            case ROUTE: return call("nav.route",Map.of("destination",d),requestId);
            case ROUTE_BETWEEN: { int i=d.indexOf('\n');if(i<0)return Optional.empty();return call("nav.route_between",Map.of("origin",d.substring(0,i),"destination",d.substring(i+1)),requestId); }
            case DIAGNOSTICS: return call("diagnostics.read",Map.of(),requestId);
            case GREETING: return call("assistant.greet",Map.of(),requestId);
            case QUICK_REPLY: return call("assistant.quick_reply",Map.of(),requestId);
            case WIFI_SETTINGS: return call("settings.wifi",Map.of(),requestId);
            case BLUETOOTH_SETTINGS: return call("settings.bluetooth",Map.of(),requestId);
            case STOP: return call("assistant.cancel",Map.of(),requestId);
            case CHAT: default: return Optional.empty();
        }
    }
    private static Optional<ToolCall> call(String id,Map<String,String> s,String r) { return Optional.of(new ToolCall(id,s,Origin.VOICE_RULE,r)); }
}

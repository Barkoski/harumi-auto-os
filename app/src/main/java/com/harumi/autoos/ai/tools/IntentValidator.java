package com.harumi.autoos.ai.tools;
import java.util.Optional;
/**
 * Valida ToolCall contra a allowlist. Regras de confirmacao:
 * - PHYSICAL sempre exige confirmacao, de qualquer origem.
 * - Origem LLM: INFO executa sem confirmar; UI, MEDIA e PHYSICAL exigem confirmacao.
 * - TOUCH/VOICE_RULE em INFO/UI/MEDIA: aceito direto.
 */
public final class IntentValidator {
    public enum Status { ACCEPTED, REJECTED, NEEDS_CONFIRMATION }
    public record Validation(Status status,String reason) { }
    private final ToolRegistry registry;
    public IntentValidator(ToolRegistry registry) { this.registry=registry; }
    public Validation validate(ToolCall c) {
        if(c==null||c.origin()==null) return rej("chamada ou origem ausente");
        Optional<ToolSpec> o=registry.get(c.toolId());
        if(o.isEmpty()) return rej("ferramenta fora da allowlist");
        ToolSpec s=o.get();
        for(String k:c.slots().keySet()) if(!s.slots().containsKey(k)) return rej("slot desconhecido '"+k+"'");
        for(var e:s.slots().entrySet()) {
            if(!c.slots().containsKey(e.getKey())) return rej("slot ausente '"+e.getKey()+"'");
            String why=e.getValue().check(e.getKey(),c.slots().get(e.getKey()));
            if(why!=null) return rej(why);
        }
        if(s.risk()==RiskClass.PHYSICAL) return new Validation(Status.NEEDS_CONFIRMATION,"acao fisica exige confirmacao");
        if(c.origin()==Origin.LLM&&s.risk()!=RiskClass.INFO) return new Validation(Status.NEEDS_CONFIRMATION,"origem LLM exige confirmacao");
        return new Validation(Status.ACCEPTED,"ok");
    }
    private static Validation rej(String r) { return new Validation(Status.REJECTED,r); }
}

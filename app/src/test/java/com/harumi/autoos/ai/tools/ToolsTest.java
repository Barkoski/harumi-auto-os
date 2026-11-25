package com.harumi.autoos.ai.tools;
import com.harumi.autoos.ai.LocalCommandParser;
import com.harumi.autoos.ai.LocalCommandParser.Action;
import com.harumi.autoos.ai.tools.IntentValidator.Status;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;
public class ToolsTest {
    private final ToolRegistry reg=ToolRegistry.defaults();
    private final IntentValidator v=new IntentValidator(reg);
    private static ToolCall c(String id,Map<String,String> s,Origin o,String r) { return new ToolCall(id,s,o,r); }
    @Test public void idOutsideAllowlistRejected() { assertEquals(Status.REJECTED,v.validate(c("shell.exec",Map.of(),Origin.LLM,"1")).status());assertTrue(reg.get("x").isEmpty()); }
    @Test public void slotOutOfRangeUnknownMissingWrongTypeRejected() {
        assertEquals(Status.REJECTED,v.validate(c("media.volume",Map.of("level","101"),Origin.TOUCH,"1")).status());
        assertEquals(Status.REJECTED,v.validate(c("media.volume",Map.of("level","abc"),Origin.TOUCH,"1")).status());
        assertEquals(Status.REJECTED,v.validate(c("media.volume",Map.of(),Origin.TOUCH,"1")).status());
        assertEquals(Status.REJECTED,v.validate(c("media.volume",Map.of("level","5","x","y"),Origin.TOUCH,"1")).status());
        assertEquals(Status.REJECTED,v.validate(c("nav.route",Map.of("destination","intent:evil"),Origin.VOICE_RULE,"1")).status());
        assertEquals(Status.ACCEPTED,v.validate(c("media.volume",Map.of("level","50"),Origin.TOUCH,"1")).status());
    }
    @Test public void physicalNeverRunsWithoutConfirmation() {
        ToolCall k=c("lights.aux",Map.of("state","on"),Origin.TOUCH,"r1");
        assertEquals(Status.NEEDS_CONFIRMATION,v.validate(k).status());
        ConfirmationGate g=new ConfirmationGate(()->0L);
        assertTrue(g.confirm("r1").isEmpty());
        g.pending(k,1000);
        assertTrue(g.confirm("r1").isPresent());
        assertTrue(g.confirm("r1").isEmpty());
    }
    @Test public void timeoutCancels() {
        long[] t={0};ConfirmationGate g=new ConfirmationGate(()->t[0]);
        g.pending(c("lights.aux",Map.of("state","on"),Origin.TOUCH,"r1"),1000);
        t[0]=1000;
        assertTrue(g.confirm("r1").isEmpty());assertEquals(ConfirmationGate.State.CANCELLED,g.state());
    }
    @Test public void wrongRequestIdDoesNotExecuteAndNewPendingReplacesOld() {
        ConfirmationGate g=new ConfirmationGate(()->0L);
        g.pending(c("lights.aux",Map.of("state","on"),Origin.TOUCH,"a"),1000);
        assertTrue(g.confirm("b").isEmpty());
        g.pending(c("lights.aux",Map.of("state","off"),Origin.TOUCH,"b"),1000);
        assertTrue(g.confirm("a").isEmpty());assertTrue(g.confirm("b").isPresent());
        g.pending(c("lights.aux",Map.of("state","on"),Origin.TOUCH,"c"),1000);g.cancel();
        assertTrue(g.confirm("c").isEmpty());
    }
    @Test public void llmRiskRules() {
        assertEquals(Status.NEEDS_CONFIRMATION,v.validate(c("media.play_pause",Map.of(),Origin.LLM,"1")).status());
        assertEquals(Status.NEEDS_CONFIRMATION,v.validate(c("nav.open",Map.of(),Origin.LLM,"1")).status());
        assertEquals(Status.ACCEPTED,v.validate(c("diagnostics.read",Map.of(),Origin.LLM,"1")).status());
        assertEquals(Status.ACCEPTED,v.validate(c("media.play_pause",Map.of(),Origin.VOICE_RULE,"1")).status());
    }
    @Test public void adapterCoversAllParserActions() {
        CommandToolAdapter a=new CommandToolAdapter();
        for(Action act:Action.values()) {
            String d=act==Action.ROUTE?"Londrina":act==Action.ROUTE_BETWEEN?"Cuiaba\nCuritiba":"";
            var o=a.adapt(new LocalCommandParser.Command(act,d),"r");
            if(act==Action.CHAT) { assertTrue(o.isEmpty());continue; }
            assertTrue(act.name(),o.isPresent());
            assertEquals(Origin.VOICE_RULE,o.get().origin());
            assertEquals(act.name(),Status.ACCEPTED,v.validate(o.get()).status());
        }
    }
}

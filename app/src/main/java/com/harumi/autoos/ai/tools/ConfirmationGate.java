package com.harumi.autoos.ai.tools;
import java.util.Optional;
import java.util.function.LongSupplier;
/** Guarda um unico pedido pendente. confirm() devolve a chamada a executar so se o requestId bate e nao expirou. */
public final class ConfirmationGate {
    public enum State { IDLE, PENDING, CONFIRMED, CANCELLED }
    private final LongSupplier clock;
    private ToolCall pending;
    private long deadline;
    private State state=State.IDLE;
    public ConfirmationGate(LongSupplier clock) { this.clock=clock; }
    /** Novo pendente substitui e cancela o anterior. */
    public synchronized void pending(ToolCall call,long timeoutMs) {
        if(call==null||call.requestId()==null||timeoutMs<=0) throw new IllegalArgumentException("pendencia invalida");
        pending=call;deadline=clock.getAsLong()+timeoutMs;state=State.PENDING;
    }
    public synchronized Optional<ToolCall> confirm(String requestId) {
        expire();
        if(state!=State.PENDING||requestId==null||!requestId.equals(pending.requestId())) return Optional.empty();
        ToolCall c=pending;pending=null;state=State.CONFIRMED;return Optional.of(c);
    }
    public synchronized void cancel() { if(state==State.PENDING){pending=null;state=State.CANCELLED;} }
    public synchronized State state() { expire();return state; }
    public synchronized Optional<ToolCall> current() { expire();return Optional.ofNullable(pending); }
    private void expire() { if(state==State.PENDING&&clock.getAsLong()>=deadline){pending=null;state=State.CANCELLED;} }
}

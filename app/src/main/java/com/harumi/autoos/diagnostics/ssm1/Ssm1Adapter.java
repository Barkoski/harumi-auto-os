package com.harumi.autoos.diagnostics.ssm1;
import com.harumi.autoos.diagnostics.DiagnosticMonitor;
import com.harumi.autoos.diagnostics.DiagnosticMonitor.*;
import java.util.*;
import java.util.function.LongSupplier;
/** Adaptador somente leitura. Parâmetros sem endereço confirmado são ignorados. NÃO VERIFICADO. */
public final class Ssm1Adapter implements DiagnosticMonitor.ReadOnlyAdapter {
    public static final String SOURCE = "SSM1 (não validado)";
    private static final int TIMEOUT_MS = 500;
    private final SerialTransport transport;
    private final List<Ssm1Constants.Param> params;
    private final LongSupplier clock;
    private boolean opened;
    public Ssm1Adapter(SerialTransport transport) { this(transport, Ssm1Constants.CANDIDATES, System::currentTimeMillis); }
    public Ssm1Adapter(SerialTransport transport, List<Ssm1Constants.Param> params, LongSupplier clock) {
        this.transport = Objects.requireNonNull(transport); this.params = List.copyOf(params); this.clock = Objects.requireNonNull(clock);
    }
    @Override public Snapshot readSnapshot() {
        try {
            if (!opened) { transport.open(); opened = true; }
            Map<String,Reading> out = new HashMap<>();
            for (Ssm1Constants.Param p : params) {
                if (!p.confirmed()) continue;
                transport.write(Ssm1Codec.readRequest(p.address()));
                int raw = Ssm1Codec.decodeResponse(p.address(), transport.read(Ssm1Codec.RESPONSE_LENGTH, TIMEOUT_MS));
                out.put(p.key(), new Reading(raw * p.scale() + p.offset(), p.unit()));
            }
            return new Snapshot(true, SOURCE, clock.getAsLong(), out);
        } catch (Exception e) {
            opened = false; transport.close();
            return new Snapshot(false, SOURCE, 0, Collections.emptyMap());
        }
    }
}

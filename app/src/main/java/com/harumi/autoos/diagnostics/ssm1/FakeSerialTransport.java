package com.harumi.autoos.diagnostics.ssm1;
import java.io.*;
import java.util.*;
/** Simulador determinístico: só aceita requisições de leitura e de parada; responde com valores configurados (endereço não configurado = 0). */
public final class FakeSerialTransport implements SerialTransport {
    private final Map<Integer,Integer> values = new HashMap<>();
    private final ArrayDeque<Byte> pending = new ArrayDeque<>();
    private boolean open;
    public FakeSerialTransport set(int address, int raw) { values.put(address, raw & 0xFF); return this; }
    public boolean isOpen() { return open; }
    @Override public void open() { open = true; }
    @Override public void write(byte[] d) throws IOException {
        if (!open) throw new IOException("Transporte fechado");
        if (d.length == 4 && (d[0] & 0xFF) == Ssm1Constants.READ_OPCODE && d[3] == 0) {
            int a = ((d[1] & 0xFF) << 8) | (d[2] & 0xFF);
            pending.add(d[1]); pending.add(d[2]); pending.add((byte) (int) values.getOrDefault(a, 0));
        } else if (Arrays.equals(d, Ssm1Constants.STOP_COMMAND)) pending.clear();
        else throw new IllegalArgumentException("Comando não permitido no simulador");
    }
    @Override public byte[] read(int length, int timeoutMs) throws IOException {
        if (!open) throw new IOException("Transporte fechado");
        int n = Math.min(length, pending.size());
        byte[] out = new byte[n];
        for (int i = 0; i < n; i++) out[i] = pending.poll();
        return out;
    }
    @Override public void close() { open = false; pending.clear(); }
}

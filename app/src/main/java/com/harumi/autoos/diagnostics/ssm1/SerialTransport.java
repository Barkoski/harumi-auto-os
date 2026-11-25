package com.harumi.autoos.diagnostics.ssm1;
import java.io.IOException;
public interface SerialTransport extends AutoCloseable {
    void open() throws IOException;
    void write(byte[] data) throws IOException;
    /** Lê até length bytes; devolve o que chegou até o timeout (pode ser menos, ou vazio). */
    byte[] read(int length, int timeoutMs) throws IOException;
    @Override void close();
}

package com.harumi.autoos.diagnostics.ssm1;
import com.harumi.autoos.diagnostics.DiagnosticMonitor.Snapshot;
import java.lang.reflect.*;
import java.util.List;
import org.junit.Test;
import static org.junit.Assert.*;
public class Ssm1Test {
    private static final int FORBIDDEN_WRITE_OPCODE = 0xAA; // de memória, NÃO verificado
    @Test public void buildsReadRequest() { assertArrayEquals(new byte[]{0x78, 0x12, 0x34, 0x00}, Ssm1Codec.readRequest(0x1234)); assertArrayEquals(new byte[]{0x12, 0, 0, 0}, Ssm1Codec.stopRequest()); }
    @Test public void rejectsBadAddress() { for (int a : new int[]{-1, 0x10000}) try { Ssm1Codec.readRequest(a); fail(); } catch (IllegalArgumentException ok) { } }
    @Test public void decodesValidAndRejectsWrongEcho() {
        assertEquals(200, Ssm1Codec.decodeResponse(0x1234, new byte[]{0x12, 0x34, (byte) 200}));
        try { Ssm1Codec.decodeResponse(0x1234, new byte[]{0x12, 0x35, 1}); fail(); } catch (IllegalArgumentException ok) { }
        try { Ssm1Codec.decodeResponse(0x1234, new byte[]{0x12, 0x34}); fail(); } catch (IllegalArgumentException ok) { }
    }
    @Test public void noWriteInCodecOrConstants() {
        for (Class<?> c : new Class<?>[]{Ssm1Codec.class, Ssm1Constants.class}) {
            for (Method m : c.getDeclaredMethods()) assertFalse(m.getName(), m.getName().toLowerCase().matches(".*(write|escrita).*"));
            for (Field f : c.getDeclaredFields()) assertFalse(f.getName(), f.getName().toLowerCase().matches(".*(write|escrita).*"));
        }
        for (int a = 0; a <= 0xFFFF; a += 0x101) assertNotEquals(FORBIDDEN_WRITE_OPCODE, Ssm1Codec.readRequest(a)[0] & 0xFF);
        assertNotEquals(FORBIDDEN_WRITE_OPCODE, Ssm1Codec.stopRequest()[0] & 0xFF);
    }
    @Test public void fakeRejectsNonReadCommands() throws Exception {
        FakeSerialTransport t = new FakeSerialTransport(); t.open();
        try { t.write(new byte[]{(byte) FORBIDDEN_WRITE_OPCODE, 0, 1, 5}); fail(); } catch (IllegalArgumentException ok) { }
    }
    @Test public void adapterBuildsConnectedSnapshot() {
        FakeSerialTransport t = new FakeSerialTransport().set(0x0010, 80).set(0x0011, 140);
        List<Ssm1Constants.Param> ps = List.of(new Ssm1Constants.Param("rpm", "rotação", "rpm", 0x0010, 25.0, 0), new Ssm1Constants.Param("coolant_temp", "temp", "°C", 0x0011, 1.0, -50), new Ssm1Constants.Param("speed", "vel", "km/h", Ssm1Constants.UNCONFIRMED_ADDRESS, 1, 0));
        Snapshot s = new Ssm1Adapter(t, ps, () -> 1234L).readSnapshot();
        assertTrue(s.connected()); assertEquals("SSM1 (não validado)", s.source()); assertEquals(1234L, s.observedAtMs());
        assertEquals(2000.0, s.readings().get("rpm").value(), 0); assertEquals("rpm", s.readings().get("rpm").unit());
        assertEquals(90.0, s.readings().get("coolant_temp").value(), 0); assertEquals(2, s.readings().size());
    }
    @Test public void defaultAdapterWithUnconfirmedAddressesIsConnectedButEmpty() {
        Snapshot s = new Ssm1Adapter(new FakeSerialTransport()).readSnapshot();
        assertTrue(s.connected()); assertTrue(s.readings().isEmpty());
    }
}

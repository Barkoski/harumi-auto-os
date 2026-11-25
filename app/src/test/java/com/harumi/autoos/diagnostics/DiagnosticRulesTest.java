package com.harumi.autoos.diagnostics;
import com.harumi.autoos.diagnostics.DiagnosticMonitor.*;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;
public class DiagnosticRulesTest {
    private final DiagnosticRules r = new DiagnosticRules(DiagnosticRules.DEFAULT_LIMITS, () -> 100_000L);
    private Snapshot snap(long at, Map<String,Reading> m) { return new Snapshot(true, "teste", at, m); }
    @Test public void disconnected() { assertEquals("Scanner desconectado.", r.speak(new Snapshot(false, "x", 0, Map.of()))); assertEquals("Scanner desconectado.", r.speak(null)); }
    @Test public void staleData() { assertTrue(r.speak(snap(94_999L, Map.of("rpm", new Reading(900, "rpm")))).startsWith("Dado antigo")); assertFalse(r.speak(snap(95_000L, Map.of("rpm", new Reading(900, "rpm")))).startsWith("Dado antigo")); }
    @Test public void implausible() { String t = r.speak(snap(100_000L, Map.of("coolant_temp", new Reading(300.5, "°C")))); assertTrue(t, t.contains("Leitura implausível de temperatura do líquido de arrefecimento")); assertTrue(t.contains("300,5")); assertFalse(t.contains("Alerta")); }
    @Test public void aboveThreshold() { String t = r.speak(snap(100_000L, Map.of("coolant_temp", new Reading(108.25, "°C")))); assertTrue(t, t.startsWith("Alerta")); assertTrue(t.contains("108,25")); assertTrue(t.contains("105")); }
    @Test public void normalSummaryKeepsExactNumbers() { String t = r.speak(snap(100_000L, Map.of("battery_voltage", new Reading(13.8, "V"), "rpm", new Reading(850, "rpm")))); assertEquals("Leituras normais: tensão da bateria 13,8 V; rotação do motor 850 rpm.", t); }
}

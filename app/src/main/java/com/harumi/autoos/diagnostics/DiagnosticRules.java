package com.harumi.autoos.diagnostics;
import com.harumi.autoos.diagnostics.DiagnosticMonitor.*;
import java.math.BigDecimal;
import java.util.*;
import java.util.function.LongSupplier;
/** Gera texto pronto para fala (pt-BR) a partir de um Snapshot. Não decide nada sobre o veículo além dos limiares abaixo. */
public final class DiagnosticRules {
    public static final long MAX_AGE_MS = 5000;
    /** Faixa plausível [plausMin, plausMax] e limiar de alerta (acima de alertMax). */
    public record Limits(String label, double plausMin, double plausMax, double alertMax) { }
    /** provisório — validar com manual do veículo */
    public static final Map<String,Limits> DEFAULT_LIMITS = Map.of(
        "rpm", new Limits("rotação do motor", 0, 9000, 6500),
        "coolant_temp", new Limits("temperatura do líquido de arrefecimento", -40, 150, 105),
        "battery_voltage", new Limits("tensão da bateria", 6, 18, 15),
        "speed", new Limits("velocidade", 0, 260, 140));
    private final Map<String,Limits> limits;
    private final LongSupplier clock;
    public DiagnosticRules() { this(DEFAULT_LIMITS, System::currentTimeMillis); }
    public DiagnosticRules(Map<String,Limits> limits, LongSupplier clock) { this.limits = Map.copyOf(limits); this.clock = Objects.requireNonNull(clock); }
    /** Número exatamente como na entrada (sem arredondar), com vírgula decimal. */
    static String num(double v) { return BigDecimal.valueOf(v).stripTrailingZeros().toPlainString().replace('.', ','); }
    public String speak(Snapshot s) {
        if (s == null || !s.connected()) return "Scanner desconectado.";
        long age = clock.getAsLong() - s.observedAtMs();
        if (age < 0 || age > MAX_AGE_MS) return "Dado antigo: a última leitura tem mais de 5 segundos. Não é possível afirmar o estado atual.";
        List<String> problems = new ArrayList<>(), ok = new ArrayList<>();
        for (var e : new TreeMap<>(s.readings()).entrySet()) {
            Limits l = limits.get(e.getKey());
            double v = e.getValue().value();
            String unit = e.getValue().unit();
            String label = l == null ? e.getKey() : l.label();
            String text = label + " " + (Double.isNaN(v) ? "NaN" : num(v)) + " " + unit;
            if (l != null && (Double.isNaN(v) || v < l.plausMin() || v > l.plausMax())) problems.add("Leitura implausível de " + label + ": " + (Double.isNaN(v) ? "valor inválido" : num(v) + " " + unit) + ".");
            else if (l != null && v > l.alertMax()) problems.add("Alerta: " + text + ", acima do limite de " + num(l.alertMax()) + ".");
            else ok.add(text);
        }
        if (!problems.isEmpty()) return String.join(" ", problems);
        return ok.isEmpty() ? "Scanner conectado, sem leituras disponíveis." : "Leituras normais: " + String.join("; ", ok) + ".";
    }
}

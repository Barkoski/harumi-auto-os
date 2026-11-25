package com.harumi.autoos.voice;
import java.text.Normalizer;
import java.util.*;
/**
 * Detecta "Oi Harumi" no texto do reconhecedor offline.
 * O modelo Vosk pt nao tem a palavra "Harumi" no vocabulario: ele ouve algo como "a rumi", "rumi" ou "arrumei".
 * Por isso a comparacao e pelo som aproximado, sempre exigindo a saudacao antes (oi/ola/ei/ok) para evitar disparo
 * em conversa comum. Frases ensinadas pelo Lucas (calibracao) tambem valem.
 */
public final class WakeWord {
    private WakeWord() { }
    private static final Set<String> GREETINGS = Set.of("oi", "ola", "ei", "ok", "hey");
    private static final String TARGET = "arumi";
    public static String normalize(String text) {
        if (text == null) return "";
        return Normalizer.normalize(text, Normalizer.Form.NFD).replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT)
            .replaceAll("[^a-z ]", " ").replaceAll("\\s+", " ").trim();
    }
    /** Forma sonora: sem h, letras dobradas viram simples, sem espacos. */
    static String sound(String text) { return normalize(text).replace(" ", "").replace("h", "").replaceAll("(.)\\1+", "$1"); }
    /** Calibracao: so aceita frase com saudacao ou cujo som fique perto de "arumi" (evita aprender conversa ao fundo). */
    public static boolean acceptsForLearning(String text) {
        String n = normalize(text);
        if (n.isEmpty()) return false;
        for (String w : n.split(" ")) if (GREETINGS.contains(w)) return true;
        return distance(sound(n), TARGET) <= 3;
    }
    public static boolean matches(String text, Collection<String> learned) {
        String n = normalize(text);
        if (n.isEmpty()) return false;
        for (String phrase : learned) { String p = normalize(phrase); if (p.length() >= 6 && (" " + n + " ").contains(" " + p + " ")) return true; }
        String[] words = n.split(" ");
        for (int i = 0; i < words.length; i++) {
            if (!GREETINGS.contains(words[i])) continue;
            // Junta ate 3 palavras depois da saudacao e compara pelo som com "arumi".
            StringBuilder tail = new StringBuilder();
            for (int j = i + 1; j < Math.min(words.length, i + 4); j++) {
                tail.append(words[j]);
                String s = sound(tail.toString());
                int limit = s.length() >= 5 ? 2 : 1;
                if (s.length() >= 4 && distance(s, TARGET) <= limit) return true;
            }
        }
        return false;
    }
    static int distance(String a, String b) {
        int[] prev = new int[b.length() + 1], cur = new int[b.length() + 1];
        for (int j = 0; j <= b.length(); j++) prev[j] = j;
        for (int i = 1; i <= a.length(); i++) {
            cur[0] = i;
            for (int j = 1; j <= b.length(); j++) cur[j] = Math.min(Math.min(cur[j - 1] + 1, prev[j] + 1), prev[j - 1] + (a.charAt(i - 1) == b.charAt(j - 1) ? 0 : 1));
            int[] t = prev; prev = cur; cur = t;
        }
        return prev[b.length()];
    }
}

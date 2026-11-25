package com.harumi.autoos.voice;
import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;
public class WakeWordTest {
    private static final List<String> NONE = List.of();
    @Test public void acceptsLikelyTranscriptionsOfOiHarumi() {
        for (String s : new String[]{"oi harumi", "Oi, Harumi!", "oi a rumi", "oi rumi", "oi arrumei", "olá a rumi", "ei harumi", "bom dia oi a rumi"})
            assertTrue(s, WakeWord.matches(s, NONE));
    }
    @Test public void ignoresOrdinaryConversation() {
        for (String s : new String[]{"", "oi", "oi tudo bem", "a rua está cheia", "oi a rua", "o rumo certo", "harmonia", "arrumei a casa", "oi amor", "e aí", "toque uma música"})
            assertFalse(s, WakeWord.matches(s, NONE));
    }
    @Test public void eAndOAreNotGreetings() {
        for (String s : new String[]{"e a rumi", "o rumi", "e arumi"}) assertFalse(s, WakeWord.matches(s, NONE));
    }
    @Test public void learningOnlyAcceptsGreetingOrSimilarSound() {
        for (String s : new String[]{"oi harumi", "oi dona maria", "ei vamos", "a rumi", "rumi", "arrumei"}) assertTrue(s, WakeWord.acceptsForLearning(s));
        for (String s : new String[]{"", "toque uma musica", "que horas sao agora", "preciso de gasolina"}) assertFalse(s, WakeWord.acceptsForLearning(s));
    }
    @Test public void learnedPhraseTriggers() {
        assertFalse(WakeWord.matches("oi dona maria", NONE));
        assertTrue(WakeWord.matches("oi dona maria", List.of("oi dona maria")));
        assertFalse("frase curta nao vale", WakeWord.matches("oi a", List.of("oi a")));
    }
}

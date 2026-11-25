package com.harumi.autoos.voice;
import org.junit.Test;
import static org.junit.Assert.*;
public class SpeechPronunciationTest {
    @Test public void nameGetsStrongInitialR() { assertEquals("Eu sou a Rarumi.",SpeechPronunciation.forSpeech("Eu sou a Harumi.")); }
    @Test public void handlesAllOccurrencesAndCase() { assertEquals("Rarumi, Rarumi!",SpeechPronunciation.forSpeech("HARUMI, harumi!")); }
    @Test public void preservesOtherWordsAndWrittenSource() { String original="Harumi e Harumizinha";assertEquals("Rarumi e Harumizinha",SpeechPronunciation.forSpeech(original));assertEquals("Harumi e Harumizinha",original); }
    @Test public void handlesNull() { assertEquals("",SpeechPronunciation.forSpeech(null)); }
}

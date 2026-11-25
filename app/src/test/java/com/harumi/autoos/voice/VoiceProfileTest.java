package com.harumi.autoos.voice;
import com.harumi.autoos.ai.LocalCommandParser;
import org.junit.Test;
import static org.junit.Assert.*;
public class VoiceProfileTest {
    @Test public void matchesApprovedAudition() { assertEquals(2,VoiceProfile.SPEAKER);assertEquals(24,VoiceProfile.STEPS);assertEquals(1.25f,VoiceProfile.SPEED,0.0001f);assertEquals(.72f,VoiceProfile.SILENCE_SCALE,0.0001f); }
    @Test public void approvedGreetingUsesCorrectPronunciation() { assertEquals("Oi, Lucas! Eu sou a Rarumi! Quer que eu abra o mapa? Me diz: pra onde a gente vai hoje?",SpeechPronunciation.forSpeech(VoiceProfile.GREETING)); }
    @Test public void simpleGreetingsDoNotRequireInference() { var p=new LocalCommandParser();assertEquals(LocalCommandParser.Action.GREETING,p.parse("Olá, Harumi").action());assertEquals(LocalCommandParser.Action.GREETING,p.parse("Oi, Rarumi!").action());assertEquals(LocalCommandParser.Action.CHAT,p.parse("Olá, o que você faz?").action()); }
}

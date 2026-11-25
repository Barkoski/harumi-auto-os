package com.harumi.autoos.voice;
import org.junit.Test;
import static org.junit.Assert.*;
public class SpeechUtteranceTest {
 @Test public void joinsSegmentsInsteadOfSubmittingFirstChunk(){SpeechUtterance u=new SpeechUtterance();u.segment("harumi trace uma rota");u.partial("de rondonópolis");assertEquals("harumi trace uma rota de rondonópolis",u.text());u.segment("de rondonópolis para londrina");assertEquals("harumi trace uma rota de rondonópolis para londrina",u.text());}
 @Test public void partialHypothesesReplaceRatherThanDuplicate(){SpeechUtterance u=new SpeechUtterance();u.partial("como");u.partial("como você está");u.segment("como você está hoje");u.partial("");assertEquals("como você está hoje",u.text());}
 @Test public void resetDoesNotLeakIntoNextUtterance(){SpeechUtterance u=new SpeechUtterance();u.segment("primeira frase");u.reset();u.partial("segunda frase");assertEquals("segunda frase",u.text());}
}

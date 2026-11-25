package com.harumi.autoos.voice;
import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;
import static org.junit.Assert.*;
public class SentenceSplitterTest {
    @Test public void sentencesArrivingInPieces() {
        SentenceSplitter s=new SentenceSplitter();
        assertEquals(Collections.emptyList(),s.feed("Olá, Lucas"));
        assertEquals(Collections.emptyList(),s.feed("Olá, Lucas!"));
        assertEquals(Arrays.asList("Olá, Lucas!"),s.feed("Olá, Lucas! Tudo"));
        assertEquals(Collections.emptyList(),s.feed("Olá, Lucas! Tudo bem?"));
        assertEquals(Arrays.asList("Tudo bem?"),s.feed("Olá, Lucas! Tudo bem? Estou aqui."));
        assertEquals("Estou aqui.",s.flush());
    }
    @Test public void severalSentencesInOneChunk() {
        SentenceSplitter s=new SentenceSplitter();
        assertEquals(Arrays.asList("Um.","Dois!","Três?"),s.feed("Um. Dois! Três? Quatro"));
        assertEquals("Quatro",s.flush());
    }
    @Test public void decimalAndThousandsAreNotBoundaries() {
        SentenceSplitter s=new SentenceSplitter();
        assertTrue(s.feed("A versão 2.").isEmpty());
        assertTrue(s.feed("A versão 2.0 custa 1.500 reais").isEmpty());
        assertEquals(Arrays.asList("A versão 2.0 custa 1.500 reais."),s.feed("A versão 2.0 custa 1.500 reais. Fim"));
    }
    @Test public void listItemNumberIsNotBoundary() {
        SentenceSplitter s=new SentenceSplitter();
        assertEquals(Arrays.asList("1. Verifique o óleo."),s.feed("1. Verifique o óleo. 2. Confira"));
        assertEquals(Arrays.asList("2. Confira os pneus."),s.feed("1. Verifique o óleo. 2. Confira os pneus.\n3. Pronto"));
        assertEquals("3. Pronto",s.flush());
    }
    @Test public void abbreviationAndEllipsis() {
        SentenceSplitter s=new SentenceSplitter();
        assertEquals(Arrays.asList("Veja o Dr. Silva hoje.","Talvez...","depois.","Certo…"),s.feed("Veja o Dr. Silva hoje. Talvez... depois. Certo… Ok"));
    }
    @Test public void flushReturnsRestOnlyWithLetters() {
        SentenceSplitter s=new SentenceSplitter();
        s.feed("Pronto. ");
        assertEquals("",s.flush());
        SentenceSplitter t=new SentenceSplitter();
        t.feed("Sem pontuação final");
        assertEquals("Sem pontuação final",t.flush());
        assertEquals("",t.flush());
        SentenceSplitter u=new SentenceSplitter();
        u.feed("Ok! 3");
        assertEquals("",u.flush());
    }
    @Test public void endOfTextSentenceWaitsForFlush() {
        SentenceSplitter s=new SentenceSplitter();
        assertTrue(s.feed("Tudo certo.").isEmpty());
        assertEquals("Tudo certo.",s.flush());
    }
}

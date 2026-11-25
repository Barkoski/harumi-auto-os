package com.harumi.autoos.ai;
import org.junit.Test;
import static org.junit.Assert.*;
public class ModelOutputTest {
    @Test public void interruptedReasoningIsNotAnAnswer(){assertEquals("",ModelOutput.clean("<think>unfinished internal reasoning"));}
    @Test public void preservesOnlyPublicReply(){assertEquals("Olá!",ModelOutput.clean("<think>private</think> Olá!<|im_end|>"));}
    @org.junit.Test public void detectsTheReportedDanglingEnding(){org.junit.Assert.assertTrue(ModelOutput.looksUnfinished("Olá! Tudo bem? Como posso ajudar com"));org.junit.Assert.assertTrue(ModelOutput.looksUnfinished("Você pode ir para"));org.junit.Assert.assertFalse(ModelOutput.looksUnfinished("Posso ajudar com uma rota."));org.junit.Assert.assertFalse(ModelOutput.looksUnfinished("Estou por aqui"));}
    @Test public void lastSentenceIgnoresDecimalPoint(){assertEquals("O motor 2.0 é forte.",ModelOutput.lastSentence("O motor 2.0 é forte. Ele tem"));}
    @Test public void lastSentenceIgnoresThousandsSeparator(){assertEquals("Custa R$ 1.500 no total.",ModelOutput.lastSentence("Custa R$ 1.500 no total. E"));}
    @Test public void lastSentenceIgnoresListNumbers(){assertEquals("1. Verifique o óleo.",ModelOutput.lastSentence("1. Verifique o óleo. 2. Calibre"));}
    @Test public void lastSentenceWithoutTerminatorIsEmpty(){assertEquals("",ModelOutput.lastSentence("Sem ponto final"));assertEquals("",ModelOutput.lastSentence(null));}
    @Test public void lastSentenceKeepsCompleteText(){assertEquals("Tudo certo com o carro.",ModelOutput.lastSentence("  Tudo certo com o carro.  "));}
    @Test public void lastSentenceAcceptsQuestionAndExclamation(){assertEquals("Tudo bem?",ModelOutput.lastSentence("Tudo bem? Posso aj"));assertEquals("Cuidado!",ModelOutput.lastSentence("Cuidado! Reduza a vel"));}
    @Test public void lastSentenceIgnoresAbbreviation(){assertEquals("Leve água, lanche etc. para a viagem.",ModelOutput.lastSentence("Leve água, lanche etc. para a viagem. Depois"));assertEquals("Fale com o Dr. Silva hoje.",ModelOutput.lastSentence("Fale com o Dr. Silva hoje. Depois"));}
    @Test public void cleanRemovesEmoji(){assertEquals("Boa viagem, Lucas! Dirija com calma.",ModelOutput.clean("Boa viagem, Lucas! 🚗💨 Dirija com calma. ☀️"));assertEquals("Curitiba fica no Paraná.",ModelOutput.clean("Curitiba fica no Paraná. 🇧🇷"));}
    @Test public void lastSentenceAcceptsEllipsisAndClosingQuote(){assertEquals("Ele disse \"vamos.\"",ModelOutput.lastSentence("Ele disse \"vamos.\" Depois"));assertEquals("Bom...",ModelOutput.lastSentence("Bom... e en"));}
}

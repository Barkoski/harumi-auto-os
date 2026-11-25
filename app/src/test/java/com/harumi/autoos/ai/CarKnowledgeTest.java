package com.harumi.autoos.ai;
import org.junit.Test;
import static org.junit.Assert.*;
import java.nio.file.*;
public class CarKnowledgeTest {
    private static void topic(String question,String id){String a=CarKnowledge.answer(question);assertEquals(question,CarKnowledge.fixedAnswers().get("kb_"+id),a);}
    @Test public void benchmarkQuestionsGetCheckedAnswers(){
        topic("Me dê uma dica para economizar combustível.","economia");
        topic("Explique em poucas palavras o que é um motor boxer.","boxer");
        topic("Qual óleo do motor eu uso?","oleo_motor");
        topic("Quantos litros de óleo vai no câmbio?","oleo_cambio");
        topic("A luz do óleo acendeu com o motor ligado","luz_oleo");
        topic("A luz da injeção está piscando","luz_injecao");
        topic("Quando trocar a correia dentada?","correia");
        topic("Qual vela eu uso?","velas");
        topic("O ELM327 funciona no meu carro?","scanner");
        topic("O carro trepida nas curvas fechadas","trepida");
        topic("Está chovendo muito, alguma dica?","chuva");
        topic("Estou com sono","sono");
        topic("Furou o pneu, e agora?","pneu_furado");
        topic("Quantos cavalos tem o meu carro?","ficha");
    }
    @Test public void faultCodes(){
        assertEquals("No motor do seu Impreza, o código 23 indica o medidor de massa de ar, o MAF.",CarKnowledge.answer("O que é o código 23?"));
        assertTrue(CarKnowledge.answer("código de falha 14").contains("fonte só"));
        assertEquals("No câmbio automático, o código 24 indica o solenoide Duty C, da tração integral.",CarKnowledge.answer("código 24 do câmbio"));
        assertTrue(CarKnowledge.answer("código 99").startsWith("Não tenho o código 99"));
    }
    @Test public void leavesOtherQuestionsToTheModel(){
        for(String s:new String[]{"Qual a capital do Paraná?","Quanto é 15 vezes 12?","Me conte uma piada","O que tem para fazer em Curitiba?",null})assertNull(s,CarKnowledge.answer(s));
    }
    @Test public void parserUsesKnowledgeButCommandsWin(){
        LocalCommandParser p=new LocalCommandParser();
        assertEquals(LocalCommandParser.Action.QUICK_REPLY,p.parse("Harumi, me dê uma dica para economizar combustível").action());
        assertEquals(LocalCommandParser.Action.DIAGNOSTICS,p.parse("Como está o carro?").action());
        assertEquals(LocalCommandParser.Action.CHAT,p.parse("Qual a capital do Paraná?").action());
    }
    @Test public void answersAreShortCompleteAndClean(){
        for(var e:CarKnowledge.fixedAnswers().entrySet()){String a=e.getValue();
            assertTrue(e.getKey(),a.endsWith("."));assertTrue(e.getKey(),a.length()<=330);
            assertTrue(e.getKey(),a.split("[.!?](?:\\s|$)").length<=3);
            assertEquals(e.getKey(),a,ModelOutput.clean(a));}
    }
    @Test public void everyFixedAnswerHasCachedVoice() throws Exception {
        Path dir=Paths.get("src/main/assets/voice-cache");String manifest=new String(Files.readAllBytes(dir.resolve("manifest.json")),"UTF-8");
        for(String id:CarKnowledge.fixedAnswers().keySet()){assertTrue(id,Files.exists(dir.resolve(id+".f32")));assertTrue(id,manifest.contains("\""+id+"\""));}
    }
}

package com.harumi.autoos.ai;
import org.junit.Test;
import static org.junit.Assert.*;
public class QuickRepliesTest {
    @Test public void wellbeingNeverNeedsLlm(){for(String s:new String[]{"Harumi, tudo bem?","Oi harumi, tudo bem? oi harumi, tudo bem?","Como você está?","Rarumi, boa noite!","Você tá bem?"}){assertNotNull(s,QuickReplies.reply(s));assertEquals(LocalCommandParser.Action.QUICK_REPLY,new LocalCommandParser().parse(s).action());}}
    @Test public void extraRequestIsNotSwallowed(){for(String s:new String[]{"Oi, trace uma rota para Curitiba","Tudo bem, o que fazer em Londrina?","Como está o carro?","Obrigado, mas abra o mapa","Qual a história desta cidade?"})assertNull(s,QuickReplies.reply(s));}
    @Test public void noPersonalHealthClaim(){assertFalse(QuickReplies.reply("tudo bem?").contains("carro"));assertNull(QuickReplies.reply(null));}
    @Test public void greetingKeepsApprovedPresentation(){assertEquals(LocalCommandParser.Action.GREETING,new LocalCommandParser().parse("Olá, Harumi").action());}
}

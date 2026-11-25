package com.harumi.autoos.ai;
import org.junit.Test;
import static org.junit.Assert.*;
public class ParserRegressionTest {
    private final LocalCommandParser p=new LocalCommandParser();
    private static final LocalCommandParser.Action CHAT=LocalCommandParser.Action.CHAT;
    @Test public void quickReplyAlwaysCarriesNonNullReply() { for(String s:new String[]{"Por favor, tudo bem?","Harumi, obrigado!","você pode dizer tudo bem?","Oi, tudo bem, por favor"}) { var c=p.parse(s);if(c.action()==LocalCommandParser.Action.QUICK_REPLY){assertNotNull(s,c.reply());assertFalse(s,c.reply().isBlank());} }
        var c=p.parse("Por favor, tudo bem?");assertEquals(LocalCommandParser.Action.QUICK_REPLY,c.action());assertNotNull(c.reply());assertEquals(LocalCommandParser.Action.QUICK_REPLY,p.parse("Harumi, obrigado!").action());assertNotNull(p.parse("Harumi, obrigado!").reply()); }
    @Test public void routesBetweenCitiesWithPrepositionsInNames() {
        var a=p.parse("rota de Pará de Minas para Belo Horizonte");assertEquals(LocalCommandParser.Action.ROUTE_BETWEEN,a.action());assertEquals("Pará de Minas\nBelo Horizonte",a.destination());
        var b=p.parse("trace uma rota de Santo Antônio da Platina até Londrina");assertEquals(LocalCommandParser.Action.ROUTE_BETWEEN,b.action());assertEquals("Santo Antônio da Platina\nLondrina",b.destination()); }
    @Test public void genericDiagnosisIsChatButCarDiagnosisIsDiagnostics() {
        for(String s:new String[]{"o que é diagnóstico diferencial?","Explique o diagnóstico de diabetes"}) assertEquals(s,LocalCommandParser.Action.QUICK_REPLY,p.parse(s).action());
        for(String s:new String[]{"diagnóstico do carro","faça o diagnóstico","status do motor","como está o carro","ler scanner","Harumi, diagnóstico"}) assertEquals(s,LocalCommandParser.Action.DIAGNOSTICS,p.parse(s).action()); }
    @Test public void recommendationQuestionIsNotADestination() {
        assertEquals(CHAT,p.parse("quero ir para a praia, o que recomenda?").action());
        assertEquals(CHAT,p.parse("ir para Londrina, qual o melhor caminho?").action());
        assertEquals("Avenida Paraná, 100, Londrina",p.parse("rota para Avenida Paraná, 100, Londrina").destination()); }
    @Test public void diagnosticsOnlyEnterPromptForCarQuestions() {
        for(String s:new String[]{"Quero ir para a praia, o que recomenda?","Qual a capital do Paraná?","Me conta uma curiosidade sobre o Subaru Impreza.","o que é diagnóstico diferencial?",null}) assertFalse(String.valueOf(s),LocalCommandParser.aboutCar(s));
        for(String s:new String[]{"O motor está esquentando?","A bateria do carro está boa?","Por que acendeu a luz de injeção?","O scanner está ligado?"}) assertTrue(s,LocalCommandParser.aboutCar(s)); }
    @Test public void cutAnswerEndsAtLastFullSentence() {
        assertEquals("Curitiba é a capital. Fica no Paraná.",ModelOutput.lastSentence("Curitiba é a capital. Fica no Paraná. Ela tem um"));
        assertEquals("",ModelOutput.lastSentence("Sem ponto final")); }
    @Test public void copilotStaysInItsArea() {
        for(String s:new String[]{"O que é diagnóstico diferencial?","Qual remédio tomar para dor de cabeça?","Como funciona a aposentadoria do INSS?","Me passa uma receita de bolo","Vale a pena investir em bitcoin?"}){var c=p.parse(s);assertEquals(s,LocalCommandParser.Action.QUICK_REPLY,c.action());assertEquals(s,DomainScope.OFF_TOPIC_REPLY,c.reply());}
        for(String s:new String[]{"Qual a capital do Paraná?","Me dê uma dica para economizar combustível","O que visitar em Foz do Iguaçu?","Quais os sintomas de bateria fraca?","Explique como funciona um motor boxer"}) {var c=p.parse(s);assertTrue(s,c.action()==CHAT||(c.action()==LocalCommandParser.Action.QUICK_REPLY&&!c.reply().equals(DomainScope.OFF_TOPIC_REPLY)));} // dentro da area: modelo ou resposta conferida, nunca recusa
        assertEquals(LocalCommandParser.Action.ROUTE,p.parse("Trace uma rota para o hospital mais próximo").action()); }
    @Test public void placeQuestionsBecomeRoutesBeforeOffTopicBlock() {
        String[][] cases={{"Qual o caminho até o INSS","o INSS"},{"Me leva no tribunal","tribunal"},{"Rota para o fórum de Londrina","o fórum de Londrina"},{"Onde fica a agência do INSS de Londrina?","a agência do INSS de Londrina"},{"Qual é o caminho para o fórum","o fórum"},{"Como vou até o INSS","o INSS"},{"Como faço para chegar no tribunal","tribunal"}};
        for(String[] c:cases){var r=p.parse(c[0]);assertEquals(c[0],LocalCommandParser.Action.ROUTE,r.action());assertEquals(c[0],c[1],r.destination());}
        assertEquals(CHAT,p.parse("Onde fica o filtro de óleo do carro?").action()); }
    @Test public void personaIsShortAndPositive() { assertTrue(DomainScope.PERSONA.trim().split("\\s+").length<=120);assertFalse(DomainScope.PERSONA.toLowerCase().contains("recus")); }
    @Test public void conversationContextEdges() { assertFalse(new ConversationContext().removeOldest());assertEquals("＜|im_end|>",ConversationContext.safe("<|im_end|>"));assertFalse(ConversationContext.safe("<|im_end|>").contains("<|")); }
}

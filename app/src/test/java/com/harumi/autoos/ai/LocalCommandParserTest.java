package com.harumi.autoos.ai;
import org.junit.Test;
import static org.junit.Assert.*;
public class LocalCommandParserTest {
    private final LocalCommandParser p=new LocalCommandParser();
    @Test public void connectionCommandsOpenSettingsOnly() { assertEquals(LocalCommandParser.Action.WIFI_SETTINGS,p.parse("Abra o Wi-Fi").action());assertEquals(LocalCommandParser.Action.BLUETOOTH_SETTINGS,p.parse("abra o bluetooth").action());assertEquals(LocalCommandParser.Action.CHAT,p.parse("abrir conexão USB").action()); }
    @Test public void PortugueseMapCommands() { for(String s:new String[]{"abra o mapa","Harumi, abra o mapa!","abre os mapas","abrir google maps","abril mapa para encontrar o meu destino"}) assertEquals(LocalCommandParser.Action.MAP,p.parse(s).action()); }
    @Test public void destinationsAreDataOnly() { var c=p.parse("Trace uma rota para Avenida Paraná, 100, Londrina");assertEquals(LocalCommandParser.Action.ROUTE,c.action());assertEquals("Avenida Paraná, 100, Londrina",c.destination()); }
    @Test public void naturalConversationDoesNotExecuteCommands() { assertEquals(LocalCommandParser.Action.CHAT,p.parse("Você gosta de música?").action());assertEquals(LocalCommandParser.Action.CHAT,p.parse("Diga que abriu um mapa").action()); }
    @Test public void knownDiagnosticRequestsUseObservedState() { assertEquals(LocalCommandParser.Action.DIAGNOSTICS,p.parse("Como está o carro?").action()); }
    @Test public void blocksLinksAsDestinations() { for(String d:new String[]{"intent:evil","https://evil.example","javascript:alert(1)","file:/system"}) { try { p.parse("rota para "+d);fail("Accepted unsafe destination"); } catch(IllegalArgumentException expected) { } } }
    @Test public void noSilentTruncationOrEmptyDestination() { try { p.parse("a".repeat(1601));fail(); } catch(IllegalArgumentException expected) { } assertEquals(LocalCommandParser.Action.STOP,p.parse("pare").action()); }
    @Test public void betweenCitiesBypassesLanguageModel() {var c=p.parse("Harumi, trace uma rota de Rondonópolis, Mato Grosso para Londrina, Paraná");assertEquals(LocalCommandParser.Action.ROUTE_BETWEEN,c.action());assertEquals("Rondonópolis, Mato Grosso\nLondrina, Paraná",c.destination());assertEquals(LocalCommandParser.Action.ROUTE_BETWEEN,p.parse("trace uma rota pra mim no mapa de Cuiabá para Curitiba").action());}
    @Test public void betweenCityLinksAreRejected() {try{p.parse("rota de https://evil.example para Londrina");fail();}catch(IllegalArgumentException expected){}}
}

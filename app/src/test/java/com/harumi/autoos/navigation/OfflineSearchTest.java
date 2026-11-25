package com.harumi.autoos.navigation;
import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.Test;

public class OfflineSearchTest {
    @Test public void normalizeRemoveAcentoCaixaEPontuacao() {
        assertEquals("sao joao d oeste", OfflineSearch.normalize("  São João d'Oeste "));
        assertEquals("br 369", OfflineSearch.normalize("BR-369"));
        assertEquals("rondonopolis", OfflineSearch.normalize("Rondonópolis"));
        assertEquals("", OfflineSearch.normalize(null));
        assertEquals("", OfflineSearch.normalize(" -- "));
    }

    @Test public void tokensRemovemPreposicoes() {
        assertEquals(Arrays.asList("catedral", "londrina"), OfflineSearch.tokens("Catedral de Londrina"));
        assertEquals(Arrays.asList("posto", "ipiranga", "cambe"), OfflineSearch.tokens("Posto Ipiranga Cambé"));
        assertTrue(OfflineSearch.tokens("de da").isEmpty());
    }

    @Test public void buildMatchUsaPrefixoNoUltimoTermoEColunaDeCidade() {
        assertEquals("city:londrina rua sergipe*", OfflineSearch.buildMatch(Collections.singletonList("londrina"), Arrays.asList("rua", "sergipe")));
        assertEquals("city:sao city:paulo rua*", OfflineSearch.buildMatch(Arrays.asList("sao", "paulo"), Collections.singletonList("rua")));
        assertEquals("curitiba*", OfflineSearch.buildMatch(null, Collections.singletonList("curitiba")));
        assertEquals("", OfflineSearch.buildMatch(null, Collections.<String>emptyList()));
    }

    @Test public void sufixosDeCidadeDeixamAoMenosUmTermo() {
        List<List<String>> s = OfflineSearch.citySuffixes(Arrays.asList("rua", "sergipe", "nova", "londrina"));
        assertEquals(Arrays.asList("sergipe", "nova", "londrina"), s.get(0));
        assertEquals(Collections.singletonList("londrina"), s.get(2));
        assertTrue(OfflineSearch.citySuffixes(Collections.singletonList("curitiba")).isEmpty());
        assertEquals(1, OfflineSearch.citySuffixes(Arrays.asList("hotel", "londrina")).size());
    }

    @Test public void ufReconhecida() {
        assertTrue(OfflineSearch.isUf("pr"));
        assertFalse(OfflineSearch.isUf("rua"));
        assertFalse(OfflineSearch.isUf(null));
    }

    @Test public void nomeExatoVenceNomeParcial() {
        List<String> t = Collections.singletonList("curitiba");
        double exato = OfflineSearch.score("curitiba", t, "curitiba", 95, null);
        double parcial = OfflineSearch.score("curitiba", t, "curitibanos", 88, null);
        assertTrue(exato > parcial);
    }

    @Test public void proximidadeDesempataMesmoNome() {
        List<String> t = Arrays.asList("rua", "sergipe");
        double perto = OfflineSearch.score("rua sergipe", t, "rua sergipe", 33, 2.0);
        double longe = OfflineSearch.score("rua sergipe", t, "rua sergipe", 33, 600.0);
        assertTrue(perto > longe);
    }

    @Test public void distanciaAproximada() {
        assertEquals(111.0, OfflineSearch.distKm(-23.0, -51.0, -24.0, -51.0), 0.5);
        assertEquals(0.0, OfflineSearch.distKm(-23.3, -51.1, -23.3, -51.1), 1e-9);
    }

    @Test public void nomeDescritivoPorTipo() {
        assertEquals("Catedral Metropolitana \u2014 Londrina, PR", OfflineSearch.displayName("Catedral Metropolitana", "igreja", "Londrina", "PR"));
        assertEquals("Rua Sergipe, Londrina - PR", OfflineSearch.displayName("Rua Sergipe", "rua", "Londrina", "PR"));
        assertEquals("Curitiba - PR", OfflineSearch.displayName("Curitiba", "cidade", "Curitiba", "PR"));
        assertEquals("Paraná", OfflineSearch.displayName("Paraná", "estado", "", "PR"));
        assertEquals("Posto X", OfflineSearch.displayName("Posto X", "posto", "", ""));
    }

    @Test public void jsonEscapaAspasBarraEControle() {
        assertEquals("\"a\\\"b\\\\c\\u000a\"", OfflineSearch.jsonString("a\"b\\c\n"));
    }
}

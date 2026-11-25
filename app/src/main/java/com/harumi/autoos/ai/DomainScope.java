package com.harumi.autoos.ai;
import java.text.Normalizer;
import java.util.Locale;
import java.util.regex.Pattern;
/**
 * Ficha da Harumi: copiloto de estrada. Define a area de atuacao do modelo e barra localmente
 * assuntos claramente fora dela (o modelo de 0,8B nao recusa de forma confiavel sozinho).
 */
public final class DomainScope {
    private DomainScope() { }
    // Instrucoes positivas: o 0,8B recusava assuntos validos quando o prompt mandava recusar. Fora da area e barrado antes, em offTopicReply.
    public static final String PERSONA =
        "Você é Harumi, copiloto de Lucas no Subaru Impreza dele. Fale em português, de forma simpática e prática. "
        + "Você ajuda com: dicas de direção e economia de combustível, segurança, manutenção e funcionamento do carro, "
        + "estradas, rotas, viagens, cidades e pontos turísticos do Brasil, paradas e abastecimento, música e apps. "
        + "Sempre responda a esses assuntos com dicas úteis. "
        + "Use no máximo três frases curtas e termine sempre a última. "
        + "Não invente números, nomes, datas, leituras do carro ou rotas. "
        + "Sobre lugares, use só conhecimento geral e sugira conferir no mapa. "
        + "Não fale do diagnóstico se não perguntarem. Nunca use emojis.";
    public static final String OFF_TOPIC_REPLY =
        "Esse assunto fica fora da minha área. Sou sua copiloto: posso ajudar com o carro, a estrada, rotas, viagem, pontos turísticos e música.";
    // Termos claramente fora do contexto de carro/estrada (texto ja sem acentos e em minusculas).
    private static final Pattern OFF_TOPIC = Pattern.compile("(?s).*\\b(?:"
        + "medicina|doencas?|remedios?|medicamentos?|diagnostico (?:diferencial|medico|clinico|de (?:cancer|diabetes|depressao|doenca))|"
        + "cancer|diabetes|depressao|ansiedade|gravidez|gravida|vacinas?|cirurgia|exame de sangue|consulta medica|"
        + "advogad[oa]s?|juridic[oa]|jurisprudencia|processo judicial|peticao|sentenca|tribunal|inss|aposentadoria|direito (?:civil|penal|previdenciario|trabalhista)|"
        + "politica|eleicao|eleicoes|deputad[oa]|senador[a]?|partido politico|"
        + "investimentos?|bitcoin|criptomoedas?|bolsa de valores|acoes da bolsa|imposto de renda|"
        + "programacao|codigo (?:em|de) (?:python|java|javascript)|python|javascript|"
        + "receita de|como cozinhar|culinaria|"
        + "religiao|horoscopo|signo"
        + ")\\b.*");
    static String normalize(String raw) {
        return Normalizer.normalize(raw == null ? "" : raw, Normalizer.Form.NFD).replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT);
    }
    /** Resposta fixa para assunto fora da area, ou null se a pergunta pode seguir. */
    public static String offTopicReply(String raw) {
        return OFF_TOPIC.matcher(normalize(raw)).matches() ? OFF_TOPIC_REPLY : null;
    }
}

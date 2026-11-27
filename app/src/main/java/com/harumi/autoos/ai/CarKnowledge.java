package com.harumi.autoos.ai;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
/**
 * Respostas conferidas sobre o carro e a estrada, usadas antes do modelo local (o 0,8B inventa fatos).
 * Dados do Impreza: docs/subaru/BASE-IMPREZA-1993-EJ18.md. Item com uma fonte so e dito como "provavel" ou "confira".
 * Cada resposta fixa tem voz pre-gravada (scripts/prepare_voice_cache.py le os textos deste arquivo; id kb_<chave>).
 */
public final class CarKnowledge {
    private CarKnowledge() { }
    private record Entry(String id, Pattern pattern, String answer) { }
    private static Entry K(String id, String regex, String answer) { return new Entry(id, Pattern.compile("(?s).*(?:" + regex + ").*"), answer); }
    // Ordem importa: o primeiro que casar responde. Texto ja sem acentos e em minusculas.
    private static final Entry[] ENTRIES = {
        K("ficha_mt2026", "\\b(?:ficha|dados|especificac\\w*|versao|qual (?:e )?o modelo) d[oe] (?:meu |seu |nosso )?(?:carro|subaru|impreza)|quantos cavalos|potencia d[oe] (?:meu |seu )?(?:carro|motor|subaru|impreza)",
            "Seu Subaru Impreza perua 1993 tem motor EJ18 e agora usa câmbio manual AWD de cinco marchas de um Impreza 1.8 de 1994. Confirme o código gravado na caixa e a relação dos diferenciais antes de comprar peças."),
        K("boxer", "\\bboxer\\b|motor (?:de )?cilindros? (?:deitados|opostos)",
            "No motor boxer os cilindros ficam deitados, dois de cada lado, e os pistões se movem em sentidos opostos. Isso deixa o motor mais baixo e equilibrado, com menos vibração. O seu EJ18 é um boxer de 4 cilindros e 1,8 litro."),
        K("economia", "\\becono\\w* (?:de )?(?:combustivel|gasolina|etanol|alcool)|\\b(?:gastar|gaste|consumir|consuma|gasta|consome) menos (?:combustivel|gasolina)|\\breduzir o consumo|\\bconsumo (?:alto|de combustivel)|\\b(?:dica|dicas) (?:de|para|pra) (?:economi\\w*|consumo)",
            "Acelere com suavidade, mantenha velocidade constante e antecipe as frenagens, aproveitando o embalo. Mantenha os pneus calibrados e não carregue peso à toa. Na estrada, acima de 100 quilômetros por hora o consumo sobe bastante."),
        K("luz_oleo", "\\b(?:luz|lampada)\\b.*\\boleo\\b|\\bpressao (?:do|de) oleo\\b",
            "Luz do óleo acesa com o motor ligado é sinal de parar. Encoste assim que for seguro, desligue o motor e confira o nível na vareta antes de seguir."),
        K("luz_cambio_mt2026", "\\bat oil temp\\b|\\b(?:luz|lampada)\\b.*\\b(?:cambio|power)\\b",
            "Após o swap manual, a luz AT OIL TEMP pode ter fiação ou painel remanescente do automático. Não interpreta temperatura da caixa manual sem verificar a instalação; peça diagnóstico elétrico."),
        K("luz_injecao", "\\b(?:luz|lampada)\\b.*\\b(?:injecao|check engine|motor)\\b|\\bcheck engine\\b",
            "Luz da injeção acesa e fixa: dá para seguir com calma, mas verifique logo. Se ela piscar com o motor andando, é falha grave, provavelmente de ignição: reduza e pare em local seguro."),
        K("diferencial_mt2026", "\\bdiferencia\\w*\\b",
            "O diferencial traseiro tem óleo próprio; confirme tipo, capacidade e eventual autoblocante pela identificação da peça. Confira que as relações dianteira e traseira são compatíveis antes de rodar."),
        K("embreagem_mt2026", "\\b(?:embreagem|plat[o\u00f4]|disco|garfo|rolamento)\\b",
            "Confirme se o acionamento instalado é por cabo ou hidráulico e identifique caixa, volante e conjunto antes de comprar. Patinação, cheiro de queimado ou dificuldade de engate exigem inspeção; não force o carro."),
        K("reboque_mt2026", "\\b(?:reboc\\w*|guinch\\w*|pane|avari\\w*)\\b",
            "Em pane, pare em local seguro e peça guincho plataforma com as quatro rodas apoiadas. Não rebocá-lo com um eixo no chão sem procedimento comprovado para esta transmissão AWD."),
        K("historico_4eat_mt2026", "\\b(?:duty c|fusivel fwd|4eat|atf|dexron|automatico|tcu)\\b",
            "O 4EAT automático é histórico: o carro agora usa câmbio manual AWD. Duty C, fusível FWD, códigos da TCU e ATF não são diagnóstico nem especificação da caixa manual; confirme qualquer fiação remanescente."),
        K("oleo_cambio_mt2026", "\\b(?:oleo|fluido|atf)\\b.*\\b(?:cambio|transmissao|automatico)\\b|\\b(?:cambio|transmissao)\\b.*\\b(?:oleo|fluido)\\b|\\batf\\b",
            "O câmbio manual AWD usa óleo de engrenagens, não ATF. Para a especificação e quantidade exatas, confirme o código da caixa e o manual aplicável; o diferencial dianteiro integra a transmissão em aplicações manuais Subaru, mas confirme nesta caixa."),
        K("oleo_motor_mt2026", "\\boleo\\b.*\\b(?:motor|troca|trocar|qual|quantos? litros?|viscosidade|usar|uso|colocar|cabe)\\b|\\b(?:troca|trocar|qual|quantos? litros?)\\b.*\\boleo\\b",
            "Para o EJ18, confirme viscosidade, classificação e capacidade no manual da variante e conforme o filtro instalado. Confira o nível na vareta, com o carro plano e motor desligado há alguns minutos."),
        K("velas_mt2026", "\\bvelas?\\b(?! de aniversario)",
            "Confirme as velas, a folga e o torque pelo código do motor, aplicação e manual antes de instalar; não tenho esses valores verificados para este carro."),
        K("correia_mt2026", "\\bcorreia (?:dentada|do comando|de comando|da distribuicao)|\\bcorreia\\b.*\\b(?:trocar|troca|quando|romper|rompeu|arrebentar)\\b",
            "Sem histórico confiável da correia dentada, inspecione e planeje a troca conforme o manual da variante, incluindo avaliação dos tensores e polias. Não presuma que a quebra não cause danos."),
        K("marcha_lenta_mt2026", "\\bmarcha lenta\\b|\\blenta (?:oscilando|baixa|alta|irregular)|\\b(?:rotacao|giro) (?:oscila|oscilando|sobe e desce)",
            "Se a marcha lenta oscila, verifique entradas de ar, sensores e sistema de marcha lenta. Confirme a rotação de ajuste no manual da versão e nas condições especificadas."),
        K("temperatura", "\\btemperatura (?:do motor|da agua|normal|ideal|do liquido)|\\b(?:motor|carro) (?:esquentando|esquentou|ferveu|fervendo|superaquec\\w*)|\\bsuperaquec\\w*",
            "Com o motor quente, o normal fica entre 80 e 100 graus. Acima de 105, fique atento; acima de 110, pare em local seguro e desligue o motor. Esses limites são de referência e não do manual do seu carro."),
        K("scanner_mt2026", "\\b(?:elm ?327|obd ?2?|obdii|scanner|leitor de (?:falhas|codigos)|select monitor|ssm)\\b",
            "O Impreza 1993 pode usar diagnóstico Subaru anterior ao OBD-II. Confirme conector, ECU e protocolo instalados antes de comprar um scanner; um leitor OBD-II comum pode não ser compatível."),
        K("piscadas_mt2026", "\\b(?:ler|leitura|ver)\\b.*\\b(?:codigos?|falhas?)\\b.*\\bsem (?:scanner|aparelho)|\\bpiscadas\\b",
            "A leitura de piscadas depende da ECU e dos conectores instalados. Confirme o procedimento no manual da versão antes de conectar qualquer terminal."),
        K("bateria_mt2026", "\\bbateria\\b|\\balternador\\b",
            "Verifique bateria, terminais e sistema de carga com multímetro e compare com o manual da configuração instalada. Uma medição isolada não identifica a peça defeituosa."),
        K("trepida_mt2026", "\\b(?:trepida|trepidando|treme|tremendo|freia sozinho|segura|travando)\\b.*\\bcurvas?\\b|\\bcurvas?\\b.*\\b(?:trepida|trepidando|treme|travando)\\b|\\btorque bind\\b",
            "Em curvas fechadas, trepidação ou travamento no AWD manual exige inspeção de pneus, relações dos diferenciais e transmissão central. Pare de usar se houver esforço forte; não faça o teste de fusível FWD do antigo automático."),
        K("vazamento", "\\b(?:vazamento|vazando|pingando|pinga)\\b.*\\boleo\\b|\\boleo\\b.*\\b(?:vazamento|vazando|pingando|pinga)\\b",
            "No EJ18, os vazamentos mais comuns são nas juntas das tampas de válvulas, nos retentores dianteiros e na placa separadora entre motor e câmbio. Retentores velhos devem ser trocados junto com a correia dentada."),
        K("cambio_tranco_mt2026", "\\b(?:cambio|marcha|marchas)\\b.*\\b(?:tranco|trancos|escorrega|patina|dura|duras|demora)\\b|\\btranco\\b",
            "No câmbio manual, marchas difíceis ou trancos podem envolver embreagem, acionamento, cabos ou trambulador e a própria caixa. Não force os engates; verifique vazamentos e procure diagnóstico mecânico."),
        K("pneus", "\\b(?:calibr\\w*|pressao (?:dos|do) pneus?|libras? (?:do|no|nos) pneus?)\\b",
            "A pressão certa está na etiqueta do carro ou no manual; não tenho esse valor confirmado para o seu Impreza. Calibre com os pneus frios, a cada 15 dias, e um pouco mais quando o carro estiver carregado."),
        K("chuva", "\\b(?:chuva|chovendo|aquaplan\\w*|pista molhada)\\b",
            "Na chuva, reduza a velocidade, dobre a distância do carro da frente e acenda o farol baixo. Se aquaplanar, não freie de repente: tire o pé do acelerador e segure o volante reto até o pneu voltar a aderir."),
        K("neblina", "\\b(?:neblina|cerracao|nevoeiro)\\b",
            "Na neblina, use farol baixo e o de neblina, nunca o farol alto. Reduza a velocidade, aumente a distância e guie-se pela faixa da direita. Se a visibilidade sumir, saia da pista em local seguro e ligue o pisca-alerta."),
        K("sono", "\\b(?:sono|sonolento|cansado|cansaco|dormir no volante|pescando)\\b",
            "Sono ao volante é perigoso. Pare em um local seguro assim que puder, descanse uns 20 minutos e só depois siga. Em viagens longas, faça uma pausa a cada duas horas."),
        K("pneu_furado", "\\bpneu (?:furado|furou|murcho|estourou|estourado)|\\bfurou (?:o |um )?pneu|\\btrocar (?:o )?pneu|\\bestepe\\b",
            "Pare em local plano e seguro, ligue o pisca-alerta e coloque o triângulo bem atrás do carro. Afrouxe os parafusos antes de erguer o carro, troque o pneu e aperte em cruz. Confira a pressão do estepe no próximo posto."),
        K("estrada_longa", "\\b(?:viagem|viajar|estrada) (?:longa|longe)|\\bantes de (?:viajar|pegar a estrada)|\\bpreparar o carro\\b|\\brevisao antes\\b",
            "Antes de pegar a estrada, confira óleo, água do radiador, pneus e estepe, faróis e palhetas. Leve água e o celular carregado. Faça uma pausa a cada duas horas."),
    };
    private static final Pattern CODE = Pattern.compile("(?s).*\\bcodigo (?:de (?:falha|erro|defeito) )?(?:numero )?(\\d{2})\\b.*");
    private static final Pattern GEARBOX = Pattern.compile("(?s).*\\b(?:cambio|transmissao|tcu|automatico)\\b.*");
    // Codigos legados da ECU; confirmar ECU e aplicabilidade depois do swap. true = so uma fonte.
    private static final Object[][] ENGINE = {
        {"11", "o sensor de ângulo do virabrequim", false}, {"12", "o sinal do motor de partida", false}, {"13", "o sensor de posição do comando", false},
        {"14", "o injetor do cilindro 1", true}, {"15", "o injetor do cilindro 2", true}, {"16", "o injetor do cilindro 3", true}, {"17", "o injetor do cilindro 4", true},
        {"21", "o sensor de temperatura do líquido de arrefecimento", false}, {"22", "o sensor de detonação", false}, {"23", "o medidor de massa de ar, o MAF", false},
        {"24", "a válvula de ar da marcha lenta", false}, {"31", "o sensor de posição da borboleta", false}, {"32", "a sonda lambda", false},
        {"33", "o sensor de velocidade do veículo", false}, {"34", "a válvula EGR, que só existe em algumas versões", false}, {"35", "o solenoide de purga do cânister", true},
        {"41", "a correção de mistura fora do limite, mistura pobre ou rica", false}, {"42", "o interruptor de marcha lenta, no sensor da borboleta", false},
        {"45", "o sensor de pressão atmosférica, se o carro tiver", true}, {"49", "o resistor de ajuste de CO", true}, {"51", "o interruptor de neutro do câmbio", true}, {"52", "o interruptor de estacionamento, a posição P", true},
    };
    private static final Object[][] GEAR = {
    };
    /** Resposta conferida, ou null para seguir ao modelo. */
    public static String answer(String raw) {
        if(raw == null || raw.length() > 1600) return null;
        String n = DomainScope.normalize(raw).replaceAll("[,.!?;:]", " ").replaceAll("\\s+", " ").trim();
        Matcher code = CODE.matcher(n);
        if(code.matches()) return codeAnswer(code.group(1), GEARBOX.matcher(n).matches());
        for(Entry e : ENTRIES) if(e.pattern().matcher(n).matches()) return e.answer();
        return null;
    }
    static String codeAnswer(String code, boolean gearbox) {
        if(gearbox) {
            return "A caixa atual é manual AWD; não aplique códigos da TCU 4EAT. Confirme a origem do código " + code + " e a instalação elétrica com um profissional.";
        }
        for(Object[] c : ENGINE) if(c[0].equals(code))
            return "No motor do seu Impreza, o código " + code + " indica " + c[1] + "." + ((Boolean) c[2] ? " Essa informação tem uma fonte só; confirme com o mecânico." : "");
        return "Não tenho o código " + code + " do motor na minha base. Confira com o mecânico.";
    }
    /** Textos fixos com id, para testes e para o gerador de voz. */
    static java.util.Map<String, String> fixedAnswers() {
        java.util.Map<String, String> m = new java.util.LinkedHashMap<>();
        for(Entry e : ENTRIES) m.put("kb_" + e.id().toLowerCase(Locale.ROOT), e.answer());
        return m;
    }
}


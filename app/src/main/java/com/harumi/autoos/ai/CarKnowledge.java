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
        K("ficha", "\\b(?:ficha|dados|especificac\\w*|versao|qual (?:e )?o modelo) d[oe] (?:meu |seu |nosso )?(?:carro|subaru|impreza)|quantos cavalos|potencia d[oe] (?:meu |seu )?(?:carro|motor|subaru|impreza)",
            "Seu carro é um Subaru Impreza perua 1993, provavelmente a versão GF6, com tração integral e câmbio automático de 4 marchas. O motor é o EJ18 boxer, 1,8 litro e 16 válvulas, com cerca de 105 cavalos. Confirme a versão pelo número do chassi."),
        K("boxer", "\\bboxer\\b|motor (?:de )?cilindros? (?:deitados|opostos)",
            "No motor boxer os cilindros ficam deitados, dois de cada lado, e os pistões se movem em sentidos opostos. Isso deixa o motor mais baixo e equilibrado, com menos vibração. O seu EJ18 é um boxer de 4 cilindros e 1,8 litro."),
        K("economia", "\\becono\\w* (?:de )?(?:combustivel|gasolina|etanol|alcool)|\\b(?:gastar|gaste|consumir|consuma|gasta|consome) menos (?:combustivel|gasolina)|\\breduzir o consumo|\\bconsumo (?:alto|de combustivel)|\\b(?:dica|dicas) (?:de|para|pra) (?:economi\\w*|consumo)",
            "Acelere com suavidade, mantenha velocidade constante e antecipe as frenagens, aproveitando o embalo. Mantenha os pneus calibrados e não carregue peso à toa. Na estrada, acima de 100 quilômetros por hora o consumo sobe bastante."),
        K("luz_oleo", "\\b(?:luz|lampada)\\b.*\\boleo\\b|\\bpressao (?:do|de) oleo\\b",
            "Luz do óleo acesa com o motor ligado é sinal de parar. Encoste assim que for seguro, desligue o motor e confira o nível na vareta antes de seguir."),
        K("luz_cambio", "\\bat oil temp\\b|\\b(?:luz|lampada)\\b.*\\b(?:cambio|power)\\b",
            "A luz AT OIL TEMP acesa com o motor ligado indica câmbio quente: pare e deixe esfriar. Se ela piscar logo ao dar a partida, provavelmente há um código de falha gravado no câmbio."),
        K("luz_injecao", "\\b(?:luz|lampada)\\b.*\\b(?:injecao|check engine|motor)\\b|\\bcheck engine\\b",
            "Luz da injeção acesa e fixa: dá para seguir com calma, mas verifique logo. Se ela piscar com o motor andando, é falha grave, provavelmente de ignição: reduza e pare em local seguro."),
        K("oleo_cambio", "\\b(?:oleo|fluido|atf)\\b.*\\b(?:cambio|transmissao|automatico)\\b|\\b(?:cambio|transmissao)\\b.*\\b(?:oleo|fluido)\\b|\\batf\\b",
            "O câmbio automático usa fluido ATF Dexron II, ou o ATF da Subaru compatível. A capacidade total é de cerca de 7,9 litros, mas uma troca pelo dreno tira uns 2,5 litros. Confira o nível com o motor quente, na posição P."),
        K("oleo_motor", "\\boleo\\b.*\\b(?:motor|troca|trocar|qual|quantos? litros?|viscosidade|usar|uso|colocar|cabe)\\b|\\b(?:troca|trocar|qual|quantos? litros?)\\b.*\\boleo\\b",
            "O motor EJ18 leva cerca de 4 litros de óleo. Na época se usava 5W-30 em clima frio, ou 10W-30 e 10W-40. Confira a vareta com o carro no plano e o motor desligado há alguns minutos."),
        K("velas", "\\bvelas?\\b(?! de aniversario)",
            "A vela indicada é a NGK BKR6E-11, com folga de 1,0 a 1,1 milímetro e aperto de 41 a 47 newton-metro. O modelo da vela veio de uma fonte só, então confira a aplicação na loja."),
        K("correia", "\\bcorreia (?:dentada|do comando|de comando|da distribuicao)|\\bcorreia\\b.*\\b(?:trocar|troca|quando|romper|rompeu|arrebentar)\\b",
            "A correia dentada deve ser inspecionada a cada 48 mil quilômetros e trocada a cada 96 mil. Sem registro da última troca, o melhor é trocar já, junto com tensor, polias, retentores e bomba d'água. O EJ18 não é interferente: se romper, o carro para, mas em tese não empena válvula."),
        K("marcha_lenta", "\\bmarcha lenta\\b|\\blenta (?:oscilando|baixa|alta|irregular)|\\b(?:rotacao|giro) (?:oscila|oscilando|sobe e desce)",
            "Com o motor quente, a marcha lenta normal é de 700 rotações, com variação de 100 para mais ou para menos. Com o ar-condicionado ligado, fica perto de 850. Se ela oscilar, a causa comum é a válvula de marcha lenta suja, que pode ser limpa antes de trocar."),
        K("temperatura", "\\btemperatura (?:do motor|da agua|normal|ideal|do liquido)|\\b(?:motor|carro) (?:esquentando|esquentou|ferveu|fervendo|superaquec\\w*)|\\bsuperaquec\\w*",
            "Com o motor quente, o normal fica entre 80 e 100 graus. Acima de 105, fique atento; acima de 110, pare em local seguro e desligue o motor. Esses limites são de referência e não do manual do seu carro."),
        K("scanner", "\\b(?:elm ?327|obd ?2?|obdii|scanner|leitor de (?:falhas|codigos)|select monitor|ssm)\\b",
            "O seu Impreza 1993 é anterior ao OBD-II e usa o protocolo Subaru Select Monitor. Leitor ELM327 comum não funciona. Serve um cabo próprio para Select Monitor, no conector amarelo de 9 pinos."),
        K("piscadas", "\\b(?:ler|leitura|ver)\\b.*\\b(?:codigos?|falhas?)\\b.*\\bsem (?:scanner|aparelho)|\\bpiscadas\\b",
            "Sem scanner, com a ignição ligada e o motor desligado, liga-se o par de plugues pretos de leitura de memória e contam-se as piscadas da luz da injeção. Piscada longa é a dezena e curta é a unidade. A posição desses plugues no seu carro ainda precisa ser confirmada."),
        K("bateria", "\\bbateria\\b|\\balternador\\b",
            "Com o motor ligado, a bateria deve marcar entre 13,5 e 14,5 volts. Abaixo de 12,5 com o motor ligado indica problema no alternador; acima de 15, no regulador."),
        K("trepida", "\\b(?:trepida|trepidando|treme|tremendo|freia sozinho|segura|travando)\\b.*\\bcurvas?\\b|\\bcurvas?\\b.*\\b(?:trepida|trepidando|treme|travando)\\b|\\btorque bind\\b",
            "Trepidar ou travar em curvas fechadas e lentas costuma ser a embreagem da tração integral ou o solenoide Duty C. Um teste é colocar o fusível no soquete FWD do cofre: se o sintoma sumir, o problema está no sistema 4x4."),
        K("vazamento", "\\b(?:vazamento|vazando|pingando|pinga)\\b.*\\boleo\\b|\\boleo\\b.*\\b(?:vazamento|vazando|pingando|pinga)\\b",
            "No EJ18, os vazamentos mais comuns são nas juntas das tampas de válvulas, nos retentores dianteiros e na placa separadora entre motor e câmbio. Retentores velhos devem ser trocados junto com a correia dentada."),
        K("cambio_tranco", "\\b(?:cambio|marcha|marchas)\\b.*\\b(?:tranco|trancos|escorrega|patina|dura|duras|demora)\\b|\\btranco\\b",
            "Trancos ou trocas que escorregam no câmbio automático costumam vir de fluido velho ou de solenoides com defeito. Confira o nível e a cor do fluido, e leia os códigos do câmbio quando o scanner estiver conectado."),
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
    // Codigos de 2 digitos da ECU JECS (base, secao 2.4) e da TCU 4EAT (secao 2.5). true = so uma fonte.
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
        {"11", "o solenoide Duty A, da pressão de linha"}, {"12", "o solenoide Duty B, do travamento do conversor"}, {"13", "o solenoide de troca 3"}, {"14", "o solenoide de troca 2"},
        {"15", "o solenoide de troca 1"}, {"21", "o sensor de temperatura do fluido"}, {"22", "o sensor de pressão atmosférica"}, {"23", "o sinal de rotação do motor"},
        {"24", "o solenoide Duty C, da tração integral"}, {"25", "o sinal de controle de torque"}, {"31", "o sensor da borboleta"}, {"32", "o sensor de velocidade 1"}, {"33", "o sensor de velocidade 2"},
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
            for(Object[] c : GEAR) if(c[0].equals(code)) return "No câmbio automático, o código " + code + " indica " + c[1] + ".";
            return "Não tenho o código " + code + " do câmbio na minha base. Confira com o mecânico.";
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

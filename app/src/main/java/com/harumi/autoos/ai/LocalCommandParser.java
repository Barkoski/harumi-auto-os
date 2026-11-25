package com.harumi.autoos.ai;

import java.text.Normalizer;

import java.util.Locale;

import java.util.regex.*;

public final class LocalCommandParser {

    public enum Action { MAP, MUSIC, ROUTE, ROUTE_BETWEEN, DIAGNOSTICS, GREETING, QUICK_REPLY, WIFI_SETTINGS, BLUETOOTH_SETTINGS, CHAT, STOP }

    public record Command(Action action,String destination,String reply) { public Command(Action action,String destination) { this(action,destination,""); } }

    /** Pergunta livre sobre o carro: so nesse caso o estado do diagnostico entra no prompt do modelo. */
    public static boolean aboutCar(String raw) {
        if(raw==null) return false;
        String n=Normalizer.normalize(raw,Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(Locale.ROOT);
        return n.matches(".*\\b(?:carro|veiculo|motor|scanner|obd2?|ecu|diagnostico do|bateria|oleo|temperatura do|luz de (?:injecao|alerta)|pane|falha no)\\b.*");
    }

    /** Conversa livre: assunto fora da area da copiloto recebe resposta fixa, sem passar pelo modelo. */
    private static Command chat(String raw) {
        String off=DomainScope.offTopicReply(raw);
        if(off!=null) return new Command(Action.QUICK_REPLY,"",off);
        String known=CarKnowledge.answer(raw); // resposta conferida antes do modelo
        return known!=null?new Command(Action.QUICK_REPLY,"",known):new Command(Action.CHAT,"");
    }

    public Command parse(String raw) {

        if(raw==null || raw.length()>1600) throw new IllegalArgumentException("Pedido muito longo.");

        String text=raw.trim().replaceFirst("(?iu)^(?:harumi|rarumi)[, ]+", "").replaceFirst("(?iu)[,.!?]+$", "");

        text=text.replaceFirst("(?iu)^(?:por favor[, ]+|(?:você |voce )?pode )", "").replaceFirst("(?iu)[, ]+por favor$", "");

        String n=Normalizer.normalize(text,Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(Locale.ROOT);

        if(n.matches("(?:oi|ola)(?:,? (?:harumi|rarumi))?")) return new Command(Action.GREETING,"");

        String quick=QuickReplies.reply(text);if(quick!=null)return new Command(Action.QUICK_REPLY,"",quick);

        if(n.matches("(pare|parar|cancele|cancelar|silencio)")) return new Command(Action.STOP,"");

        if(n.matches("(?:abra|abrir|abre|configurar)(?: o| a| as)? (?:wi-?fi|configuracoes de wi-?fi)")) return new Command(Action.WIFI_SETTINGS,"");

        if(n.matches("(?:abra|abrir|abre|configurar)(?: o| a| as)? (?:bluetooth|configuracoes de bluetooth)")) return new Command(Action.BLUETOOTH_SETTINGS,"");

        if(n.matches("(?:abra|abrir|abre|abril)(?: o| os| um| uma)? (?:mapa|mapas|navegador|navegacao|google maps|waze)(?: para (?:encontrar|ver|buscar|procurar).*)?")) return new Command(Action.MAP,"");

        if(n.matches("(?:abra|abrir|abre|toque|tocar)(?: a| o| uma)? (?:musica|radio|spotify)")) return new Command(Action.MUSIC,"");

        if(n.matches(".*(?:temperatura do motor|rotacao do motor|estado do carro|como esta o carro|problema no carro|status do motor|(?:ler|leia|le|use|usar) (?:o )?scanner|diagnostico (?:d[oae]s?|n[oa]) (?:meu |nosso )?(?:carro|veiculo|motor|scanner|obd2?)).*|(?:(?:faca|fazer|faz|realize|rode|inicie|mostre|me de|quero|ver|veja) )?(?:o |um )?diagnostico(?: completo| geral| agora)?")) return new Command(Action.DIAGNOSTICS,"");

        Matcher between=Pattern.compile("(?iu)^(?:me )?(?:(?:trace|traça|traca|tracar|traçar|faça|faca) (?:uma |a )?rota(?: pra mim| para mim)?(?: no mapa)?|rota|navegue) de\\s+(.+?)\\s+(?:para|até|ate)\\s+(.+)$").matcher(text);

        if(between.matches()) {

            String origin=between.group(1).trim(),target=between.group(2).trim();

            for(String place:new String[]{origin,target})if(place.length()<2||place.length()>160||place.matches("(?s).*[\\p{Cntrl}<>].*")||place.matches("(?i).*(?:https?:|intent:|javascript:|file:|geo:).*"))throw new IllegalArgumentException("Informe cidades sem links.");

            return new Command(Action.ROUTE_BETWEEN,origin+"\n"+target);

        }

        Matcher route=Pattern.compile("(?iu)^(?:(?:trace|traça|traca|traz|traçar|tracar) (?:uma |a )?rota para|faça (?:uma |a )?rota para|faca (?:uma |a )?rota para|navegue para|navegar para|me lev[ae] (?:para|pra|pro|até|ate|à|a|no|na|ao)|qual (?:é |e )?o caminho (?:até|ate|para|pro|pra)|onde fica|como vou (?:até|ate|para|pro|pra)|como faço para chegar (?:em|no|na|ao)|como faco para chegar (?:em|no|na|ao)|(?:quero )?ir para|rota para|como chego (?:em|no|na))\\s+(.+)$").matcher(text);

        if(route.matches()) {

            String destination=route.group(1).trim();

            if(destination.length()<2 || destination.length()>160 || destination.matches("(?s).*[\\p{Cntrl}<>].*") || destination.matches("(?i).*(?:https?:|intent:|javascript:|file:|geo:|google\\.navigation:).*")) throw new IllegalArgumentException("Informe um endereço ou nome de local, sem links.");

            String dn=Normalizer.normalize(destination,Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(Locale.ROOT);

            if(dn.matches("(?s).*(?:\\?|[,;]\\s*(?:e\\s+)?(?:o que|qual|quais|como|onde|voce|vc|me\\s+(?:recomend|sugir|indic)|recomend|sugir|alguma|tem\\b)|\\be\\s+(?:o que|qual|quais|como)|\\b(?:recomenda|sugere|indica)\\b).*")) return chat(raw);

            if(text.matches("(?iu)^onde fica\\s.*")&&aboutCar(destination)) return chat(raw);

            return new Command(Action.ROUTE,destination);

        }

        return chat(raw);

    }

}


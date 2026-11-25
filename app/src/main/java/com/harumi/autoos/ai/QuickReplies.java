package com.harumi.autoos.ai;
import java.text.Normalizer;
import java.util.Locale;
/** Exact small-talk only: questions about places, commands and diagnostics always use their real paths. */
public final class QuickReplies {
    private QuickReplies() { }
    public static String reply(String raw) {
        if(raw==null||raw.length()>1600)return null;
        String n=Normalizer.normalize(raw,Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(Locale.ROOT)
            .replaceAll("\\b(?:harumi|rarumi)\\b", " ").replaceAll("[,.!?;:]", " ").replaceAll("\\s+"," ").trim();
        String greeting="(?:oi|ola|bom dia|boa tarde|boa noite)";
        String wellbeing="(?:tudo bem|(?:esta|ta) tudo bem|como (?:vai|voce esta|voce ta)|voce (?:esta|ta) bem)";
        String unit="(?:"+greeting+"(?: "+wellbeing+")?|"+wellbeing+")";
        if(n.matches(unit+"(?: "+unit+"){0,2}"))return "Oi, Lucas! Tudo bem por aqui. E você?";
        if(n.matches("(?:obrigad[oa]|valeu)(?: muito)?"))return "Por nada, Lucas! Estou por aqui.";
        return null;
    }
}

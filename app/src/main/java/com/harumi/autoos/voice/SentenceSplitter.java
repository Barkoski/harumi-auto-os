package com.harumi.autoos.voice;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
/** Entrega, a cada texto acumulado, so as frases completas novas (fala em fluxo enquanto o modelo gera). Uma instancia por resposta; nao e thread-safe. */
public final class SentenceSplitter {
    private static final Set<String> ABBREVIATIONS=new HashSet<>(Arrays.asList("etc","dr","dra","sr","sra","km","p.ex","ex","prof","profa","av","min","máx","mín"));
    private String last="";
    private int consumed;
    /** Frase completa = termina em . ! ? ou reticencias, seguido de espaco/quebra (o fim do texto ainda nao conta: pode vir "2.0"). */
    public List<String> feed(String accumulated) {
        List<String> out=new ArrayList<>();
        if(accumulated==null) return out;
        last=accumulated;
        int n=last.length();
        for(int i=consumed;i<n;i++){
            char c=last.charAt(i);
            if(c!='.'&&c!='!'&&c!='?'&&c!='…') continue;
            int j=i;
            while(j+1<n&&(last.charAt(j+1)=='.'||last.charAt(j+1)=='!'||last.charAt(j+1)=='?'||last.charAt(j+1)=='…')) j++;
            int k=j+1;
            while(k<n&&"\"')]”’»".indexOf(last.charAt(k))>=0) k++;
            boolean single=j==i;int dot=i;i=j;
            if(k>=n||!Character.isWhitespace(last.charAt(k))) continue;
            if(single&&c=='.'&&!isSentenceDot(last,dot)) continue;
            String sentence=last.substring(consumed,k).trim();
            consumed=k;
            if(hasLetter(sentence)) out.add(sentence);
        }
        return out;
    }
    /** Resto ainda nao entregue (ultima frase sem espaco depois, ou texto sem pontuacao); "" se nao houver letras. */
    public String flush() {
        if(consumed>=last.length()) return "";
        String rest=last.substring(consumed).trim();
        consumed=last.length();
        return hasLetter(rest)?rest:"";
    }
    private static boolean hasLetter(String s){for(int i=0;i<s.length();i++)if(Character.isLetter(s.charAt(i)))return true;return false;}
    private static boolean isSentenceDot(String value,int dot){
        int s=dot;
        while(s>0&&!Character.isWhitespace(value.charAt(s-1))) s--;
        String word=value.substring(s,dot).replaceAll("^[\"'(\\[“‘«]+","").toLowerCase(Locale.ROOT);
        if(word.matches("\\d{1,2}")) return false; // "1." de lista (ou "versao 2. Depois"): mesmo criterio de ModelOutput.lastSentence
        return !ABBREVIATIONS.contains(word);
    }
}

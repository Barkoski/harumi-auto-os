package com.harumi.autoos.ai;
public final class ModelOutput {
    private ModelOutput() { }
    public static boolean looksUnfinished(String text){
        String value=text==null?"":text.trim().toLowerCase(java.util.Locale.ROOT);
        return value.matches("(?s).*(?:[,;:]|\\b(?:com|de|para|em|e|que|um|uma|o|a|os|as|se|por))$");
    }
    private static final java.util.Set<String> ABBREVIATIONS=new java.util.HashSet<>(java.util.Arrays.asList("etc","dr","dra","sr","sra","km","p.ex","ex","prof","profa","av","min","máx","mín"));
    /** Corta no fim da ultima frase completa; devolve "" se nao houver nenhuma (o chamador decide o que falar). */
    public static String lastSentence(String text) {
        String value=text==null?"":text.trim();
        int n=value.length(),last=0;
        for(int i=0;i<n;i++){
            char c=value.charAt(i);
            if(c!='.'&&c!='!'&&c!='?') continue;
            int j=i;
            while(j+1<n&&(value.charAt(j+1)=='.'||value.charAt(j+1)=='!'||value.charAt(j+1)=='?')) j++;
            int k=j+1;
            while(k<n&&"\"')]”’»".indexOf(value.charAt(k))>=0) k++;
            boolean boundary=k>=n||Character.isWhitespace(value.charAt(k));
            if(boundary&&j==i&&c=='.'&&!isSentenceDot(value,i,k)) boundary=false;
            if(boundary) last=k;
            i=j;
        }
        return value.substring(0,last).trim();
    }
    private static boolean isSentenceDot(String value,int dot,int after){
        int s=dot;
        while(s>0&&!Character.isWhitespace(value.charAt(s-1))) s--;
        String word=value.substring(s,dot).replaceAll("^[\"'(\\[“‘«]+","").toLowerCase(java.util.Locale.ROOT);
        if(word.matches("\\d{1,2}")){
            boolean lineStart=true;
            for(int p=s-1;p>=0&&value.charAt(p)!='\n';p--) if(!Character.isWhitespace(value.charAt(p))){lineStart=false;break;}
            if(lineStart||after<value.length()) return false;
        }
        return after>=value.length()||!ABBREVIATIONS.contains(word);
    }
    // Emoji proibido na Harumi (decisao do Lucas): pictogramas, simbolos, bandeiras, seletores de variacao e juntores.
    private static final java.util.regex.Pattern EMOJI=java.util.regex.Pattern.compile("[\\x{1F000}-\\x{1FAFF}\\x{2600}-\\x{27BF}\\x{2B00}-\\x{2BFF}\\x{1F1E6}-\\x{1F1FF}\\x{FE0E}\\x{FE0F}\\x{200D}\\x{20E3}]");
    public static String clean(String value) {
        return EMOJI.matcher(value.replaceAll("(?is)<think>.*?(?:</think>|$)","").replaceAll("<\\|[^>]*\\|>","")).replaceAll("").replaceAll("[ \\t]{2,}"," ").trim();
    }
}

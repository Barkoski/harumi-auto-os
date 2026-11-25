package com.harumi.autoos.ai.tools;
import java.util.Set;
/** Esquema de um slot: STRING (tamanho max), INT (faixa) ou ENUM (valores permitidos). Todos obrigatorios. */
public record SlotSpec(Type type,int min,int max,Set<String> values) {
    public enum Type { STRING, INT, ENUM }
    public static SlotSpec string(int maxLen) { return new SlotSpec(Type.STRING,1,maxLen,Set.of()); }
    public static SlotSpec integer(int min,int max) { return new SlotSpec(Type.INT,min,max,Set.of()); }
    public static SlotSpec enumOf(String... v) { return new SlotSpec(Type.ENUM,0,0,Set.of(v)); }
    /** Devolve motivo da rejeicao ou null se o valor e valido. */
    public String check(String name,String v) {
        if(v==null) return "slot '"+name+"' nulo";
        switch(type) {
            case STRING:
                if(v.length()<min||v.length()>max) return "slot '"+name+"' fora do tamanho "+min+".."+max;
                if(v.matches("(?s).*[\\p{Cntrl}<>].*")) return "slot '"+name+"' com caracteres proibidos";
                if(v.matches("(?is).*(?:https?:|intent:|javascript:|file:|geo:|google\\.navigation:).*")) return "slot '"+name+"' com link/esquema proibido";
                return null;
            case INT:
                try { int i=Integer.parseInt(v); return i<min||i>max?"slot '"+name+"' fora da faixa "+min+".."+max:null; }
                catch(NumberFormatException e) { return "slot '"+name+"' nao e inteiro"; }
            default:
                return values.contains(v)?null:"slot '"+name+"' fora dos valores permitidos";
        }
    }
}

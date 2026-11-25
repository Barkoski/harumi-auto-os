package com.harumi.autoos.ai;
import java.util.ArrayDeque;
public final class ConversationContext {
    private final ArrayDeque<String> turns=new ArrayDeque<>();
    public static String safe(String text){return text.replace("<|","＜|");}
    public void add(String question,String answer){turns.addLast("<|im_start|>user\n"+safe(question)+"<|im_end|>\n<|im_start|>assistant\n"+safe(answer)+"<|im_end|>\n");while(turns.size()>3||characters()>3200)turns.removeFirst();}
    public String prompt(){return String.join("",turns);}
    private int characters(){return turns.stream().mapToInt(String::length).sum();}
    public boolean removeOldest(){if(turns.isEmpty())return false;turns.removeFirst();return true;}
    public void clear(){turns.clear();}
}

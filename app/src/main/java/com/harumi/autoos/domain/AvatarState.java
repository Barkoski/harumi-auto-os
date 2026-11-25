package com.harumi.autoos.domain;
import java.util.Locale;
public final class AvatarState {
    private AvatarState() { }
    public static String from(String status,boolean busy) {
        if(!busy)return "idle";
        String text=status==null?"":status.toLowerCase(Locale.ROOT);
        if(text.startsWith("ouvindo"))return "listening";
        if(text.startsWith("harumi falando"))return "speaking";
        return "thinking";
    }
}

package com.harumi.autoos.voice;
/** Vosk results are segments, not necessarily a complete user request. */
public final class SpeechUtterance {
    private final StringBuilder confirmed=new StringBuilder();
    private String partial="";
    public void reset(){confirmed.setLength(0);partial="";}
    public boolean partial(String text){text=clean(text);boolean changed=!text.equals(partial);partial=text;return changed;}
    public void segment(String text){text=clean(text);if(!text.isEmpty()){if(confirmed.length()>0)confirmed.append(' ');confirmed.append(text);}partial="";}
    public String text(){return (confirmed.toString()+(partial.isEmpty()?"":" "+partial)).trim();}
    private static String clean(String s){return s==null?"":s.trim().replaceAll("\\s+"," ");}
}

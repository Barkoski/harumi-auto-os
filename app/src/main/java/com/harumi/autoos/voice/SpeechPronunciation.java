package com.harumi.autoos.voice;
/** Pronunciation is applied only to synthesis; UI, stored text and identity keep Harumi. */
public final class SpeechPronunciation {
    private SpeechPronunciation() { }
    public static String forSpeech(String text) {
        if(text==null)return "";
        return text.replaceAll("(?iu)(?<![\\p{L}\\p{N}_])harumi(?![\\p{L}\\p{N}_])","Rarumi");
    }
}

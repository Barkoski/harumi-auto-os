package com.harumi.autoos.domain;
import org.junit.Test;
import static org.junit.Assert.*;
public class AvatarStateTest {
    @Test public void readyIsIdle() { assertEquals("idle",AvatarState.from("Pronta para conversar",false)); }
    @Test public void microphoneIsListening() { assertEquals("listening",AvatarState.from("Ouvindo… fale após tocar no microfone",true)); }
    @Test public void synthesisPreparationIsNotSpeaking() { assertEquals("thinking",AvatarState.from("Preparando voz feminina…",true)); }
    @Test public void playbackIsSpeaking() { assertEquals("speaking",AvatarState.from("Harumi falando…",true)); }
    @Test public void unknownBusyStateDoesNotPretendToListen() { assertEquals("thinking",AvatarState.from(null,true)); }
}

package com.harumi.autoos;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import android.content.Context;
import com.harumi.autoos.ai.*;
import com.harumi.autoos.voice.*;
import com.harumi.autoos.diagnostics.DiagnosticMonitor;
import com.k2fsa.sherpa.onnx.GeneratedAudio;
import org.vosk.Model;
import org.vosk.Recognizer;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.File;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class LocalAiIntegrationTest {
    @Test public void actualModelVoiceAndRecognitionOffline() throws Exception {
        Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
        File root=ModelAssets.prepare(c);
        JSONObject evidence=new JSONObject();
        long start=System.currentTimeMillis();
        try(LocalLanguageModel model=new LocalLanguageModel()) {
            model.prepare(root);
            String reply=model.answer("Olá, Harumi. Se apresente em uma frase curta.",new DiagnosticMonitor().summary());
            assertTrue("Model returned no reply",reply.length()>10);
            assertFalse("Model did not generate a reply",reply.startsWith("Não consegui concluir"));
            assertFalse("Reasoning leaked",reply.contains("<think>"));
            evidence.put("reply",reply);evidence.put("llm_ms",System.currentTimeMillis()-start);
        }
        start=System.currentTimeMillis();
        try(FemaleVoice voice=new FemaleVoice()) {
            voice.prepare(root);
            GeneratedAudio greeting=voice.synthesize(VoiceProfile.GREETING);
            assertTrue("No voice samples",greeting.getSamples().length>greeting.getSampleRate());
            assertTrue(greeting.save(new File(c.getCacheDir(),"harumi-voice-sample.wav").getAbsolutePath()));
            evidence.put("voice","Supertonic 3 F3 / speaker 2 / pt / 24 steps");evidence.put("speed",VoiceProfile.SPEED);evidence.put("silence_scale",VoiceProfile.SILENCE_SCALE);evidence.put("greeting",VoiceProfile.GREETING);evidence.put("spoken_name",SpeechPronunciation.forSpeech("Harumi"));evidence.put("tts_ms",System.currentTimeMillis()-start);evidence.put("voice_seconds",(double)greeting.getSamples().length/greeting.getSampleRate());
            GeneratedAudio command=voice.synthesize("Abra o mapa para encontrar o meu destino.");
            try(Model acoustic=new Model(new File(root,"vosk-model-small-pt-0.3").getAbsolutePath());Recognizer recognizer=new Recognizer(acoustic,16000.0f)) {
                float[] samples=command.getSamples();int count=(int)((long)samples.length*16000/command.getSampleRate());short[] pcm=new short[count];
                for(int i=0;i<count;i++) { int index=(int)((long)i*command.getSampleRate()/16000);pcm[i]=(short)(Math.max(-1,Math.min(1,samples[index]))*32767); }
                recognizer.acceptWaveForm(pcm,pcm.length);
                String text=new JSONObject(recognizer.getFinalResult()).optString("text");
                evidence.put("stt_transcription",text);
                try(java.io.FileOutputStream stream=new java.io.FileOutputStream(new File(c.getCacheDir(),"ai-integration-evidence.json"))) { stream.write(evidence.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
                assertTrue("Portuguese speech recognition failed: "+text,text.contains("mapa"));
                assertEquals("Recognized speech did not become a permitted action: "+text,LocalCommandParser.Action.MAP,new LocalCommandParser().parse(text).action());
            }
        }
        try(java.io.FileOutputStream stream=new java.io.FileOutputStream(new File(c.getCacheDir(),"ai-integration-evidence.json"))) { stream.write(evidence.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    }
}

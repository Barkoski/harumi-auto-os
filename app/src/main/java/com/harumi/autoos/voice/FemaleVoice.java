package com.harumi.autoos.voice;
import android.media.*;
import com.k2fsa.sherpa.onnx.*;
import java.io.File;
import java.util.concurrent.atomic.AtomicBoolean;
/** Supertonic 3 F3 (speaker 2), selected by Lucas. Keep its native pitch and voice identity. */
public final class FemaleVoice implements AutoCloseable {
    private OfflineTts tts;
    private volatile AudioTrack track;
    private final AtomicBoolean cancelled=new AtomicBoolean();
    private volatile boolean ducked;
    public void beginUtterance(){cancelled.set(false);ducked=false;}
    /** Outro app pediu para abaixar (CAN_DUCK): reduz o volume em vez de interromper a fala. */
    public void duck(boolean on){ducked=on;AudioTrack current=track;if(current!=null){try{current.setVolume(on?0.3f:1f);}catch(IllegalStateException ignored){}}}
    public void prepare(File root) {
        if(tts!=null) return;
        File dir=new File(root,"sherpa-onnx-supertonic-3-tts-int8-2026-05-11");
        OfflineTtsSupertonicModelConfig supertonic=new OfflineTtsSupertonicModelConfig();
        supertonic.setDurationPredictor(new File(dir,"duration_predictor.int8.onnx").getAbsolutePath());
        supertonic.setTextEncoder(new File(dir,"text_encoder.int8.onnx").getAbsolutePath());
        supertonic.setVectorEstimator(new File(dir,"vector_estimator.int8.onnx").getAbsolutePath());
        supertonic.setVocoder(new File(dir,"vocoder.int8.onnx").getAbsolutePath());
        supertonic.setTtsJson(new File(dir,"tts.json").getAbsolutePath());
        supertonic.setUnicodeIndexer(new File(dir,"unicode_indexer.bin").getAbsolutePath());
        supertonic.setVoiceStyle(new File(dir,"voice.bin").getAbsolutePath());
        OfflineTtsModelConfig model=new OfflineTtsModelConfig();model.setSupertonic(supertonic);model.setNumThreads(2);model.setProvider("cpu");
        OfflineTtsConfig config=new OfflineTtsConfig();config.setModel(model);config.setMaxNumSentences(1);
        tts=new OfflineTts(null,config);
        if(tts.numSpeakers()<3) { tts.release();tts=null; throw new IllegalStateException("A voz feminina escolhida não está no pacote."); }
    }
    /** Chamar so da thread de fala. Nao zera o cancelamento (beginUtterance faz isso): um cancel() que chegue entre as frases nao pode ser desfeito. */
    public GeneratedAudio synthesize(String text) {
        GenerationConfig config=new GenerationConfig();config.setSid(VoiceProfile.SPEAKER);config.setNumSteps(VoiceProfile.STEPS);config.setSpeed(VoiceProfile.SPEED);config.setSilenceScale(VoiceProfile.SILENCE_SCALE);
        config.setExtra(java.util.Collections.singletonMap("lang","pt"));
        return tts.generateWithConfigAndCallback(SpeechPronunciation.forSpeech(text),config,new kotlin.jvm.functions.Function1<float[],Integer>() {
            @Override public Integer invoke(float[] samples) { return cancelled.get()?0:1; }
        });
    }
    public void play(GeneratedAudio audio) {
        if(cancelled.get()) return;
        float[] samples=audio.getSamples();
        int min=AudioTrack.getMinBufferSize(audio.getSampleRate(),AudioFormat.CHANNEL_OUT_MONO,AudioFormat.ENCODING_PCM_FLOAT);
        AudioTrack local=new AudioTrack.Builder().setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANT).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(new AudioFormat.Builder().setSampleRate(audio.getSampleRate()).setEncoding(AudioFormat.ENCODING_PCM_FLOAT).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setTransferMode(AudioTrack.MODE_STREAM).setBufferSizeInBytes(Math.max(4096,min)).build();
        track=local;
        try {
            if(ducked) local.setVolume(0.3f);
            local.play();int offset=0;
            while(offset<samples.length&&!cancelled.get()) {
                int n=local.write(samples,offset,Math.min(2048,samples.length-offset),AudioTrack.WRITE_NON_BLOCKING);
                if(n<0) break;
                offset+=n;
                if(n==0) { try { Thread.sleep(10); } catch(InterruptedException e) { Thread.currentThread().interrupt();break; } }
            }
            long deadline=android.os.SystemClock.elapsedRealtime()+3000;
            while(!cancelled.get() && local.getPlaybackHeadPosition()<offset && android.os.SystemClock.elapsedRealtime()<deadline) { try { Thread.sleep(25); } catch(InterruptedException e) { Thread.currentThread().interrupt();break; } }
        } finally { track=null;try { local.pause();local.flush(); } catch(IllegalStateException ignored) { } finally { local.release(); } }
    }
    public void cancel() { cancelled.set(true);AudioTrack current=track;if(current!=null) { try { current.pause(); } catch(IllegalStateException ignored) { } } }
    @Override public void close() { cancel();if(tts!=null) { tts.release();tts=null; } }
}

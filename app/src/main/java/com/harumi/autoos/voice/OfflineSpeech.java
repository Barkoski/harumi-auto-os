package com.harumi.autoos.voice;
import org.vosk.Model;
import org.vosk.Recognizer;
import org.vosk.android.*;
import java.io.*;
public final class OfflineSpeech implements AutoCloseable {
    private Model model;
    private Recognizer recognizer;
    private SpeechService service;
    public void prepare(File root) throws IOException { if(model==null) model=new Model(new File(root,"vosk-model-small-pt-0.3").getAbsolutePath()); }
    public void start(RecognitionListener listener) throws IOException {
        stop();recognizer=new Recognizer(model,16000.0f);service=new SpeechService(recognizer,16000.0f);
        if(!service.startListening(listener,45000))throw new IOException("Captura de microfone não iniciou.");
    }
    /** Escuta continua, sem prazo (usada para "Oi Harumi"). */
    public void startContinuous(RecognitionListener listener) throws IOException {
        stop();recognizer=new Recognizer(model,16000.0f);service=new SpeechService(recognizer,16000.0f);
        if(!service.startListening(listener))throw new IOException("Captura de microfone não iniciou.");
    }
    public boolean ready() { return model!=null; }
    public void stop() { if(service!=null) { service.stop();service.shutdown();service=null; } if(recognizer!=null) { recognizer.close();recognizer=null; } }
    @Override public void close() { stop();if(model!=null) { model.close();model=null; } }
}

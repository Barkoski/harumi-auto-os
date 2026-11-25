package com.harumi.autoos.ai;
import android.app.Activity;
import android.media.*;
import android.os.Handler;
import android.os.Looper;
import com.harumi.autoos.voice.*;
import com.harumi.autoos.diagnostics.DiagnosticMonitor;
import org.vosk.android.RecognitionListener;
import org.json.JSONObject;
import java.io.File;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class AssistantController implements AutoCloseable, RecognitionListener {
    public interface Listener {
        void state(String status,boolean busy);
        void message(String role,String text);
        void action(LocalCommandParser.Command command);
        default void partial(String text){}
        default void dictation(String text){}
        /** Ha app instalado para executar o comando? Chamado na thread de trabalho, antes de responder. */
        default boolean canHandle(LocalCommandParser.Command command){return true;}
        /** "Oi Harumi" ouvido: mostrar a conversa. */
        default void wake(){}
        default boolean micAllowed(){return true;}
    }
    public static final String WAKE_READY="Pronta · diga “Oi Harumi”";
    private static final String WAKE_REPLY="Oi, Lucas! O que você deseja?";
    private static final String MUSIC_OPEN="Vou abrir seu aplicativo de música.";
    private static final String MUSIC_MISSING="Não encontrei um aplicativo de música nesta central. Use o rádio ou o Bluetooth da central.";
    private static final String PREFS="harumi_wake";
    private volatile boolean wakeEnabled,wakeOn,learning;
    private int learnCount;
    private final java.util.List<String> learned=new CopyOnWriteArrayList<>();
    private final Runnable wakeRetry=()->startWake(true);
    private final Runnable learnTimeout=this::learnTimedOut;
    private void learnTimedOut(){if(learning){learning=false;listener.message("Harumi","Não ouvi as três vezes. Toque em Ensinar minha pronúncia para tentar de novo.");if(wakeOn)listener.state(WAKE_READY,false);}}
    private final Activity activity;
    private final Listener listener;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final ExecutorService speaker=Executors.newSingleThreadExecutor(); // fila de fala: unica thread que usa FemaleVoice
    private final AtomicInteger session=new AtomicInteger();
    private final AtomicBoolean busy=new AtomicBoolean();
    private final LocalCommandParser parser=new LocalCommandParser();
    private final DiagnosticMonitor diagnostic;
    private volatile LocalLanguageModel language;
    private final FemaleVoice voice=new FemaleVoice();
    private final OfflineSpeech speech=new OfflineSpeech();
    private final AudioManager audio;
    private final AtomicReference<AudioFocusRequest> focus=new AtomicReference<>();
    private volatile File models;
    private volatile boolean active=true,closed=false,listening=false;
    private boolean interruptedOnPause;
    private boolean actionHandedOff;
    private final SpeechUtterance utterance=new SpeechUtterance();
    private final Runnable speechEnd=this::finishListening;
    public AssistantController(Activity a,Listener l) { this(a,l,new DiagnosticMonitor()); }
    public AssistantController(Activity a,Listener l,DiagnosticMonitor d) {
        diagnostic=d;activity=a;listener=l;audio=(AudioManager)a.getSystemService(Activity.AUDIO_SERVICE);
        android.content.SharedPreferences p=a.getSharedPreferences(PREFS,Activity.MODE_PRIVATE);
        wakeEnabled=p.getBoolean("enabled",true);
        for(String s:p.getString("phrases","").split("\n"))if(!s.isBlank())learned.add(s);
    }
    public void resume() { active=true;diagnostic.start();if(interruptedOnPause){interruptedOnPause=false;listener.message("Harumi","A operação foi interrompida quando o aplicativo saiu de primeiro plano. Pode enviar sua mensagem novamente.");}if(!busy.get()){listener.state("Pronta para conversar · IA local",false);startWake();main.postDelayed(this::warmUp,5000);} } // aquecimento depois da tela pronta (competia com a abertura)
    /** Carrega modelos em segundo plano para o primeiro pedido nao pagar o custo. Cancelavel: qualquer nova sessao/pausa aborta entre etapas; nao segura busy. */
    private void warmUp(){
        if(closed||!active||busy.get())return;
        final int id=session.get();
        worker.execute(()->{
            try{
                if(!valid(id))return;File root=models();if(!valid(id))return;
                LocalLanguageModel lm=language;if(lm==null){lm=new LocalLanguageModel();language=lm;}
                if(!valid(id))return;lm.prepare(root);if(!valid(id))return;
                speaker.execute(()->{try{if(valid(id))voice.prepare(root);}catch(Exception|LinkageError e){android.util.Log.w("HarumiAI","Voice warm-up skipped",e);}});if(!valid(id))return;
                speech.prepare(root);
            }catch(Exception|LinkageError e){android.util.Log.w("HarumiAI","Warm-up skipped",e);}
        });
    }

    // ---- "Oi Harumi": escuta continua enquanto a Harumi esta aberta e ociosa ----
    public boolean wakeEnabled(){return wakeEnabled;}
    public void setWakeEnabled(boolean on){
        wakeEnabled=on;activity.getSharedPreferences(PREFS,Activity.MODE_PRIVATE).edit().putBoolean("enabled",on).apply();
        if(on)startWake();else{stopWake();if(!busy.get())listener.state("Pronta para conversar · IA local",false);}
    }
    public void startWake(){startWake(true);}
    /** announce=false preserva o status atual (ex.: resposta parcial com botao Continuar). */
    private void startWake(boolean announce){
        main.removeCallbacks(wakeRetry);
        if(closed||!active||!wakeEnabled||wakeOn||listening||busy.get()||!listener.micAllowed())return;
        if(audio.getMode()!=AudioManager.MODE_NORMAL){main.postDelayed(wakeRetry,10000);return;} // chamada em andamento
        worker.execute(()->{
            try{speech.prepare(models());}catch(Exception|LinkageError e){android.util.Log.e("HarumiAI","Wake word unavailable",e);return;}
            main.post(()->{
                if(closed||!active||!wakeEnabled||wakeOn||listening||busy.get())return;
                try{speech.startContinuous(wakeListener);wakeOn=true;if(learning||announce)listener.state(learning?learnStatus():WAKE_READY,false);}
                catch(Exception e){android.util.Log.e("HarumiAI","Wake word microphone failed",e);speech.stop();main.postDelayed(wakeRetry,15000);}
            });
        });
    }
    private void stopWake(){main.removeCallbacks(wakeRetry);if(wakeOn){wakeOn=false;speech.stop();}}
    private String learnStatus(){return "Aprendendo: diga “Oi Harumi” ("+(learnCount+1)+" de 3)";}
    public void learnWake(){
        if(closed||!active)return;
        if(busy.get()){listener.message("Harumi","Aguarde eu terminar ou toque em Parar antes de ensinar a pronúncia.");return;}
        learning=true;learnCount=0;main.removeCallbacks(learnTimeout);main.postDelayed(learnTimeout,40000);
        listener.message("Harumi","Diga “Oi Harumi” três vezes, com uma pausa entre elas.");
        if(!wakeEnabled)setWakeEnabled(true);else if(wakeOn)listener.state(learnStatus(),false);else startWake();
    }
    private void learned(String text){
        String n=WakeWord.normalize(text);if(n.length()<6||!WakeWord.acceptsForLearning(text))return;
        if(!learned.contains(n)){learned.add(n);while(learned.size()>6)learned.remove(0);}
        activity.getSharedPreferences(PREFS,Activity.MODE_PRIVATE).edit().putString("phrases",String.join("\n",learned)).apply();
        if(++learnCount>=3){learning=false;main.removeCallbacks(learnTimeout);listener.message("Harumi","Pronto! Aprendi seu jeito de dizer “Oi Harumi”.");listener.state(WAKE_READY,false);}
        else listener.state(learnStatus(),false);
    }
    private final RecognitionListener wakeListener=new RecognitionListener(){
        private String lastPartial="";
        public void onPartialResult(String h){check(recognitionText(h,"partial"),false);}
        public void onResult(String h){check(recognitionText(h,"text"),true);}
        public void onFinalResult(String h){check(recognitionText(h,"text"),true);}
        public void onError(Exception e){if(wakeOn){wakeOn=false;speech.stop();main.postDelayed(wakeRetry,5000);}}
        public void onTimeout(){if(wakeOn){wakeOn=false;main.postDelayed(wakeRetry,1000);}}
        private void check(String text,boolean complete){
            if(!wakeOn||text.isBlank())return;
            if(audio.getMode()!=AudioManager.MODE_NORMAL){stopWake();main.postDelayed(wakeRetry,10000);return;}
            if(learning){if(complete)learned(text);return;}
            if(!WakeWord.matches(text,learned)){if(!complete)lastPartial="";return;}
            // Parcial isolado engana (ruido/TV): so vale quando o mesmo parcial casa 2 vezes seguidas; resultado completo vale na hora.
            String n=WakeWord.normalize(text);
            if(complete||n.equals(lastPartial)){lastPartial="";onWake();}else lastPartial=n;
        }
    };
    /** Disparo do "Oi Harumi" (tambem usado pelo teste de bancada em build de depuracao). */
    public void onWake(){
        stopWake();
        if(closed||!active||!busy.compareAndSet(false,true))return;
        int id=session.incrementAndGet();
        listener.wake();listener.message("Harumi",WAKE_REPLY);
        worker.execute(()->{
            try{speak(id,WAKE_REPLY);}catch(Exception|LinkageError e){android.util.Log.e("HarumiAI","Wake reply voice failed",e);}
            main.post(()->{if(valid(id)){busy.set(false);listen();}});
        });
    }
    public boolean wakeMatches(String text){return WakeWord.matches(text,learned);}
    private boolean valid(int id) { return !closed&&active&&id==session.get(); }
    private void ui(int id,Runnable task) { main.post(()->{ if(valid(id)) task.run(); }); }
    private File models() throws Exception { if(models==null) models=ModelAssets.prepare(activity);return models; }
    public void submit(String question) {
        if(closed||!active||question==null||question.isBlank()) return;
        LocalCommandParser.Command command;
        try { command=parser.parse(question); } catch(IllegalArgumentException e) { listener.message("Harumi",e.getMessage());return; }
        if(command.action()==LocalCommandParser.Action.STOP) { cancel();return; }
        if(!busy.compareAndSet(false,true)) { listener.message("Harumi","Aguarde ou toque em Parar para interromper a operação atual.");return; }
        stopWake();int id=session.incrementAndGet();actionHandedOff=false;listener.message("Você",question);listener.state("Pensando…",true);
        worker.execute(()->{
            String completion="Pronta para conversar · IA local";
            final SpeechStream stream=new SpeechStream(id);
            try {
                if(!valid(id)) return;
                String reply;
                switch(command.action()) {
                    case GREETING: reply=VoiceProfile.GREETING;break;
                    case QUICK_REPLY: reply=command.reply();break;
                    case WIFI_SETTINGS: reply="Vou abrir as configurações de Wi-Fi do Android.";break;
                    case BLUETOOTH_SETTINGS: reply="Vou abrir as configurações de Bluetooth do Android.";break;
                    case MAP: reply="Vou abrir seu aplicativo de mapas.";break;
                    case MUSIC: reply=listener.canHandle(command)?MUSIC_OPEN:MUSIC_MISSING;break;
                    case ROUTE_BETWEEN: reply="Vou mostrar o trajeto no mapa. O cálculo usa Internet e não considera trânsito em tempo real.";break;
                    case ROUTE: reply="Vou traçar o caminho até "+command.destination()+".";break;
                    case DIAGNOSTICS: reply=diagnostic.summary();break;
                    default:
                        stream.used=true;
                        ui(id,()->listener.state("Carregando modelo local…",true));
                        ui(id,()->listener.state("Preparando IA local · a primeira execução pode demorar…",true));
                        File root=models();if(!valid(id)) return;
                        LocalLanguageModel lm=language;if(lm==null){lm=new LocalLanguageModel();language=lm;}
                        final long epoch=LocalLanguageModel.currentEpoch(); // antes de valid(id): cancel() incrementa session e depois o epoch nativo
                        if(!valid(id)) return;
                        lm.prepare(root);
                        if(!valid(id)) return;
                        ui(id,()->listener.state("Pensando…",true));LocalLanguageModel.Answer generated=lm.answer(question,LocalCommandParser.aboutCar(question)?diagnostic.summary():null,text->{if(!text.isBlank()){ui(id,()->listener.partial(text));stream.feed(text);}},epoch);reply=generated.text();
                        // Corte por limite: termina na ultima frase completa (nunca meia frase). A continuacao automatica repetia trechos.
                        if(generated.incomplete()&&!"cancelled".equals(generated.reason())){String cut=ModelOutput.lastSentence(reply);if(!cut.isEmpty())reply=cut;}
                        if(generated.incomplete()&&!"cancelled".equals(generated.reason())&&ModelOutput.looksUnfinished(reply))completion="Resposta parcial · toque em Continuar";
                }
                if(!valid(id)) return;
                String answer=reply==null||reply.isBlank()?"Não consegui montar uma resposta agora. Pode repetir?":reply;
                ui(id,()->listener.message("Harumi",answer));
                if(command.action()==LocalCommandParser.Action.MAP||command.action()==LocalCommandParser.Action.MUSIC||command.action()==LocalCommandParser.Action.ROUTE||command.action()==LocalCommandParser.Action.ROUTE_BETWEEN||command.action()==LocalCommandParser.Action.WIFI_SETTINGS||command.action()==LocalCommandParser.Action.BLUETOOTH_SETTINGS) if(listener.canHandle(command)) ui(id,()->{actionHandedOff=true;listener.action(command);});
                try {
                    if(stream.used) { // frases completas ja foram faladas durante a geracao; aqui so o resto (e, se parcial, nunca o pedaco final)
                        String tail=answer;
                        if(completion.startsWith("Resposta parcial")){String cut=ModelOutput.lastSentence(answer);tail=cut.isEmpty()?"A resposta ficou incompleta. Toque em Continuar.":cut;}
                        stream.finish(tail);
                    } else speak(id,answer);
                }
                catch(Exception|LinkageError voiceError) { completion="Resposta em texto · falha na voz";android.util.Log.e("HarumiAI","Voice engine failure",voiceError);ui(id,()->listener.message("Harumi","A resposta está acima em texto. Não consegui reproduzir a voz neste momento.")); }
            } catch(Exception|LinkageError e) {
                completion="Falha na IA local · confira a mensagem";
                String error=e.getMessage()!=null&&e.getMessage().contains("Tempo")?"A IA local atingiu o limite de processamento. Tente uma pergunta mais curta. Os atalhos continuam disponíveis.":"Não consegui concluir a operação local. Confira o espaço disponível e a compatibilidade do Android. Os atalhos continuam disponíveis.";
                ui(id,()->listener.message("Harumi",error));
                android.util.Log.e("HarumiAI","Local engine failure",e);
            } finally { stream.close();finish(id,completion); } // so "Pronta"/religar o "Oi Harumi" depois que ela calou
        });
    }
    public void greet() { submit("Olá, Harumi"); }
    /** Toda sintese/reproducao roda na thread unica `speaker` (FemaleVoice nao e thread-safe); o worker espera o fim. */
    private void speak(int id,String text) throws Exception {
        Future<?> f=speaker.submit(()->{speakNow(id,text);return null;});
        try { f.get(); } catch(ExecutionException e) { Throwable c=e.getCause();if(c instanceof Exception) throw (Exception)c;if(c instanceof Error) throw (Error)c;throw e; }
    }
    private AudioFocusRequest requestFocus(int id) {
        AudioFocusRequest request=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
            .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANT).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setOnAudioFocusChangeListener(change->{ if(!valid(id)) return;if(change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) voice.duck(true);else if(change==AudioManager.AUDIOFOCUS_GAIN) voice.duck(false);else if(change==AudioManager.AUDIOFOCUS_LOSS||change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) cancel(); },main).build();
        focus.set(request);
        if(audio.requestAudioFocus(request)!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED) { focus.compareAndSet(request,null);return null; }
        if(!valid(id)) { if(focus.compareAndSet(request,null)) audio.abandonAudioFocusRequest(request);return null; } // cancel() passou antes do focus.set: nao vazar o foco
        return request;
    }
    /** Fala em fluxo: as frases completas da resposta do modelo entram na fila do speaker enquanto ela ainda e gerada. */
    private final class SpeechStream {
        private final int id;
        private final SentenceSplitter splitter=new SentenceSplitter();
        volatile boolean used;
        private volatile boolean stopped;
        private volatile Throwable error;
        private volatile Future<?> last;
        private volatile AudioFocusRequest request;
        private boolean started; // so a thread speaker
        SpeechStream(int id) { this.id=id; }
        void feed(String text) { for(String s:splitter.feed(text)) say(s); }
        private void say(String s) {
            if(s.isBlank()||stopped) return;
            try { last=speaker.submit(()->sayNow(s)); } catch(RejectedExecutionException e) { stopped=true; }
        }
        private void sayNow(String s) {
            if(stopped||!valid(id)) return;
            try {
                if(!started) {
                    if(audio.getMode()!=AudioManager.MODE_NORMAL) { stopped=true;return; }
                    ui(id,()->listener.state("Preparando voz feminina…",true));
                    voice.beginUtterance();if(!valid(id)) return; // beginUtterance antes do valid: cancel() incrementa a sessao antes de voice.cancel()
                    voice.prepare(models());if(!valid(id)) return;
                }
                com.k2fsa.sherpa.onnx.GeneratedAudio generated=voice.synthesize(s);
                if(stopped||!valid(id)) return;
                if(!started) { // foco uma unica vez, so quando ha audio pronto (nao abaixa a musica durante a sintese)
                    request=requestFocus(id);
                    if(request==null) { stopped=true;return; }
                    started=true;ui(id,()->listener.state("Harumi falando…",true));
                }
                voice.play(generated);
            } catch(Exception|LinkageError e) { error=e;stopped=true; }
        }
        /** Fim da geracao: resto da resposta (se completa) entra na fila; espera ela calar e propaga falha de voz. */
        void finish(String tail) throws Exception {
            feed(tail);say(splitter.flush());await();
            Throwable e=error;if(e instanceof Exception) throw (Exception)e;if(e instanceof Error) throw (Error)e;
        }
        private void await() { Future<?> f=last;if(f==null) return;try { f.get(); } catch(InterruptedException e) { Thread.currentThread().interrupt(); } catch(ExecutionException ignored) { } }
        /** Sempre no finally do worker: descarta frases pendentes, espera a frase em curso e solta o foco desta fala. */
        void close() { stopped=true;await();AudioFocusRequest r=request;if(r!=null&&focus.compareAndSet(r,null)) audio.abandonAudioFocusRequest(r); }
    }
    private void speakNow(int id,String text) throws Exception {
        if(!valid(id)||audio.getMode()!=AudioManager.MODE_NORMAL) return;
        ui(id,()->listener.state("Preparando voz feminina…",true));
        voice.beginUtterance();
        com.k2fsa.sherpa.onnx.GeneratedAudio generated=CachedVoice.load(activity,text);
        if(generated==null){voice.prepare(models());if(!valid(id)) return;generated=voice.synthesize(text);}
        if(!valid(id)) return;
        if(requestFocus(id)==null) return;
        ui(id,()->listener.state("Harumi falando…",true));
        try { if(valid(id)) voice.play(generated); } finally { releaseFocus(); }
    }
    public void listen() {
        if(closed||!active||!busy.compareAndSet(false,true)) return;
        stopWake();int id=session.incrementAndGet();utterance.reset();listener.dictation("");listener.state("Preparando reconhecimento offline…",true);
        worker.execute(()->{
            try {
                speech.prepare(models());if(!valid(id)) { finish(id);return; }
                main.post(()->{
                    if(!valid(id)) { finish(id);return; }
                    if(audio.getMode()!=AudioManager.MODE_NORMAL) { listener.message("Harumi","Não posso ouvir durante uma chamada.");finish(id);return; }
                    try { if(audio.isMicrophoneMute())throw new IllegalStateException("Microfone silenciado pelo Android");AudioFocusRequest request=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE).setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANT).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build()).setOnAudioFocusChangeListener(change->{if(valid(id)&&(change==AudioManager.AUDIOFOCUS_LOSS||change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT))cancel();},main).build();
                        focus.set(request);
                        if(audio.requestAudioFocus(request)!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED)throw new IllegalStateException("Sem foco de áudio");
                        listening=true;speech.start(listenerFor(id));listener.state("Ouvindo… fale e aguarde a pausa, ou toque em Concluir",true); }
                    catch(Exception e) { android.util.Log.e("HarumiAI","Microphone start failed",e);listening=false;speech.stop();releaseFocus();listener.message("Harumi","Não foi possível acessar o microfone. Confira a permissão e a entrada de áudio do emulador ou da central.");finish(id,"Falha ao iniciar o microfone"); }
                });
            } catch(Exception|LinkageError e) { android.util.Log.e("HarumiAI","Speech engine failure",e);ui(id,()->listener.message("Harumi","Reconhecimento local indisponível neste Android. Você pode usar o campo de texto."));finish(id,"Falha no reconhecimento local"); }
        });
    }
    private RecognitionListener listenerFor(int id){return new RecognitionListener(){
        public void onPartialResult(String s){if(valid(id))AssistantController.this.onPartialResult(s);}
        public void onResult(String s){if(valid(id))AssistantController.this.onResult(s);}
        public void onFinalResult(String s){if(valid(id))AssistantController.this.onFinalResult(s);}
        public void onError(Exception e){if(valid(id))AssistantController.this.onError(e);}
        public void onTimeout(){if(valid(id))AssistantController.this.onTimeout();}
    };}
    private String recognitionText(String json,String key){try{return new JSONObject(json).optString(key,"");}catch(Exception e){return "";}}
    public void finishListening(){
        if(!listening||!active)return;listening=false;main.removeCallbacks(speechEnd);String text=utterance.text();speech.stop();releaseFocus();busy.set(false);listener.dictation("");
        if(text.isBlank()){listener.state("Não ouvi uma frase. Toque para tentar novamente.",false);startWake(false);}else submit(text);
    }
    @Override public void onPartialResult(String hypothesis){if(!listening||!active)return;String text=recognitionText(hypothesis,"partial");if(utterance.partial(text)&&!text.isBlank()){main.removeCallbacks(speechEnd);}listener.dictation(utterance.text());}
    @Override public void onResult(String hypothesis){if(!listening||!active)return;String text=recognitionText(hypothesis,"text");if(!text.isBlank()){utterance.segment(text);listener.dictation(utterance.text());main.removeCallbacks(speechEnd);main.postDelayed(speechEnd,1800);}}
    @Override public void onFinalResult(String hypothesis){if(!listening||!active)return;String text=recognitionText(hypothesis,"text");if(!text.isBlank())utterance.segment(text);finishListening();}
    @Override public void onError(Exception e){if(listening){main.removeCallbacks(speechEnd);listening=false;speech.stop();releaseFocus();busy.set(false);listener.state("Falha no microfone. Tente novamente.",false);main.postDelayed(wakeRetry,5000);}}
    @Override public void onTimeout(){finishListening();}
    private void finish(int id) { finish(id,"Pronta para conversar · IA local"); }
    private void finish(int id,String status) { main.post(()->{ if(valid(id)) { busy.set(false);listener.state(status,false);startWake(status.startsWith("Pronta")); } }); }
    private void releaseFocus() { AudioFocusRequest f=focus.getAndSet(null);if(f!=null)audio.abandonAudioFocusRequest(f); }
    public void cancel() {
        final int cancelled=session.incrementAndGet();main.removeCallbacks(speechEnd);utterance.reset();listener.dictation("");listening=false;wakeOn=false;main.removeCallbacks(wakeRetry);speech.stop();voice.cancel();
        try { if(language!=null) LocalLanguageModel.cancel(); } catch(LinkageError ignored) { }
        releaseFocus();
        // Keep queued work serialized. Only clear busy after the previous worker unwinds.
        if(!closed) worker.execute(()->main.post(()->{ if(session.get()!=cancelled)return;busy.set(false);if(active&&!closed){listener.state("Pronta para conversar · IA local",false);startWake();} }));
    }
    public void cancelWithFeedback(){if(busy.get())listener.message("Harumi","Operação interrompida. Pode enviar uma nova mensagem.");cancel();}
    public void pause() { interruptedOnPause=busy.get()&&!actionHandedOff;active=false;diagnostic.close();cancel(); }
    @Override public void close() { closed=true;active=false;wakeOn=false;main.removeCallbacks(wakeRetry);main.removeCallbacks(learnTimeout);diagnostic.close();session.incrementAndGet();main.removeCallbacks(speechEnd);utterance.reset();listener.dictation("");listening=false;speech.stop();voice.cancel();if(language!=null)LocalLanguageModel.cancel();worker.execute(()->{speech.close();if(language!=null)language.close();});worker.shutdown();try{speaker.execute(voice::close);}catch(RejectedExecutionException ignored){}speaker.shutdown(); }
}

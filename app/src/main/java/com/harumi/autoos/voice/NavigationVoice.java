package com.harumi.autoos.voice;
import android.content.Context;
import android.media.*;
import java.util.*;
import java.util.concurrent.*;
public final class NavigationVoice {
    private static final int MAX_QUEUE=3;
    private static final Map<String,String> CLIPS=buildClips();
    private final Context context;private final AudioManager audio;
    private final ExecutorService executor=Executors.newSingleThreadExecutor(r->{Thread t=new Thread(r,"harumi-nav-voice");t.setDaemon(true);return t;});
    private final ArrayDeque<String> queue=new ArrayDeque<>();private final Map<String,CachedPcm.Audio> loaded=new HashMap<>();
    private boolean draining;private volatile boolean closed;private volatile AudioTrack current;private AudioFocusRequest focus;
    public NavigationVoice(Context context) { this.context=context.getApplicationContext();audio=(AudioManager)this.context.getSystemService(Context.AUDIO_SERVICE); }
    private static Map<String,String> buildClips() {
        Map<String,String> m=new LinkedHashMap<>();
        for(String c:new String[]{"d100","d200","d500","d1k","now","left","right","slight_left","slight_right","sharp_left","sharp_right","straight","uturn","keep_left","keep_right","arrive","recalc","roundabout_1","roundabout_2","roundabout_3","roundabout_4","roundabout_5"})m.put(c,"nav_"+c);
        m.put("nav_start","nav_start"); // o codigo ja carrega o prefixo
        return Collections.unmodifiableMap(m);
    }
    public static boolean validCode(String code) { return code!=null&&CLIPS.containsKey(code); }
    public static String clipId(String code) { return code==null?null:CLIPS.get(code); }
    public static Set<String> codes() { return CLIPS.keySet(); }
    public void play(String code) {
        if(closed||!validCode(code))return;
        synchronized(queue){
            queue.addLast(code);while(queue.size()>MAX_QUEUE)queue.removeFirst(); // descarta as mais antigas
            if(draining)return;draining=true;
        }
        try{executor.execute(this::drain);}catch(RejectedExecutionException e){synchronized(queue){draining=false;}}
    }
    private void drain() {
        boolean focused=false;
        try{
            while(!closed){
                String code;synchronized(queue){code=queue.pollFirst();if(code==null){draining=false;return;}}
                CachedPcm.Audio clip=clip(code);if(clip==null)continue;
                if(!focused)focused=requestFocus();
                playClip(clip);
            }
        }finally{
            synchronized(queue){draining=false;}
            if(focused)abandonFocus();
        }
    }
    private CachedPcm.Audio clip(String code) {
        String id=clipId(code);CachedPcm.Audio a=loaded.get(id);
        if(a==null){a=CachedVoice.loadById(context,id);if(a!=null)loaded.put(id,a);}
        return a;
    }
    private boolean requestFocus() {
        if(audio==null)return false;
        focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK).setAudioAttributes(attributes()).setOnAudioFocusChangeListener(change->{ }).build();
        audio.requestAudioFocus(focus);return true; // mesmo sem foco concedido a instrucao de rota fala
    }
    private void abandonFocus() { if(audio!=null&&focus!=null)audio.abandonAudioFocusRequest(focus);focus=null; }
    private static AudioAttributes attributes() { return new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build(); }
    private void playClip(CachedPcm.Audio clip) {
        AudioTrack track=null;
        try{
            int frames=clip.samples().length;
            track=new AudioTrack.Builder().setAudioAttributes(attributes())
                .setAudioFormat(new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_FLOAT).setSampleRate(clip.sampleRate()).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
                .setBufferSizeInBytes(frames*4).setTransferMode(AudioTrack.MODE_STATIC).build();
            if(track.write(clip.samples(),0,frames,AudioTrack.WRITE_BLOCKING)!=frames)return;
            current=track;if(closed)return;
            track.play();
            long end=System.nanoTime()+(frames*1000L/clip.sampleRate()+600)*1_000_000L; // limite de seguranca
            while(!closed&&track.getPlaybackHeadPosition()<frames&&System.nanoTime()<end)Thread.sleep(20);
        }catch(InterruptedException e){Thread.currentThread().interrupt();}
        catch(RuntimeException e){android.util.Log.w("HarumiAI","Navigation voice failed: "+e.getClass().getSimpleName());}
        finally{current=null;if(track!=null){try{track.stop();}catch(RuntimeException ignored){}track.release();}}
    }
    public void close() {
        closed=true;synchronized(queue){queue.clear();}
        AudioTrack t=current;if(t!=null){try{t.stop();}catch(RuntimeException ignored){}}
        executor.shutdownNow();
    }
}

package com.harumi.autoos.voice;
import android.content.Context;
import com.k2fsa.sherpa.onnx.GeneratedAudio;
import java.io.*;
public final class CachedVoice {
    private CachedVoice() { }
    public static CachedPcm.Audio loadById(Context context,String id) { // clipes fixos por id (navegacao); id fora do padrao nunca toca o disco
        if(id==null||!id.matches("[a-z0-9_]{1,40}"))return null;
        try(InputStream input=context.getAssets().open("voice-cache/"+id+".f32")){return CachedPcm.decode(input);}
        catch(IOException e){android.util.Log.w("HarumiAI","Navigation clip unavailable: "+id);return null;}
    }
    public static GeneratedAudio load(Context context,String text) {
        if(VoiceProfile.SPEAKER!=2||VoiceProfile.STEPS!=24||VoiceProfile.SPEED!=1.25f||VoiceProfile.SILENCE_SCALE!=.72f)return null;
        if(text==null||text.isEmpty())return null;
        try{
            StringBuilder json=new StringBuilder();
            try(BufferedReader reader=new BufferedReader(new InputStreamReader(context.getAssets().open("voice-cache/manifest.json"),java.nio.charset.StandardCharsets.UTF_8))){
                String line;while((line=reader.readLine())!=null){json.append(line);if(json.length()>32768)throw new IOException("Oversized cache metadata");}
            }
            org.json.JSONArray clips=new org.json.JSONObject(json.toString()).getJSONArray("clips");String key=null; // o texto exato do manifest (gerado a partir do codigo pelo script) define o clipe; texto diferente cai na sintese
            for(int i=0;i<clips.length()&&key==null;i++){org.json.JSONObject clip=clips.getJSONObject(i);String id=clip.getString("id");if(text.equals(clip.getString("text"))&&id.matches("[a-z0-9_]{1,40}"))key=id;}
            if(key==null)return null;
            try(InputStream input=context.getAssets().open("voice-cache/"+key+".f32")){
            CachedPcm.Audio audio=CachedPcm.decode(input);return new GeneratedAudio(audio.samples(),audio.sampleRate());
            }
        }catch(IOException|org.json.JSONException e){android.util.Log.w("HarumiAI","Fixed voice cache unavailable; using synthesis");return null;}
    }
}

package com.harumi.autoos.ai;
import java.io.File;
import java.nio.charset.StandardCharsets;
public final class LocalLanguageModel implements AutoCloseable {
    static { System.loadLibrary("harumi"); }
    public interface Progress { void onText(byte[] text); }
    public record Answer(String text,boolean incomplete,String reason){}
    private long handle;
    private final ConversationContext context=new ConversationContext();
    public void prepare(File root) { if(handle==0)handle=load(new File(root,"Qwen3.5-0.8B-Q4_K_M.gguf").getAbsolutePath().getBytes(StandardCharsets.UTF_8)); }
    public Answer answer(String question,String diagnostics,java.util.function.Consumer<String> progress) { return answer(question,diagnostics,progress,epoch()); }
    public Answer answer(String question,String diagnostics,java.util.function.Consumer<String> progress,long epoch) {
        String system=DomainScope.PERSONA
            +(diagnostics==null||diagnostics.isBlank()?"":" Diagnóstico real: "+diagnostics);
        String prompt;
        do {prompt="<|im_start|>system\n"+system+"<|im_end|>\n"+context.prompt()+"<|im_start|>user\n"+ConversationContext.safe(question)+"<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n";
            if(tokenCount(handle,prompt.getBytes(StandardCharsets.UTF_8))<=3000)break;
        }while(context.removeOldest());
        String q=java.text.Normalizer.normalize(question==null?"":question,java.text.Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(java.util.Locale.ROOT);
        boolean longer=q.contains("explique")||q.contains("detalhe")||q.contains("passo a passo")||q.contains("mais sobre"); // cobre "detalhes"
        int maxTokens=longer?320:160,maxSentences=longer?6:3;
        String raw=new String(generate(handle,prompt.getBytes(StandardCharsets.UTF_8),text->progress.accept(ModelOutput.clean(new String(text,StandardCharsets.UTF_8))),epoch,maxTokens,maxSentences),StandardCharsets.UTF_8);
        int split=raw.indexOf('\n');String reason=split<0?"error":raw.substring(0,split);String answer=ModelOutput.clean(split<0?raw:raw.substring(split+1));
        if("sentences".equals(reason)){String cut=ModelOutput.lastSentence(answer);if(!cut.isEmpty())answer=cut;} // parada por frases pode trazer o inicio da proxima palavra
        boolean incomplete=(!"eos".equals(reason)&&!"sentences".equals(reason)&&!"cancelled".equals(reason))||ModelOutput.looksUnfinished(answer);
        if(answer.isEmpty())return new Answer("Não consegui concluir a resposta agora. Toque em Continuar para tentar novamente.",true,"cancelled".equals(reason)?reason:"empty");
        context.add(question,answer);
        return new Answer(answer,incomplete,reason);
    }
    public String answer(String question,String diagnostics){return answer(question,diagnostics,text->{}).text();}
    public static void cancel(){cancelNative();}
    /** Epoch de cancelamento; so chamar de thread que ja pode carregar a biblioteca nativa (worker). */
    public static long currentEpoch(){return epoch();}
    @Override public void close(){if(handle!=0){unload(handle);handle=0;}context.clear();}
    private static native long load(byte[] path);
    private static native int tokenCount(long handle,byte[] prompt);
    private static native byte[] generate(long handle,byte[] prompt,Progress progress,long epoch,int maxTokens,int maxSentences);
    private static native long epoch();
    private static native void cancelNative();
    private static native void unload(long handle);
}

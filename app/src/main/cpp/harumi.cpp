#include <jni.h>
#include <llama.h>
#include <atomic>
#include <chrono>
#include <string>
#include <vector>
#include <algorithm>
#include <stdexcept>
#include <thread>

namespace {
std::atomic<uint64_t> cancel_epoch(0); // cada cancelamento incrementa; a requisicao compara com o valor capturado pelo Java
struct Engine {
    llama_model *model = nullptr;
    llama_context *context = nullptr;
    std::chrono::steady_clock::time_point deadline;
    uint64_t request_epoch = 0;
};
std::string bytes(JNIEnv *env, jbyteArray value) {
    if (!value) return {};
    jsize n = env->GetArrayLength(value);
    std::string s(n, '\0');
    env->GetByteArrayRegion(value, 0, n, reinterpret_cast<jbyte *>(s.data()));
    return s;
}
jbyteArray result(JNIEnv *env, const std::string &s) {
    jbyteArray a = env->NewByteArray(s.size());
    if (!a) return nullptr;
    env->SetByteArrayRegion(a, 0, s.size(), reinterpret_cast<const jbyte *>(s.data()));
    return a;
}
void fail(JNIEnv *env, const char *message) { env->ThrowNew(env->FindClass("java/lang/IllegalStateException"), message); }
bool abort_decode(void *data) { return cancel_epoch.load()!=static_cast<Engine *>(data)->request_epoch || std::chrono::steady_clock::now()>=static_cast<Engine *>(data)->deadline; }
}
extern "C" JNIEXPORT jlong JNICALL Java_com_harumi_autoos_ai_LocalLanguageModel_load(JNIEnv *env, jclass, jbyteArray path) {
    llama_backend_init();
    auto p = llama_model_default_params(); p.n_gpu_layers = 0;
    auto *e = new Engine(); e->model = llama_model_load_from_file(bytes(env, path).c_str(), p);
    if (!e->model) { delete e; fail(env, "Nao foi possivel carregar o modelo local."); return 0; }
    return reinterpret_cast<jlong>(e);
}
extern "C" JNIEXPORT jbyteArray JNICALL Java_com_harumi_autoos_ai_LocalLanguageModel_generate(JNIEnv *env, jclass, jlong handle, jbyteArray prompt, jobject progress, jlong epoch, jint maxTokens, jint maxSentences) {
    auto *e = reinterpret_cast<Engine *>(handle);
    if (!e || !e->model) { fail(env, "Modelo indisponivel."); return nullptr; }
    e->request_epoch=static_cast<uint64_t>(epoch); // nao zera cancelamento: cancel anterior a esta chamada continua valendo
    auto cancelled=[&]{return cancel_epoch.load()!=e->request_epoch;};
    if(cancelled())return result(env,"cancelled\n");
    e->deadline=std::chrono::steady_clock::now()+std::chrono::seconds(180); // teto de seguranca; respostas curtas terminam antes por EOS
    if(!e->context) {
        auto cp = llama_context_default_params(); cp.n_ctx = 4096; cp.n_batch = 256; cp.n_ubatch = 128;
        cp.n_threads=std::max(1u,std::min(4u,std::thread::hardware_concurrency()));cp.n_threads_batch=cp.n_threads;
        cp.abort_callback = abort_decode;cp.abort_callback_data=e;
        e->context=llama_init_from_model(e->model, cp);
    }
    llama_context *ctx = e->context;
    if (!ctx) { fail(env, "Memoria insuficiente para a conversa."); return nullptr; }
    // Reuse allocations, but clear all recurrent/KV state: no unsafe prefix reuse on a hybrid model.
    llama_memory_clear(llama_get_memory(ctx),true);
    const llama_vocab *vocab = llama_model_get_vocab(e->model);
    std::string text = bytes(env, prompt);
    int size = -llama_tokenize(vocab, text.data(), text.size(), nullptr, 0, true, true);
    std::vector<llama_token> tokens(std::max(1, size));
    int count = llama_tokenize(vocab, text.data(), text.size(), tokens.data(), tokens.size(), true, true);
    if (count <= 0 || count > 3000) { /* 3000 de prompt + 1024 de resposta cabem em n_ctx 4096 */ fail(env, "Conversa excedeu o contexto local."); return nullptr; }
    for (int offset = 0; offset < count && !cancelled(); offset += 256) {
        int n = std::min(256, count - offset);
        if (llama_decode(ctx, llama_batch_get_one(tokens.data()+offset, n)) != 0) {
            if(cancelled())return result(env, "");
            fail(env, std::chrono::steady_clock::now()>=e->deadline?"Tempo de inferencia excedido.":"Falha ao processar a conversa.");return nullptr;
        }
    }
    llama_sampler *sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(sampler, llama_sampler_init_penalties(llama_vocab_n_tokens(vocab), 64, 1.1f, 0.0f, 0.0f)); // antes de top_k/top_p/temp/dist, como em common/sampling.cpp
    llama_sampler_chain_add(sampler, llama_sampler_init_top_k(20));
    llama_sampler_chain_add(sampler, llama_sampler_init_top_p(0.8f, 1));
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.4f)); // mais conservador: o 0,8B inventava mais a 0,6
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));
    std::string output; std::string reason="length";
    jmethodID onText=nullptr;if(progress){jclass cls=env->GetObjectClass(progress);onText=env->GetMethodID(cls,"onText","([B)V");env->DeleteLocalRef(cls);if(!onText){env->ExceptionClear();}}
    auto utf8Output=[&](){size_t end=output.size();if(end==0)return output;size_t start=end-1;while(start>0&&(static_cast<unsigned char>(output[start])&0xc0)==0x80)--start;unsigned char lead=output[start];size_t need=lead<0x80?1:lead<0xe0?2:lead<0xf0?3:4;return end-start<need?output.substr(0,start):output;};
    auto publish=[&](){if(onText){jbyteArray value=result(env,utf8Output());env->CallVoidMethod(progress,onText,value);env->DeleteLocalRef(value);}};
    // frases completas: . ! ? seguido de espaco/quebra; ignora "2.0" (sem espaco) e item de lista "1." no inicio da linha
    auto sentences=[&](){int n=0;for(size_t k=0;k+1<output.size();++k){char c=output[k],d=output[k+1];if((c!='.'&&c!='!'&&c!='?')||(d!=' '&&d!='\n'&&d!='\r'&&d!='\t'))continue;
        if(c=='.'){size_t b=k;while(b>0&&output[b-1]>='0'&&output[b-1]<='9')--b;if(b<k&&(b==0||output[b-1]=='\n'))continue;}
        ++n;}return n;};
    const int tokenLimit=std::max(1,std::min(static_cast<int>(maxTokens),1024)),sentenceLimit=static_cast<int>(maxSentences);
    for (int i=0; i<tokenLimit && !cancelled(); ++i) { /* teto de tokens vindo do Java (3000 de prompt + 1024 cabem em n_ctx 4096) */
        if (std::chrono::steady_clock::now()>=e->deadline) {reason="time";break;}
        llama_token token = llama_sampler_sample(sampler, ctx, -1);
        if (llama_vocab_is_eog(vocab, token)) {reason="eos";break;}
        char piece[512]; int n = llama_token_to_piece(vocab, token, piece, sizeof(piece), 0, true);
        if (n > 0) output.append(piece, n);
        if(sentenceLimit>0&&sentences()>=sentenceLimit){reason="sentences";break;}
        if(i%8==0)publish();
        if(env->ExceptionCheck()){llama_sampler_free(sampler);return nullptr;}
        if (llama_decode(ctx, llama_batch_get_one(&token, 1)) != 0) {reason=std::chrono::steady_clock::now()>=e->deadline?"time":"decode";break;}
    }
    llama_sampler_free(sampler);
    if(output.empty()&&!cancelled()&&std::chrono::steady_clock::now()>=e->deadline){fail(env,"Tempo de inferencia excedido.");return nullptr;}
    if(cancelled())return result(env,"cancelled\n");
    publish();if(env->ExceptionCheck())return nullptr;
    return result(env,reason+"\n"+utf8Output());
}
extern "C" JNIEXPORT jint JNICALL Java_com_harumi_autoos_ai_LocalLanguageModel_tokenCount(JNIEnv *env,jclass,jlong handle,jbyteArray prompt){
    auto *e=reinterpret_cast<Engine *>(handle);if(!e||!e->model)return 0;
    std::string text=bytes(env,prompt);return -llama_tokenize(llama_model_get_vocab(e->model),text.data(),text.size(),nullptr,0,true,true);
}
extern "C" JNIEXPORT void JNICALL Java_com_harumi_autoos_ai_LocalLanguageModel_cancelNative(JNIEnv *, jclass) { cancel_epoch.fetch_add(1); }
extern "C" JNIEXPORT jlong JNICALL Java_com_harumi_autoos_ai_LocalLanguageModel_epoch(JNIEnv *, jclass) { return static_cast<jlong>(cancel_epoch.load()); }
extern "C" JNIEXPORT void JNICALL Java_com_harumi_autoos_ai_LocalLanguageModel_unload(JNIEnv *, jclass, jlong handle) {
    auto *e = reinterpret_cast<Engine *>(handle); if (e) { if(e->context)llama_free(e->context);llama_model_free(e->model); delete e; }
}

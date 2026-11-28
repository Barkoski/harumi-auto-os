# IA embarcada no Orange Pi 5 — avaliação inicial (11/11/2026)

## O que o hardware muda

O Orange Pi passa a poder ser o computador que roda a interface e a IA dentro do carro, em vez da central multimídia atual. O NVMe de 256 GB serve para sistema, modelo e mapas; os 8 GB de RAM permitem manter app e modelo carregados com margem maior que em muitos head units. Ainda precisamos conferir a placa exata, RAM, sistema, driver, refrigeração e alimentação. O anúncio não prova que Android, áudio, GPS ou NPU estejam funcionando.

“Tem npm” normalmente significa que existe Node.js/npm em uma imagem Linux, ou que foi instalado por ela. npm instala ferramentas JavaScript; não acelera IA e não é requisito para o app Android nativo. Só será útil para scripts/servidores Node de protótipo. A Harumi atual é Android Java + interface WebView + inferência C++ via JNI.

## O que o código atual já faz

- Carrega `Qwen3.5-0.8B-Q4_K_M.gguf` em `LocalLanguageModel`.
- O C++ usa `llama.cpp`, contexto 4096 e `n_gpu_layers=0`; o CMake força backend CPU e desliga Vulkan/OpenCL. Portanto a implementação atual não usa a NPU e tampouco seleciona a GPU.
- Voz é pipeline separado: Vosk para reconhecimento de português e Supertonic para fala. Não são substituídos automaticamente pelo LLM.

## Opções para este Orange Pi

### Caminho A — Android + CPU (primeira prova)

Manter o APK e o JNI/llama.cpp atuais. Compilar ARM64, instalar numa imagem Android que realmente dê boot e testar o GGUF quantizado. É o caminho de menor retrabalho e verifica a placa como terminal Android. O processador ARM executa o modelo; a NPU fica ociosa. Usar os resultados históricos do emulador apenas como referência, nunca como previsão de velocidade ou estabilidade no RK3588S.

### Caminho B — Linux + RKLLM/NPU

Converter/usar um modelo no formato RKLLM e rodar a biblioteca do fabricante no RK3588S. É o caminho mais direto para experimentar a NPU Rockchip. O SDK do fornecedor lista artefatos/modelos RK3588 e publica benchmarks próprios, inclusive Qwen3.5 0.8B, mas o benchmark usa configurações específicas de sequência, frequência, quantização e runtime. Não é evidência do Orange Pi recebido nem do Android instalado. Há API de compilação Android no repositório RKLLM, mas o exemplo operacional principal é Linux ARM64; binário, biblioteca, driver e permissões precisam combinar com o sistema/kernel reais.

O app atual não pode simplesmente abrir um arquivo `.rkllm`: precisaria de uma implementação alternativa de inferência, JNI/API de serviço, conversor de prompt/stream/cancelamento e validação de licença/redistribuição do runtime. Uma opção arquitetural é rodar um servidor local no Orange Pi e fazer o app chamar `127.0.0.1`; isso só se aplica se o OS escolhido permitir o processo servidor e a ponte de rede. Manteremos fallback llama.cpp CPU.

## Compatibilidade de modelos no RKLLM (consulta 11/11/2026)

O repositório oficial `airockchip/rknn-llm` lista suporte a Qwen3.5 e Gemma4 no changelog 1.3.0 e disponibiliza exemplos/artefatos RK3588. A tabela do fornecedor publica para RK3588 (sequência de entrada 128 tokens, 64 gerados, CPU e NPU em frequência máxima, `optimization_level=0`):

| Modelo/formato do benchmark | Tokens/s publicados | Memória publicada | Leitura para este projeto |
|---|---:|---:|---|
| Qwen3.5 0.8B W8A8 | 27,05 | ~1.040 MB | Melhor candidato principal para comparar ao GGUF atual |
| Qwen3.5 0.8B W4A16 | 18,79 | ~690 MB | Menor memória, mais lento nesta tabela |
| Qwen2 0.5B W8A8 | 41,58 | ~670 MB | Alternativa menor/rápida, arquitetura mais antiga |
| Qwen3 0.6B W8A8 | 32,91 | ~790 MB | Alternativa compacta |
| Qwen3.5 2B W8A8 | 13,59 | ~2.122 MB | Pode caber em 8 GB, mas memória real do sistema/app precisa ser medida |
| Gemma4 E2B W8A8 | 11,12 | ~2.499 MB | Candidato maior; validar qualidade, memória e suporte do pacote exato |

Observações importantes:

- As tabelas dão memória reportada pelo runtime, não consumo total da placa. Android/Linux, WebView, ASR/TTS e buffers competem pela RAM compartilhada.
- O `Qwen3.5-0.8B-Q4_K_M.gguf` do app não é intercambiável com os artefatos RKLLM. Deve-se obter/gerar o pacote RKLLM correspondente à arquitetura/quantização; não assumir conversão direta dessa quantização. A documentação/README mostra um artefato Qwen3.5 0.8B W8A8 para RK3588.
- O benchmark do fabricante foi feito sob frequência máxima declarada e sequência curta. É referência de comparação, não promessa para a unidade, refrigeração ou fonte do usuário.
- “Gemma4” está listado como Gemma4 E2B no benchmark de texto; há exemplo separado de entrada multimodal imagem/áudio. Isso não significa que reconhecimento de fala em português ou síntese Supertonic estejam incluídos no LLM.
- Suporte a conversão e inferência precisa ser conferido na mesma versão do Toolkit, runtime, driver NPU e `.rkllm`; registrar os hashes de todos.

Fontes primárias: [changelog RKLLM](https://github.com/airockchip/rknn-llm/blob/main/CHANGELOG.md), [benchmark](https://github.com/airockchip/rknn-llm/blob/main/benchmark.md), [README/model zoo e exemplo](https://github.com/airockchip/rknn-llm).

## Projeto de integração planejado

1. Manter `LocalLanguageModel` atual como backend CPU de referência.
2. Introduzir uma interface de backend (`prepare`, `answer/stream`, `cancel`, `close`) que preserve contexto de conversa, limpeza de saída, limite de tokens e contrato de cancelamento.
3. Criar `RkllmLanguageModel` em módulo/source set Android ARM64 opcional; JNI encapsula a API C oficial, sem expor símbolos RKLLM ao resto do app. Seleção por configuração explícita de bancada, com fallback claro para CPU se biblioteca/modelo/driver não carregarem.
4. Separar armazenamento/manifesto do modelo `.rkllm` (versão, hash, arquitetura, quantização e licença) dos assets GGUF. Não empacotar os dois modelos grandes no APK de produção por padrão.
5. Implementar um teste de bancada que verifique carregamento, prompt simples em pt-BR, streaming, EOS, cancelamento, várias chamadas seguidas e recuperação de falha. Benchmark deve registrar TTFT, tokens/s, RSS, temperatura e consumo.
6. Primeiro provar a API do RKLLM no OS/runtime recomendado pelo SDK; em seguida repetir no Android exato escolhido para a multimídia. Se o suporte Android falhar, rodar um serviço local no Linux é alternativa de arquitetura, não requisito definido.

### Instruções do build de bancada

O app agora possui uma camada Java opcional e um wrapper JNI para a API RKLLM Android. O runtime do SDK continua como dependência externa e o build normal segue CPU:

1. Obter da distribuição oficial Rockchip o diretório Android ARM64 do RKLLM SDK/runtime compatível com a imagem instalada. Colocá-lo em `app/src/main/cpp/rkllm-runtime/Android/librkllm_api/`, incluindo `include/rkllm.h`, `arm64-v8a/librkllmrt.so` e dependências OpenMP exigidas pelo SDK. Não copiar binários de tutorial sem confirmar origem/versão/licença.
2. Copiar o modelo convertido compatível (candidato `Qwen3.5-0.8B_w8a8_rk3588.rkllm`) para a pasta privada `models-v2` que a Harumi já usa. Por ora, o mecanismo de `ModelAssets` não instala esse modelo: ele precisa ser provisionado à parte, e a app volta para GGUF CPU se não puder inicializar RKLLM.
3. Compilar somente ARM64: `gradlew.bat :app:assembleDebug -PenableRkllm=true`. A flag ativa o backend RKLLM e restringe a ABI do APK a ARM64; sem ela, continua `llama.cpp` CPU com ARM64 e x86_64. Para escolher uma pasta de SDK diferente, passe também `-DHARUMI_RKLLM_ROOT=<diretório>` via configuração CMake do Android Studio.
4. Instalar primeiro em bancada, coletar logcat e confirmar `rkllm_init` bem-sucedido/uso de NPU. Comparar prompt, versão/hash do modelo, TTFT, tokens/s, RSS e temperatura. Só depois testar voz e uso simultâneo.

Estado do código após 11/11/2026: `LanguageModelBackend`, factory com fallback e wrapper JNI RKLLM estão implementados como caminho opcional. A flag fica desligada por padrão. Este checkout não tem o SDK Android RKLLM nem modelo `.rkllm`; portanto ainda não é possível compilar/testar o backend NPU aqui e não existe integração NPU comprovada. O mecanismo por `BuildConfig` seleciona NPU somente em build de bancada explicitamente habilitado, não detecta NPU por conta própria.

### Caminho C — Linux + llama.cpp CPU

É um protótipo de comparação simples, mas exige adaptar integração e distribuição para Linux. O projeto atual já prova o backend CPU dentro de Android, não num serviço Linux do Orange Pi.

## Recomendação

Primeiro escolher o OS pelo suporte comprovado de tela, toque, áudio, Wi-Fi/Bluetooth e GNSS na placa exata. Se o Android oficial for funcional e houver intenção de usar a placa atrás/ao lado da central, começar com Harumi Android + Qwen GGUF em CPU. Em seguida executar um experimento RKLLM isolado no OS recomendado pelo SDK (provavelmente Linux) com Qwen3.5 0.8B, medindo latência inicial, tokens/s, RAM, temperatura e consumo. Só integrar NPU depois de repetir o teste na imagem Android pretendida e confirmar a compatibilidade ABI/runtime/driver.

Começar benchmark com o mesmo prompt e modelo em: CPU llama.cpp atual; RKLLM CPU/GPU/NPU conforme suportado; e, se o formato estiver disponível, variante RKLLM do Qwen3.5-0.8B. Registrar modelo e hash, quantização, versão/runtime, OS/kernel/driver, contexto, frequência/temperatura, TTFT e tokens/s. Não usar “Gemma 4, 6 tokens/s” como especificação até identificar arquivo, conversão, quantização, backend, sequência e ambiente do vendedor.

## Voz e funções do sistema

O LLM pode permanecer offline. O ASR Vosk e o TTS Supertonic existentes também são locais no Android, mas microfone, saída de áudio e desempenho precisam de teste na placa. Mapas/rotas podem usar Internet conforme as funções atuais; ficar offline depende de instalar os pacotes regionais e glyphs documentados. GPS depende de receptor/driver. A IA não deve controlar ECU, atuadores, câmeras ou alimentação.

## Referências oficiais consultadas

- RKLLM e instruções/modelos: https://github.com/airockchip/rknn-llm
- Changelog de arquiteturas/modelos: https://github.com/airockchip/rknn-llm/blob/main/CHANGELOG.md
- Benchmark publicado pelo SDK (condições do fornecedor; não representa medição local): https://github.com/airockchip/rknn-llm/blob/main/benchmark.md
- Exemplo de build da API Android: https://github.com/airockchip/rknn-llm/tree/main/examples/rkllm_api_demo/deploy
- Build Android de llama.cpp: https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md

Referências e benchmarks foram consultados em 11/11/2026; compatibilidade e desempenho no Orange Pi comprado seguem não verificados.

# ADR-008: Conversa e voz locais, ações limitadas e diagnóstico de leitura

Status: aceita para desenvolvimento e teste em bancada; homologação física pendente.
Data: 02/11/2026.
Decisor de escopo: Lucas, que solicitou a integração no aplicativo.

## Contexto

Harumi roda no Android original da central do Subaru Impreza SW 1993. O processador, a ABI, os motores de áudio OEM e o protocolo de diagnóstico ainda não foram medidos no aparelho. O usuário quer conversar em português, ouvir voz feminina e pedir mapas/rotas.

## Decisão original (0.3.0)

- Qwen3.5-0.8B Q4_K_M executado por JNI com llama.cpp CPU, contexto de 2048 tokens, saída limitada a 128 tokens e duas threads. O modelo é carregado sob demanda.
- Reconhecimento offline Vosk com modelo português pequeno, iniciado por toque, permissão de microfone e duração limitada. Não há hotword nem escuta permanente.
- Kokoro INT8 via sherpa-onnx, voz pf_dora, ID 42 confirmado nos metadados do ONNX, idioma pt-br. Sem fallback automático para voz masculina ou serviço remoto.
- Ações conhecidas passam por parser local. O texto produzido pelo LLM não é executado como comando. Destinos viram dados codificados em intents documentadas, após confirmação nativa.
- Diagnóstico possui contrato de adaptador somente leitura, snapshot com fonte/instante/unidade e verificação de dados antigos. O adaptador padrão permanece desconectado. Não presumir OBD-II nem fabricar medições.
- Trabalho pesado fora da UI, operações serializadas, cancelamento e invalidação de respostas ao pausar. Áudio interrompido ao perder foco; microfone encerrado ao pausar.

## Alternativas

IA remota exigiria rede, autenticação e envio de voz/texto. Um modelo maior aumentaria memória e latência antes de conhecermos o SoC. Usar apenas o TTS padrão não garante voz feminina instalada. As opções escolhidas permitem testar o fluxo completo sem API paga ou rede.

## Consequências

O APK fica maior porque já inclui os modelos; a primeira execução prepara cópias privadas no dispositivo. Há bibliotecas somente arm64-v8a e x86_64. Desempenho, temperatura, voz em cabine e qualidade de transcrição precisam de teste na central. Não há serviço persistente de diagnóstico ou inicialização por ACC nesta versão: monitoramento enquanto a Harumi está ativa é apenas a base de integração; funcionamento contínuo no veículo depende de adaptador e homologação de energia.

P2 desenvolvido em bancada conforme a exceção expressa da especificação. HOME continua desabilitada; câmeras e MCU continuam fora da autoridade da IA.

## Situação atual (0.3.15)

Os valores da decisão original acima são históricos (contexto de 2048 tokens, saída de 128 tokens, duas threads, Kokoro pf_dora). Valores atuais conferidos no código:

- Contexto de 4096 tokens (n_ctx em harumi.cpp), prompt de até 3400 tokens, saída de até 384 tokens, até 4 threads e prazo de 60 s por geração.
- Voz Supertonic 3 INT8, speaker 2 (F3), velocidade 1.25, silêncio 0.72 e 24 passos, executada por sherpa-onnx 2.0.1.
- Reconhecimento Vosk small pt 0.3, com janela de 45 s e pausa de 1,8 s.

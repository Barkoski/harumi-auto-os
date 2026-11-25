# Harumi Auto OS 0.3.15-dev.1

## Quatro melhorias solicitadas

1. Captura: o aplicativo encerrava a escuta no primeiro resultado de segmento Vosk. Agora acumula segmentos e hipóteses parciais, mostra a transcrição e aguarda 1,8 s após um endpoint. Janela máxima de 45 s; Concluir fala envia manualmente o que foi ouvido. Foco de áudio exclusivo durante captura, cancelamento por perda de foco/pausa e callbacks vinculados à sessão para impedir resultados antigos. O modelo acústico continua Vosk pequeno pt; não há promessa de precisão perfeita no microfone físico.
2. Contexto/respostas: n_ctx 1024→4096; limite de saída 64→384 tokens; orçamento cooperativo 20→60 s. Histórico guarda até quatro pares completos dentro de 5000 caracteres, removendo turnos inteiros. Contagem real de tokens antes da geração mantém reserva de saída. Mensagens aceitam até 1600 caracteres. Removidos cortes arbitrários de resposta em caracteres. Texto é exibido enquanto o modelo gera; razão de término distingue EOS, limite, tempo e cancelamento. Resposta parcial ou final pendente como “Como posso ajudar com” exibe Continuar resposta. A fala usa a parte concluída quando a geração é parcial.
3. Ícones: aplicativos instalados fornecem os próprios ícones pelo PackageManager; a aba Instalados mostra os apps realmente acessíveis. Atalhos de Waze/Spotify ausentes recebem Instalar. Catálogo usa imagem nativa quando disponível e referências da loja ou ícones locais para os demais.
4. Interface: launcher inspirado na segunda imagem, com dock vertical, grade de ícones e faixa de mídia; mantém identidade Harumi escura/rosa, personagem e voz F3 aprovada. Sem reprodução fictícia: comandos de mídia vão ao player ativo do Android. Interface de fábrica continua disponível num botão nativo compacto. Câmeras, firmware e HOME preservados.

## Evidências

51 testes unitários sem falhas; lint sem erros e APK de bancada compilado. Teste de instrumentação SpeechCaptureRegressionTest passou no Android API30 x86_64: microfone emulado iniciou, primeiro segmento não encerrou a escuta, hipótese seguinte manteve captura, frase completa foi submetida. Os eventos de reconhecimento desse teste foram injetados; não é medição da precisão do microfone de Lucas.

UI em 2000x1200, 1280x720, 1024x600, 1024x520, 800x480 e 390x844: ícones carregados, navegação de painéis, transcrição, streaming e Continuação. Atlas e catálogo anteriores passaram em quatro resoluções. Android WebView83: ícones reais de 12 aplicativos da bancada, tela sem overflow. Não foi operado o LDPlayer do usuário.

Geração local real no Android de bancada: primeiras partes em 6,234 / 4,062 / 4,609 s; textos completos em 7,453 / 4,375 / 6,125 s. As três gerações chegaram a EOS; o teste de contexto lembrou Londrina na pergunta seguinte. Esses tempos são de texto nesta bancada, não da fala completa nem garantia no hardware físico. Evidência ai-launcher-0315-results.json.

## Limites restantes

O modelo 0.8B continua pequeno e pode responder de forma imprecisa; contexto maior não substitui capacidade ou base turística. Respostas longas podem levar mais tempo. GPS ao vivo, motor de rotas offline e diagnóstico físico continuam pendentes. A precisão da fala real deve ser conferida no microfone da central/emulador do usuário. O APK não instala apps de terceiros automaticamente.

Conversa, ASR e voz permanecem locais. Internet é usada somente pelos caminhos de mapas implementados na versão anterior. Nenhuma publicação, alteração de firmware ou ativação de HOME.

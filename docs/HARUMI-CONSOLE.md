# Harumi animada — 0.3.5-dev.1 — 02/11/2026

Personagem escolhida por Lucas no vídeo gemini_generated_video_32078480.mp4. Original preservado em reference-assets; cinco trechos locais sem áudio acompanham saudação, espera, escuta, processamento e resposta falada. Os estados vêm do controlador nativo: preparar a voz ainda é processamento; falar começa na reprodução de áudio. Comando duplicado não troca o estado de uma captura/fala em andamento.

A personagem permanece visível ao lado da conversa. Um único elemento de vídeo muda de posição entre HOME e conversa. Reprodução pausa com app em segundo plano, painéis sobrepostos e preferência por movimento reduzido. Vídeos locais H264 baseline 256×352; nenhum áudio do vídeo original interfere na voz F3 aprovada.

O movimento da boca pertence aos trechos do vídeo e não é sincronização fonética por palavra. O fundo quadriculado opaco está gravado no original e foi preservado.

Verificação: build debug concluído; 27 testes unitários passaram; lint sem erros. Navegador: quatro estados reproduzidos, personagem na conversa, pausa/retomada e movimento reduzido. Android 11/API 30 emulado: vídeo em espera, escuta real do microfone com personagem visível, animação durante TTS real, pausa em segundo plano e retomada passaram. Layouts 1024×600, 1024×480, 800×480 e celular verificados. A demonstração alterna os estados explicitamente e é identificada como demonstração; não representa conversa real.

APK 0.3.5 inclui as animações. Codecs, desempenho e consumo na central física ainda precisam ser medidos. Diagnóstico físico permanece desconectado; HOME desabilitada. Não houve alteração de firmware, publicação ou envio do vídeo a serviços externos.


Atualização 0.3.6: o quadriculado foi removido dos clipes usados pelo app e substituído pela cor do painel; o original permanece intacto. A interface recebeu o redesign descrito em INTERFACE-RETRO-036.md.

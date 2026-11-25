# Validação — voz 0.3.1-dev.1 — 02/11/2026

Voz selecionada pelo usuário: opção 2, Supertonic 3 F3, speaker 2. Preserva o timbre nativo dessa voz. Idioma pt, 24 passos de geração, velocidade 0.99 e silêncio 1.08; sem mudança artificial de pitch.

O texto escrito continua Harumi. SpeechPronunciation troca apenas a palavra isolada Harumi por Rarumi ao sintetizar, conforme a pronúncia solicitada. O texto da conversa, os rótulos e o prompt do modelo não são alterados. O parser aceita Harumi e Rarumi como chamada inicial em comandos conhecidos.

## Verificado

- Build debug arm64-v8a/x86_64 concluído.
- 13 testes unitários passaram: roteamento, comandos e quatro verificações de pronúncia/limites de palavra.
- Lint: zero erros, cinco avisos já documentados da configuração Android/WebView/dependências.
- Instalação e teste integrado no Android 11/API 30 emulado, sem Wi-Fi ou dados: OK (1 test).
- Síntese efetiva pela nova biblioteca sherpa-onnx 2.0.1, callback JNI tipado e voz Supertonic F3.
- Campo enviado à fala: Rarumi.
- Amostra fixa sintetizada no Android: 8.63 s; síntese/preparação no teste: 4279 ms. Não extrapolar esses tempos para a central ARM.
- Transcrição pelo Vosk: “abra o mapa para encontrar o meu destino”; convertida em ação MAP permitida.
- Teste de UI da conversa, confirmação de rota, diagnóstico desconectado, cancelamento e recuperação: cinco verificações passaram. O arquivo assistant-ui-results.json contém os resultados.

A naturalidade subjetiva e a pronúncia percebida dependem da avaliação auditiva do usuário. Microfone/alto-falantes da central e cabine não foram homologados. O diagnóstico físico permanece desconectado e HOME desabilitada.

## Atualização

O APK mantém applicationId e assinatura debug do projeto. A preparação dos modelos usa models-v2, para não confundir o pacote novo com o marcador antigo do Kokoro. Os modelos privados anteriores não foram apagados automaticamente. Reserve espaço adicional na atualização; em instalação limpa, pelo menos 3 GB livres continuam sendo a recomendação de bancada.

As versões anteriores e suas evidências são históricas. O APK 0.3.1 substitui a voz anterior por F3; não modifica firmware nem funções OEM.

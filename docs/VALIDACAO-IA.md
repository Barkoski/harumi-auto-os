# Validação da IA: 02/11/2026

## Executado

- APK debug compilado para arm64-v8a e x86_64, com otimização nativa Release. Build SUCCESSFUL em build-ai.log.
- Nove testes unitários: três de roteamento e seis de interpretação de comandos, incluindo destino com acentos, rejeição de links e comando reconhecido no áudio sintético.
- Lint: zero erros e cinco avisos (target fixado, atualizações de dependências e JavaScript necessário à UI própria).
- Teste instrumentado real no Android 11/API 30, x86_64, 4 GB emulados, WebView 83.0.4103.120. Wi-Fi e dados desligados; o app não possui permissão INTERNET. ai-instrumentation.log registra OK (1 test).
- Qwen efetivamente carregado e gerando resposta: 8534 ms no teste, incluindo carregamento e contexto. Esse valor não prevê o desempenho na central ARM.
- Kokoro feminino pf_dora: amostra sintética de 6.12 segundos, sintetizada em 4867 ms no teste (inclui preparação). Amostra WAV gerada no Android.
- Reconhecimento de áudio sintético em português e conversão da transcrição em ação MAP permitida. Transcrição: “abril mapa para encontrar o meu destino”. Há erro de reconhecimento (“abril” por “abra”); uma correção restrita desse comando foi adicionada ao parser e testada. Não é avaliação estatística da precisão do ASR.
- Cinco verificações pela tela Android: conversa WebView→JNI→modelo→voz; confirmação nativa de destino; diagnóstico desconectado; cancelamento de turno; retorno ao launcher pelo botão nativo.
- Captura com microfone emulado silencioso iniciada localmente e cancelada ao ir para HOME; retorno em estado pronto. Permissão de teste revogada depois. Isso não valida fala real em cabine.
- Navegador: 1024×600, 1024×480, 800×480 e 390×844. Não houve overflow horizontal; celular tem rolagem vertical.

## Não executado ou não implementado

Microfone real em cabine, ruído, alto-falantes da central, chamadas/rádio OEM, CPU ARM física, consumo/temperatura, ACC/suspensão, ré/360° e qualquer leitura de ECU. Sem adaptador Subaru validado, não há monitoramento real do veículo. A rota foi verificada até a confirmação; geocodificação, trajeto e navegação dentro de um app de mapas não foram homologados no emulador.

O monitor de leitura tem polling apenas enquanto a Harumi está ativa, com adaptador padrão desconectado. Serviço persistente e inicialização por ACC não foram implementados. Nenhuma função OEM foi substituída. T01–T26 da central continuam NOT_RUN; as evidências de bancada não alteram essa matriz.

## Reprodução

JDK 17, Gradle 8.7, AGP 8.6.1, SDK 35, NDK 27.2.12479018, CMake 3.22.1. `gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug`. Instalar APK e APK de testes em emulador autorizado e executar `adb shell am instrument -w com.harumi.autoos.test/androidx.test.runner.AndroidJUnitRunner`.

scripts/test_assistant_ui.py verifica os fluxos pela WebView de debug no emulador de bancada. Depuração WebView habilitada apenas quando o APK é debuggable. Nenhum segredo, chave de assinatura ou configuração local de SDK acompanha os fontes.

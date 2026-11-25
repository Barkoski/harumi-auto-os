# Validação — 02/11/2026

## Evidências

- build-debug.log: assembleDebug, testDebugUnitTest e lintDebug concluídos.
- unit-tests.xml: 3 casos JUnit, zero falhas/erros: comandos arbitrários, módulos e roteamento.
- lint-results-debug.txt: zero erros e três avisos: versões mais recentes de dependências e JavaScript habilitado. Versões fixadas; JS restrito à UI própria.
- android-smoke-results.json: 11 verificações em Android API 30 e WebView 83.0.4103.120.
- ui-test-results.json: interface/configuração no navegador, sem interpretar HTML em nomes vindos do estado nativo.

## Integração emulada

Ponte e estado inicial; layout Android 1024×600 com WebView 1024×520; diagnóstico; associação de Settings como NAV apenas para teste; lançamento; persistência após force-stop; limpeza; rejeição de comando desconhecido; bloqueio de navegação externa; abertura sem Wi-Fi/dados; retorno pelo botão nativo ao Launcher3. Associação de teste limpa.

O teste externo utilizou domínio inválido e a navegação foi bloqueada. Não constitui auditoria completa da ponte. Não houve homologação de STT, TTS, telefonia, câmeras, energia, API 26 ou aparelho físico.

T01–T26 em homologacao/testes.csv permanecem NOT_RUN para homologação na central. Resultados emulados são separados.

## Ferramentas

JDK Azul Zulu 17; Gradle 8.7; AGP 8.6.1; SDK 35; Build Tools 34.0.0; emulador Android 11/API 30. Downloads em ../work/android-toolchain, fora do pacote fonte. Sem alteração global do PATH.

## Fontes técnicas

- https://developer.android.com/studio
- https://developer.android.com/build/releases/agp-8-6-0-release-notes
- https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
- https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges

Especificação preservada em especificacao/HAO-TECH-001-v0.2.0.txt.

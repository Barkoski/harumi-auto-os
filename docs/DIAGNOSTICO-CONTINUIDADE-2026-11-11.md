# Diagnóstico de continuidade — 11/11/2026

Escopo: somente Harumi Auto OS deste repositório. A placa Orange Pi 5 anunciada e os acessórios descritos pelo Lucas ainda não foram conectados nem identificados por software. Este diagnóstico registra o checkout e a evidência disponível; não homologa o hardware automotivo.

## Estado do checkout

- Branch `revisao-noturna-2026-11-03`, HEAD `d6ff538` (apps Claude/ChatGPT e apresentação em Ajustes). Working tree estava limpo durante a inspeção.
- Não há `AGENTS.md` na raiz nem em subpastas do projeto. O único encontrado pertence ao vendor `vendor/llama.cpp` e não rege o código próprio.
- Os documentos de referência mais recentes no topo ainda citam 0.3.15, mas o código e commits posteriores já incluem novos módulos de cockpit, mapas e rotas. Há registros incompatíveis entre documentos: `ENTREGA-0315.md` e `STATUS.md` chamam rota offline de pendente; `MAPA-OFFLINE.md` afirma teste funcional em Android 14 x86_64.

## Implementado no código (não equivale a homologação)

- Conversa com modelo local via llama.cpp JNI, Vosk para ASR, Supertonic para TTS; interface web local e comandos tipados. Evidência histórica de bancada está em `docs/ENTREGA-0315.md` e `docs/evidencias/ai-launcher-0315-results.json`.
- Atlas/cockpit, mapa vetorial MapLibre, busca/planejamento de destinos, cache de tiles e gateway de rede com hosts fixos. A interface informa origens e distingue resultados online/offline.
- `OfflineRouter` com GraphHopper e `OfflineSearch` com índice SQLite FTS4 existem e são chamados como fallback de rede em `MapNetworkGateway`. O grafo esperado é `rotas/grafo-brasil-v2`; a busca espera `mapas/busca-brasil.sqlite`.
- Feed GNSS Android, permissão pedida ao iniciar navegação, avaliação de qualidade e replay NMEA para desenvolvimento existem. GNSS real depende do receptor efetivo e ainda não foi homologado na central.
- Existe protótipo de transporte/adaptador Subaru SSM1 somente leitura, fake serial e parâmetros candidatos. Sem interface física e protocolo/endereço confirmado, não fornece diagnóstico real. Comandos do LLM não atuam em ECU/atuadores.

## Evidência e limites

- O histórico de `docs/MAPA-OFFLINE.md` reporta rota GraphHopper exercitada em emulador Android 14 x86_64, mas o pacote de grafo usado não está neste checkout. A evidência anexada e a execução não foram reproduzidas nesta sessão.
- `data/brazil/harumi-brazil.sqlite` tem 2.941.317.120 bytes e integridade indicada como `ok`, mas é banco-fonte/analítico; não é o índice `busca-brasil.sqlite` esperado pelo app. Esse índice e o grafo não aparecem no checkout. O `brasil.mbtiles` e as fontes glyph mencionados na documentação também não estão em `app/src/main/assets` nem em `data/brazil`.
- O manifest pede Internet para provedores de mapas/rotas/busca. Conversa, ASR e TTS são documentados como locais. Mapa, geocodificação e rota podem consultar rede; seus fallbacks offline são condicionais aos pacotes acima. Tiles rasters/fontes ainda podem depender de rede.
- Android API/ABI/driver, NPU/RKLLM, aceleração llama.cpp, 6 tokens/s alegados pelo vendedor, temperatura, alimentação automotiva, ventoinha/fonte, RTC, Wi-Fi/Bluetooth, toque, câmera de ré/360, áudio OEM e ACC não foram testados no Orange Pi ou no Subaru.
- Central Android previamente possuída: documentos antigos referem Fóton como hipótese comercial, mas entrada de vídeo e retorno de toque não estão confirmados; firmware e HOME seguem preservados/desabilitados.
- `docs/homologacao/testes.csv` mantém T01–T26 como `NOT_RUN`; isso continua sendo a referência para homologação física.

## Verificação tentada nesta sessão

`./gradlew.bat :app:testDebugUnitTest` baixou/abriu o Gradle Wrapper 8.7, mas falhou na configuração antes de compilar: a sessão usa Oracle Java 8 (`java version 1.8.0_503`), incompatível com AGP 8.6.1, que pede JDK 11+ e cujo projeto documenta JDK 17. Não há JDK 17 instalado nos caminhos usuais inspecionados. Nenhum APK ou teste novo foi produzido nesta sessão.

## Menor próximo passo técnico

Preparar, fora do APK, um pacote de teste regional pequeno (por exemplo, Londrina e entorno) com índice de busca e grafo gerados a partir de fontes identificadas, manifesto/hash e instalação/cópia simples; rodar busca e duas rotas em modo avião no emulador com JDK 17. Só depois medir memória, armazenamento, tempo de carga e rota offline em ARM64. Antes de usar/destruir o SSD NVMe comprado, preservar e verificar uma imagem/cópia integral do sistema que veio nele.

## Sequência de bancada Orange Pi

1. Identificar a placa por serigrafia e leitura local de `uname`, `getprop`, `dumpsys package`, ABI, API, kernel, armazenamento e dispositivos USB; registrar foto/versão da imagem.
2. Sem formatar o NVMe, criar imagem bruta, verificar hash e fazer teste de restauração em mídia separada.
3. Confirmar fonte, refrigeração ativa/passiva sob carga e limites de temperatura antes de inferir estabilidade.
4. Compilar primeiro variante ARM64 CPU; testar LLM, ASR e TTS sem rede. Tratar RKLLM/NPU como experimento separado por modelo/runtime suportado, com resultados e consumo medidos.
5. Testar GPS, Wi-Fi/Bluetooth, touchscreen/retorno, áudio e câmera em entradas isoladas. Planejar alimentação automotiva protegida, ACC e desligamento controlado antes de instalar no carro.
6. Manter câmera/energia/diagnóstico fora do controle do LLM e repetir os gates OEM antes de qualquer HOME/launcher padrão.

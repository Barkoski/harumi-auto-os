# Compatibilidade e core: Aikon Fóton G3

Pesquisa de 02/11/2026. Identificação informada por Lucas: F09-88256/360/G3. O anúncio estava cadastrado como Generic/FOTON G3; esse código também existe no catálogo oficial Aikon. Isso identifica a referência comercial, não autentica o aparelho comprado.

## O que a fonte oficial confirma

A [ficha da Aikon](https://aikontechnology.com/produto/09-88256-360-g3/) anuncia tela de 9 polegadas, matriz 2000×1200, oito núcleos a 2,7 GHz, RAM de 8 GB e armazenamento de 256 GB. Também descreve Android, Bluetooth 5.1, Wi-Fi em duas bandas e quatro câmeras 1080p. A página menciona divisão de tela condicionada ao aplicativo e funções de projeção CPAA. Não informa Android/API exatos, ABI, identificação da MCU, SoC ou protocolo público de controle das câmeras.

O fabricante distingue receptor GPS de software: não promete navegador incluído. Há anúncios de revendedores que dizem fornecer apps e atribuem Android 14/UIS7870 a variantes da família. Esses dados não foram usados como confirmação da unidade de Lucas: a descrição fornecida e a página oficial não comprovam esses detalhes. Não baixar firmware com base nessa hipótese.

A resolução de imagem indicada é uma matriz de pixels; não deve ser usada como se fosse a densidade Android em dpi. Mediremos área útil e densidade no aparelho. CPAA/CarPlay não equivale a Android Automotive OS ou a um APK Android do Apple Maps.

## Qual APK usar

Não existe um formato exclusivo de APK Aikon/ZK. O pacote precisa atender ao Android/API, às arquiteturas aceitas pelo sistema, às dependências e à assinatura. Um processador de 64 bits não basta para provar que o Android instalado aceita apps ARM64. A [documentação de ABI do Android](https://developer.android.com/ndk/guides/abis) diferencia ARM32/armeabi-v7a, ARM64/arm64-v8a e x86_64.

O APK completo Harumi 0.3.9 é um APK único assinado de bancada, com bibliotecas ARM64 para a central e x86_64 para emulador, mínimo API 26/Android 8, target 34. Não inclui armeabi-v7a. A instalação e a IA não estão homologadas se a central aceitar somente 32 bits. A validação Java de compatibilidade não contorna uma instalação rejeitada pelo Android.

Por isso acompanha um verificador separado, sem bibliotecas nativas/modelos: Harumi Compatibilidade, Android 8+, cerca de 18 KB. Ele pode coletar os dados em sistemas ARM32 ou ARM64 sem depender da instalação da IA. Os valores são declarações do sistema, não autenticação física. O exportador local usa o seletor Android de arquivos; não solicita acesso geral ao armazenamento nem envia o relatório.

Para apps distribuídos pela loja, usar a Play Store quando disponível/certificada. Um arquivo .aab não é um APK instalável. Quando a distribuição usa splits, é necessário o conjunto compatível, não apenas base.apk. [Android App Bundles](https://developer.android.com/guide/app-bundle/app-bundle-format).

## Matriz inicial de aplicativos

| Aplicativo | Requisito oficial pesquisado | Integração e verificação pendente |
|---|---|---|
| Google Maps | Android 9+ para atualizações atuais | Detectar instalação, abrir, entregar destino, GPS e voz na central |
| Waze | Android 10+ | Detectar, entregar destino e testar Internet/GPS durante navegação |
| Spotify | Android 7+ | Abrir app; conta e reprodução sob responsabilidade do Spotify; testar áudio e interrupções |
| Apple Maps | Caminho documentado via iPhone/CarPlay; também há versão web | Não tratar como APK Android nativo. Testar CPAA OEM separadamente; não controlado pela Harumi |
| Navegador offline/OEM já adquirido | Depende do produto, versão e licença | Listar no seletor ou configurar favorito manual; validar intent de destino e mapas licenciados |
| Câmeras, rádio, DSP, telefonia e CPAA OEM | Dependem do firmware e das integrações da central | Preservar os aplicativos originais; abertura do ícone não comprova ré automática, áudio ou retorno |

Fontes oficiais: [Google Maps](https://support.google.com/maps/answer/3096703?co=GENIE.Platform%3DAndroid&hl=en), [Waze](https://support.google.com/waze/answer/6071125?hl=en), [Spotify](https://support.spotify.com/ml-en/article/supported-devices-for-spotify/), [Apple CarPlay](https://support.apple.com/en-mide/guide/iphone/iph215b053f6/ios), [Apple Maps web](https://support.apple.com/en-in/120585). Requisitos pesquisados nesta data, sujeitos a alterações e filtros da loja.

Android mínimo é apenas um requisito, não aprovação completa. A [certificação Play Protect](https://support.google.com/googleplay/answer/7165974?hl=pt-BR) deve ser conferida em Play Store > Configurações > Sobre. Presença dos pacotes Google não demonstra certificação. O coletor registra Store/Services, não tenta certificar a unidade.

## Core: próximos critérios de aceite

1. **Perfil real:** abrir Harumi Compatibilidade na central, salvar JSON e conferir Android/API, ABIs, processo, RAM, espaço, WebView, nomes/versões dos apps e identificação OEM. Confrontar com etiqueta e tela da MCU; esses últimos não são obtidos por API universal.
2. **Runtime de IA:** instalar APK completo apenas quando os pré-requisitos forem atendidos. Medir carregamento frio/quente, RAM e pressão de memória, tempo até a primeira resposta e síntese, consumo/temperatura e cancelamento. Qwen3.5-0.8B quantizado é candidato existente, não desempenho garantido pelos oito núcleos anunciados.
3. **Integração por aplicativo:** testar mapas e mídia reais. O seletor já suporta múltiplos apps e favoritos; nomes falados como Waze/Spotify ainda abrem a categoria. Controle específico por nome, entrega de destino e comandos de reprodução precisam de contratos/testes por app, sem comandos arbitrários do LLM.
4. **Áudio e microfone:** validar voz em cabine, foco/volume com rádio e Spotify, chamadas Bluetooth e instruções de rota. Verificar conflito com Adam Pro antes de considerar hotword. Escuta atual permanece por toque.
5. **Ciclo automotivo:** testar ré/360° com IA ativa e travada, sair para OEM, ACC, suspensão/retomada e uso prolongado. HOME permanece desabilitada até aprovação física. Não criar inicialização persistente que prejudique câmeras ou bateria.
6. **Diagnóstico Subaru:** identificar interface elétrica/protocolo de leitura do veículo antes de implementar transporte. Impreza 1993 não deve ser tratado automaticamente como OBD-II. Hoje o adaptador segue desconectado; nenhuma leitura de ECU foi implementada.
7. **Compatibilidade futura:** Android 14/API 34 ainda não testado em central/emulador neste trabalho. Para Android 15+ com páginas de 16 KiB, auditar/recompilar todas as dependências nativas e testar em ambiente correspondente; hoje apenas página de 4 KiB foi observada na bancada. [Orientação Android](https://developer.android.com/guide/practices/page-sizes).

## Entrega e limites

O core avançou nesta etapa com política verificável de ABI/API, inventário e exportação, além de pesquisa específica da referência comercial. Não há central física conectada: compatibilidade com o aparelho de Lucas continua pendente de medição. O relatório de bancada é identificado como x86_64 e não é relatório da Fóton G3. Não houve alteração de firmware, root, instalação de apps comerciais de terceiros ou publicação.

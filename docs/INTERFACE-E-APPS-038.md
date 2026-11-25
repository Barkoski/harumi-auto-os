# Harumi Auto OS 0.3.8-dev.1

Estrutura da primeira interface restaurada: três botões grandes à direita, saudação, personagem e comando de voz à esquerda. Personalização da Harumi original em carvão/preto e rosa suave, com pétalas animadas e linhas de fundo discretas. Sem o menu lateral ou a decoração retrô rejeitados. Efeitos respeitam a preferência de movimento reduzido. Personagem continua sem quadriculado, composta sobre #1b1b21; voz F3 mantida.

## Aplicativos

Harumi é um aplicativo sobre o Android stock da central, não uma ROM com apps comerciais incluídos. A imagem de bancada instalada é Android 11/API 30 AOSP, tag default/x86_64. Inventário real salvo em docs/evidencias/android-bench-packages.txt; Maps, Waze e Spotify não estavam instalados. Não há inventário da central física conectada.

Os botões Navegação e Música agora abrem uma lista dos aplicativos instalados reconhecidos na categoria, com opção Outros apps para aplicativos OEM que não anunciem corretamente sua categoria. Maps, Waze, Spotify e outros só aparecem se instalados e visíveis ao Android. Aplicativos favoritos configurados continuam disponíveis e identificados, sem ocultar alternativas. A Harumi não inclui lojas, contas, assinaturas ou APKs desses serviços; Apple Maps não foi localizado ou instalado na bancada.

Categoria de mapas usa handlers de geo e pacotes conhecidos; música usa MUSIC_PLAYER e pacotes conhecidos. A configuração manual permite incluir apps OEM. Encaminhamento de destino utiliza seletor de mapas compatíveis com geo; google.navigation é alternativa apenas quando não há handler geo. Cada app decide como tratar o endereço. Comandos de voz com nome de app continuam abrindo o seletor da categoria, não uma seleção automática por nome.

## Verificação

Build debug concluído; 27 testes unitários passaram; lint sem erros. Layouts 1024×600, 1024×480 e 800×480 sem rolagem. Celular 390×844 permite rolagem vertical. Animações e conversa verificadas em navegador, incluindo movimento reduzido. Android 11 emulado: múltiplos navegadores e players testados com quatro atividades fictícias, preservação do favorito e acesso a outros apps; fixtures removidas após o teste e não incluídas no APK de entrega. A seleção foi testada com fixtures, não com Maps/Waze/Spotify reais. Reprodução da personagem, microfone, TTS e pausa/retomada também testados no APK final emulado.

Central física, diagnóstico e integração OEM permanecem pendentes; HOME desabilitada. Não houve modificação de firmware ou publicação.

# Validação: 0.3.3-dev.1: 02/11/2026

## Entregue

Botão Falar com Harumi na tela inicial, com abertura da conversa e início deliberado da escuta offline. Texto continua disponível separadamente. Voz F3 aprovada e pronúncia Rarumi preservadas.

Painel Conexões com o celular: status da rede, instruções de compartilhamento por Wi-Fi, Bluetooth e USB, acesso às telas Android de Wi-Fi, Bluetooth e redes/conexões. Comandos “abra o Wi-Fi”, “abra o Bluetooth” e “abrir conexão USB” abrem essas configurações, sem prometer ativação automática.

ConnectivityMonitor acompanha a rede padrão enquanto a Harumi está ativa. “Internet disponível” exige capacidades INTERNET e VALIDATED observadas no Android. Conexão sem validação, portal de autenticação e ausência de rede têm mensagens diferentes. Não usa pareamento Bluetooth ou cabo físico como prova de acesso à Internet. USB só é identificado como tal quando o Android o reporta; em outras ROMs pode ser apresentado como Ethernet/cabo.

## Permissões e limites

Adicionada apenas ACCESS_NETWORK_STATE (normal) para observar a rede. RECORD_AUDIO continua condicionado à ação e à permissão do usuário. Sem leitura de senha/SSID, lista de dispositivos pareados, controle privilegiado de tethering, alteração de rede em silêncio, root ou flash. Não foi adicionada permissão INTERNET ao app: a IA e a voz são locais; os apps de mapas/mídia usam suas próprias conexões.

Bluetooth PAN e USB tethering dependem de suporte do celular, porta, drivers e firmware da central. Android Auto/espelhamento não comprova compartilhamento de Internet. O painel orienta a configuração; não implementa drivers ou uma pilha de compartilhamento própria. Wi-Fi, Bluetooth e USB não foram homologados com celular e central físicos.

## Executado

- Build debug arm64-v8a e x86_64 concluído; 22 testes unitários passaram; lint sem erros, cinco avisos conhecidos.
- Nove verificações no Android 11/API 30 emulado: status offline; painel e três caminhos; abertura das três telas Android; atualização para Internet disponível por Wi-Fi; botão Falar da HOME iniciando captura offline; cancelamento/retorno sem overflow; comando de Wi-Fi encaminhado pela conversa e executado após resposta local.
- A permissão de microfone usada no teste foi revogada depois. Captura emulada silenciosa não valida ruído e microfone em cabine.
- Interface verificada em navegador em 1024×600, 1024×480, 800×480 e 390×844. Sem overflow horizontal; celular usa rolagem vertical.
- Acrescentados identificadores de versão aos ativos e desabilitado cache da WebView para impedir mistura da interface nova com JavaScript/CSS antigos após atualização.

Ré/360°, áudio/chamadas OEM, ACC/energia e diagnóstico físico continuam pendentes. HOME permanece desabilitada e firmware preservado. O teste específico de IA/voz da 0.3.2 permanece histórico; esta alteração foi validada pelos testes direcionados de voz na HOME e conectividade.

## Fontes Android

- https://developer.android.com/reference/android/provider/Settings
- https://developer.android.com/reference/android/net/NetworkCapabilities
- https://developer.android.com/training/monitoring-device-state/connectivity-status-type

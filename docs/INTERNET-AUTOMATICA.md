# Internet e interface — 0.3.4-dev.1 — 02/11/2026

## Correção de escopo de Lucas

O usuário quer Internet disponível automaticamente ao entrar/conectar o celular ao carro, sem escolher transporte dentro da Harumi. Usa vários aparelhos: iPhone 15, iPhone 12, Xiaomi e Motorola, entre outros. Não vincular o produto a uma marca. O cabo será usado principalmente para carregar; retirar a opção de Internet USB.

## Implementado

- Removida a opção USB, a ação connection.phone e o comando nativo de configuração USB.
- O botão passa a ser Internet. O painel apresenta o status automático e mantém Wi-Fi/Bluetooth recolhidos como configuração inicial, sem seletor de transporte diário.
- A Harumi continua acompanhando a rede padrão do Android, incluindo troca/reconexão observada. Não é necessário selecionar um transporte no app.
- A voz aprovada, o botão Falar e os comandos Wi-Fi/Bluetooth foram preservados.

## Limite explícito — automação universal ainda não entregue

Observar a rede e usar o transporte escolhido pelo sistema não equivale a ativar o compartilhamento no telefone. O aplicativo não habilita à distância o roteador de qualquer iPhone/Android ao parear, carregar ou conectar o cabo. Não foi criada automação universal de telefone, serviço Bluetooth PAN, driver ou conexão privilegiada.

O caminho comum é configurar uma vez na central as redes Wi-Fi dos celulares e permitir que o Android reconecte quando estiverem disponíveis, com Wi-Fi ligado e roteador do telefone ativo. Bluetooth para Internet depende do suporte a compartilhamento de rede no celular e na central; pareamento de chamadas/áudio é diferente.

Funcionamento sem nenhuma ação em celulares de várias marcas ainda exige verificar as condições de cada sistema e o firmware da central. Internet independente de telefone requer verificar se a unidade tem modem/entrada SIM e suporte de dados; os anúncios citados na especificação não comprovam isso no aparelho real. Não foi contratada conexão ou adquirido hardware.

## Verificação

Build debug arm64-v8a/x86_64 concluído, 22 testes unitários passaram e lint sem erros. Oito verificações no Android 11/API 30 emulado passaram: offline, painel com USB ausente e configuração recolhida, abertura de Wi-Fi e Bluetooth, reconexão observada por Wi-Fi sem seleção na Harumi, captura pela HOME, cancelamento/retorno e comando de Wi-Fi. O telefone físico e a central não estavam conectados. Capturas e resultados estão em evidencias/internet-034-results.json e imagens associadas.

## Fontes oficiais

- Reconexão a redes salvas com Wi-Fi ativado: https://support.google.com/android/answer/9075847?hl=pt-BR
- Ativação de ponto de acesso/tethering no Android: https://support.google.com/android/answer/9059108?hl=pt-BR
- No iPhone, Personal Hotspot/Allow Others to Join e condições de conexão: https://support.apple.com/en-us/111785
- Restrições ao controle de Wi-Fi por apps: https://developer.android.com/reference/android/net/wifi/WifiManager

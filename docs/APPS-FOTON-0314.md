# Apps da Fóton e integração Harumi: 0.3.14-dev.1

Pesquisa em 03/11/2026. Nenhum aplicativo de terceiros foi instalado na central física ou no LDPlayer do usuário. Foram implementados catálogo, inventário real, abertura de apps, associação OEM e acesso à loja oficial. Os aplicativos continuam sendo pacotes separados no Android da central.

## Resultado da pesquisa

| Referência | O que sustenta | Limite |
|---|---|---|
| Manual oficial da linha Fóton (2024), pp.5–24 e 46–54 | Funções OEM e instalação pela Play Store; cita apps de terceiros como exemplos | Manual da linha, não inventário de uma unidade F09-88256/360/G3 |
| Anúncio F09-88256/G3 do vendedor A1 Multimídias, reproduzido pela Atech | Anuncia iGO, Waze, Netflix, Spotify, YouTube, Maps, Chrome e Play Store | Composição do vendedor; não prova padrão universal de fábrica nem a unidade do usuário |
| Manual oficial Próton (2024) e suporte Próton G3 | Comparação de outra linha Aikon: escolha de navegador e instalação via loja | Comparação de linha, não inventário da Fóton |

A lista comercial foi usada como referência; não há base para afirmar que todos os mesmos apps vêm em qualquer Fóton. A documentação orienta instalar um navegador compatível. A central física precisa ser inventariada para confirmar pacotes, versões, licenças e compatibilidade.

## Catálogo implementado

7 entradas Android: Google Maps, Waze, Spotify, YouTube, Chrome, Netflix e Torque. Torque Lite é o destino da loja; a edição mencionada no manual não foi identificada. 17 entradas OEM: Play Store, iGO/navegador de fábrica, Rádio, Telefone/Bluetooth, Música local, Vídeo local, Equalizador/DSP, CPAA/CarPlay/Android Auto, Câmeras/360°, AUX, Fotos, Pastas, Assistente touch, Conduzir/volante, Adam, Monitor GPS e Ajuda.

O catálogo não embute APKs de terceiros. Apps comuns são identificados pelo pacote da página oficial da Play Store. Para funções OEM com pacote desconhecido, o usuário associa um aplicativo visível da unidade: não houve adivinhação de nomes de pacote, extração de firmware ou tentativa de instalar APK de outra central. Ausência de atividade acessível pode exigir a interface original.

Aplicativos → Apps Android abre o existente ou sua página na loja. A loja pode pedir login e confirmação e verifica disponibilidade no aparelho. Apps OEM não têm botão de download genérico; são preservados no Android original. Ver todos os instalados lista atividades exportadas, habilitadas e acessíveis; não inclui pacotes sem interface.

## GPS gratuito

Para posição real, o Android oferece LocationManager/GPS_PROVIDER, usando receptor GNSS, permissão e sinal de satélite; não exige chave de um serviço externo. Isso não fornece mapa nem cálculo de rotas. A implementação de acompanhamento GPS não foi incluída nesta versão. O mapa Harumi 0.3.13 continua com OSRM online experimental e tiles OSM, com suas políticas de uso.

## Validação

45 testes unitários e lint/assembleDebug aprovados. Catálogo testado em 1024x600, 1024x480, 800x480 e 390x844: estado de prévia sem fingir instalação, troca de grupos, ações por ID e fechamento. Android API30 x86_64 WebView83 em bancada separada: status real de apps ausentes, fallback sem Play Store para a página oficial no navegador, seletor OEM e lista de apps existentes. Nenhum download/instalação externa ocorreu nesses testes. Nenhuma homologação física da Fóton foi realizada.

## Fontes

- https://aikontechnology.com/wp-content/uploads/2024/05/Manual-Aikon-Foton.pdf
- https://atecheletronica.com/shopping/multimidia-universal-aikon-foton-g3-8256gb-octacore-4g-9p-58211572449
- https://aikontechnology.com/central-de-ajuda/i-cartablet/foton/
- https://aikontechnology.com/central-de-ajuda/i-cartablet/proton/
- https://aikontechnology.com/wp-content/uploads/2024/05/Manual-Aikon-Proton.pdf
- https://developer.android.com/reference/android/location/LocationManager
- URLs oficiais dos aplicativos: https://play.google.com/store/apps/details?id= seguido dos IDs fixos em assets/apps-catalog.json.

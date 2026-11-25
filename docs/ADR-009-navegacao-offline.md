# ADR-009: Navegação por GPS offline e integração com o celular

Status: Proposta, aguarda dados da central e decisão do Lucas.
Data: 03/11/2026.
Decisor: Lucas.

Convenção deste documento: tudo que não foi conferido em arquivo do projeto está marcado "(de memória, confirmar na fonte oficial)" ou "(estimativa)". Nada aqui foi pesquisado na internet.

## Contexto

Situação atual, conforme docs/MAPA-ROTAS-0313.md, docs/MAPAS-E-IA-LOCAL.md e docs/TERCEIROS.md:

- Há um atlas offline (dados e fotos dentro do app).
- O planejador de rotas usa o servidor demonstrativo OSRM (online) e tiles do OpenStreetMap (online). O próprio projeto já registra: sem SLA, uso pessoal experimental, sem navegação por GPS, sem instruções por manobra, sem recálculo, sem motor nacional offline.
- Destinos podem ser entregues a apps externos por intents geo: (já existentes; a entrega real de navegação curva a curva depende de cada app e ainda precisa de teste, conforme MAPAS-E-IA-LOCAL.md).
- O servidor demo do OSRM e os tiles públicos do OSM não servem para uso real/produção (de memória, confirmar na fonte oficial; as políticas estão citadas em TERCEIROS.md: operations.osmfoundation.org/policies/tiles/ e o wiki do demo server do osrm-backend).
- Existe data/brazil/harumi-brazil.sqlite (cerca de 2,9 GB, conforme data/brazil/index-report.json), com 5.571 municípios, 752.545 POIs e 7.608.387 registros de "road". O que há na tabela "road" (geometria? só nomes?) não foi conferido no schema.

## Objetivo

Um GPS que funcione sem o celular e sem internet, dentro da central, e que ainda assim aproveite o celular quando ele estiver presente (internet, destino, notificações).

## Opções

### A) Imediato: app externo offline via intent geo: (já existente)

- Organic Maps: licença Apache-2.0 (de memória, confirmar na fonte oficial).
- OsmAnd: o app é GPLv3 (de memória, confirmar na fonte oficial). Pode ser usado como app externo, instalado à parte. Não deve ser embutido nem ter código copiado para a Harumi, para não afetar a licença do projeto.
- Prós: sem desenvolvimento de motor; voz e recálculo já existem nesses apps; o fluxo de geo: já está implementado.
- Contras: a Harumi não controla a interface nem o áudio; a entrega do destino precisa de teste por app (já registrado em MAPAS-E-IA-LOCAL.md); o app instalado não deixa a Harumi ler seu armazenamento privado.
- Pendência: confirmar na central se o app roda (ABI, versão do Android, espaço, GPS).

### B) Dentro da Harumi, em fases

Peças:

1. Posição: LocationManager do Android com o receptor GNSS da central (se houver; ver pendências).
2. Desenho do mapa: MapLibre Native Android (licença BSD, de memória, confirmar na fonte oficial), com tiles vetoriais do OSM em PMTiles ou MBTiles. Brasil até zoom 14: 1 a 3 GB (estimativa).
3. Motor de rotas, duas candidatas:
   - GraphHopper: Apache-2.0, Java (de memória, confirmar na fonte oficial). Grafo de carro do Brasil: 1 a 3 GB (estimativa).
   - BRouter: licença a confirmar. Já citado em MAPAS-E-IA-LOCAL.md como exemplo de cálculo offline separado do desenho do mapa.
   - Valhalla: descartado por ora (C++ pesado; exigiria build nativo e mais teste).
   A escolha final exige teste em Android/ARM64 na central e revisão de licença e formato, como já diz MAPAS-E-IA-LOCAL.md.
4. Busca de destinos: o harumi-brazil.sqlite serve, em princípio, para buscar cidades e POIs offline. Não é motor de rota. Isso é uma suposição a conferir no schema.
5. Onde ficam os mapas: fora do APK, no armazenamento do app, instalados como pacote de região com manifesto, hash e instalação atômica (como descrito em MAPAS-E-IA-LOCAL.md). O APK não deve crescer com mapas.
6. Atribuição: "© OpenStreetMap contributors" (ODbL) visível na tela do mapa. Os pacotes devem vir de extratos licenciados para offline; não raspar tile.openstreetmap.org (política já citada em MAPAS-E-IA-LOCAL.md).

Contras: é o maior trabalho; o total (mapa + grafo + banco atual) pode exceder o armazenamento livre da central, que não foi medido; recálculo, instruções por voz e convivência com rádio e chamadas precisam ser construídos e testados.

### Integração com o celular (vale para A e B)

- Internet: hotspot do celular ou chip 4G na central. Sem isso, a central fica sem rede (o projeto tem docs/INTERNET-AUTOMATICA.md, não relido para este ADR).
- App companheiro (Android ou iPhone, a decidir): envia o destino por Wi-Fi local ou Bluetooth. Exige definir protocolo e pareamento. Não decidido.
- Notificações do celular só via app companheiro, com o usuário escolhendo o que aparece.
- Privacidade: destino e posição trafegam apenas entre celular e central.

## Decisão proposta

- A já: manter e testar o geo: com Organic Maps ou OsmAnd instalados na central.
- B em fases, somente depois que o kit confirmar o receptor GNSS. Fases sugeridas: (1) posição no mapa; (2) mapa offline de uma região; (3) rota offline entre dois pontos; (4) recálculo e voz; (5) companheiro do celular.
- Nada de B começa antes de a central responder às medições abaixo.

## Pendências e o que medir na central

- Existe receptor GNSS? Qual modelo, interface (serial, Android Location), taxa de atualização, tempo até o primeiro fix, desempenho em garagem e túnel?
- SoC, ABI (arm64-v8a ou outra), RAM, versão do Android, WebView.
- Armazenamento livre real e velocidade de leitura (tiles e grafo na casa de GB).
- Se o app externo (Organic Maps/OsmAnd) instala e navega de ponta a ponta com o intent atual.
- Schema de harumi-brazil.sqlite: o que há em "road"; se serve para busca de endereço.
- Licenças a confirmar: Organic Maps, OsmAnd, MapLibre Native, GraphHopper, BRouter, formatos PMTiles/MBTiles e o extrato de dados escolhido.
- Tamanhos de mapa e grafo (hoje apenas estimativas).
- Escolha do companheiro: Android ou iPhone.
- Coexistência com câmeras OEM, rádio e voz (ADR-001/003): a navegação não pode atrapalhar o retorno imediato à câmera de ré.

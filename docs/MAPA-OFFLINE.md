# Mapa offline do Brasil (Harumi Auto OS)

## O que é o arquivo

`brasil.mbtiles` é um único arquivo (cerca de 2 a 4 GB) com o desenho do mapa do Brasil inteiro (ruas, bairros, rios, prédios etc.) em pedaços chamados "tiles", do zoom 0 ao 14. Ele foi gerado no PC com o Planetiler, no mesmo formato (OpenMapTiles) que o app já usa pela Internet. Com ele na central, o mapa 3D carrega do próprio aparelho, sem gastar dados.

Funcionamento no app:

1. Com Internet, o app busca o mapa online, que é sempre o mais atualizado, e guarda uma cópia (cache).
2. Sem Internet, usa a cópia guardada daquele trecho, se houver.
3. Sem Internet e sem cópia guardada, lê do arquivo do Brasil. Se o pedaço não estiver no arquivo, mas estiver dentro dos limites do Brasil (por exemplo, mar aberto, onde não há nada para desenhar), mostra o pedaço vazio.
4. Se o arquivo não existir ou estiver com defeito, o mapa só funciona com Internet, como antes.

## Onde está no PC

`D:\HarumiMapa\saida\brasil.mbtiles`

## Onde ele precisa ficar na central

O nome tem de ser exatamente `brasil.mbtiles`, em uma destas pastas (o app olha nesta ordem):

1. `/sdcard/Android/data/com.harumi.autoos/files/mapas/brasil.mbtiles` (recomendada)
2. Pasta interna do app (`files/mapas/`), que só dá para usar via adb com `run-as` (build de debug). Não precisa para o uso normal.

Se a pasta `mapas` não existir, crie.

## Como copiar

Espaço livre necessário: o tamanho do arquivo mais uma folga (reserve pelo menos 5 GB livres na central).

### Sem terminal (cabo USB)

1. Ligue a central/celular ao PC por cabo USB e escolha "Transferência de arquivos" na notificação do Android.
2. No Explorador de Arquivos do Windows, abra o aparelho > Armazenamento interno > `Android` > `data` > `com.harumi.autoos` > `files`.
3. Crie a pasta `mapas` (se não existir) e copie `brasil.mbtiles` para dentro dela.
4. Se o Android esconder `Android/data`, abra o app Harumi Auto OS uma vez antes (isso cria a pasta `files`) ou use o gerenciador de arquivos da própria central. Em versões novas do Android o Windows às vezes não mostra `Android/data`; nesse caso use o adb abaixo.

### Com terminal (adb)

```powershell
adb shell mkdir -p /sdcard/Android/data/com.harumi.autoos/files/mapas
adb push D:\HarumiMapa\saida\brasil.mbtiles /sdcard/Android/data/com.harumi.autoos/files/mapas/brasil.mbtiles
```

A cópia de alguns GB demora vários minutos. Depois de copiar, feche e abra o app de novo para ele reconhecer o arquivo (se o arquivo não existia na primeira tentativa, o app verifica de novo a cada 30 segundos).

## Como saber se está funcionando

- No `logcat` (adb), filtre por `HarumiMap`:

  ```powershell
  adb logcat -s HarumiMap
  ```

  Ao abrir o mapa, aparece uma linha `offline mbtiles: name=... bounds=... minzoom=0 maxzoom=14 format=pbf file=... (N MB)`. Isso confirma que o arquivo foi aberto.
- Se aparecer `offline mbtiles: nao foi possivel abrir ...`, o arquivo está corrompido ou incompleto (cópia interrompida): copie de novo. O mapa continua funcionando pela Internet.
- Teste prático: ponha a central em modo avião, abra o mapa 3D numa cidade do Brasil e navegue com zoom entre 0 e 14. As ruas e prédios devem aparecer. Os textos (nomes de ruas) ainda dependem de fontes, veja abaixo.

## O que ainda depende de Internet

- Fontes dos nomes de ruas e lugares (glyphs): continuam sendo baixadas na primeira vez e guardadas em cache. Elas não estão no arquivo de mapa. Para ficar 100% offline faltam as fontes "Noto Sans Regular" e "Noto Sans Bold" em formato pbf; para o português bastam as faixas `0-255` e `256-511`. Dá para empacotá-las no app depois, mas isso exige um download (precisa da sua autorização).
- Rotas (OSRM) e busca de endereço (Nominatim): continuam online.
- Mapa fora do Brasil, e tiles de zoom acima de 14: não existem no arquivo.
- Mapa raster (tiles PNG do OpenStreetMap, se usado como alternativa): continua online com cache.

## Detalhes técnicos (para quem for mexer no código)

- Código: `OfflineTiles.java` (leitura do MBTiles, somente leitura, aberto uma vez de forma preguiçosa) e o ramo `vt/` em `MapNetworkGateway.java`.
- MBTiles usa linhas no padrão TMS (a linha 0 fica no sul); o app converte com `row = (1 << z) - 1 - y`.
- Os tiles do arquivo vêm comprimidos em gzip; o gateway descomprime antes de entregar ao WebView, como já fazia com os tiles online. Tiles lidos do arquivo não vão para o cache em disco.
- Tile ausente dentro dos limites (`bounds` do metadata) devolve resposta 200 com corpo vazio, tratada pelo MapLibre como tile sem camadas. Tile na borda dos limites (parcialmente fora) vai para a Internet.

## Rotas sem Internet (pasta `rotas/`) — EM VALIDAÇÃO

Status: FUNCIONANDO no emulador (Android 14 x86_64). Dois remendos foram necessários: (1) `MMapDataAccess` ajustada (`ByteBuffer` de Java 13; `scripts/build-graphhopper-android.sh` gera `app/libs/graphhopper-core-11.1-android.jar`); (2) peso de carro próprio sem Janino (`navigation/gh/HarumiGraphHopper.java`), porque o Janino gera bytecode JVM, que o Android não carrega. O mesmo peso é usado no import do PC e no app.

- Gerar o grafo no PC: `bash scripts/importar-grafo-v2.sh` (cerca de 6 min, -Xmx8g, saída em `D:\HarumiMapa\saida\grafo-brasil-v2`, 1,9 GB).
- Copiar os ARQUIVOS desse grafo para `Android/data/com.harumi.autoos/files/rotas/grafo-brasil-v2/` (o app cria `rotas/` e `grafo-brasil-v2/` ao abrir; abra o app antes e copie só os arquivos para dentro).
- Teste em build debug: um arquivo vazio `rotas/forcar-offline` faz rota e busca pularem a Internet (ignorado em build de produção).
- Copiar os arquivos da pasta `grafo-brasil` para `Android/data/com.harumi.autoos/files/rotas/grafo-brasil/` (o app cria `rotas/` e `grafo-brasil/` ao abrir; abra o app antes e copie só os arquivos para dentro, nunca crie a pasta por cabo/adb).
- Política: Internet primeiro (rota com limite de cerca de 6,5 s); se falhar e não houver cache, usa `OfflineRouter` (resposta traz `"source":"offline"`). O rumo (`bearing`) é ignorado na rota local.
- Código: `OfflineRouter.java` e o ramo `route` em `MapNetworkGateway.java`; log com a tag `HarumiRoute`.

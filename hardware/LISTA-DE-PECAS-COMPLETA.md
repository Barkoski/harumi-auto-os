# Lista de peças completa da Harumi (revisão de 20/11/2026)

Junta numa lista só: `LISTA-DE-COMPRAS.md` (Amazon), `LISTA-DE-COMPRAS-ECONOMICA.md` (AliExpress),
`sensores-360/LEIA-ME.md`, `COMPATIBILIDADE-2026-11-20.md` e a separação em duas caixas (`caixa-harumi/LEIA-ME.md`).
Cada peça diz **onde fica no carro** e **em que liga**, para nada ficar sem conector ou sem cabo.

**Status:** JÁ = comprado · COMPRAR = está nas listas de compras · **NOVO** = faltava nas listas · LOJA = autopeças/elétrica
local · IMPRIMIR = peça 3D em ASA · OPC = opcional.
**Preço:** o das listas (Amazon / AliExpress, 20/11/2026). "—" = ainda não pesquisado.
**Medida:** L × P × A em mm. Com fonte quando achei; *est.* = estimada (conferir com a peça).

## 1. Tela (em cima do painel) e central (caixa embaixo do painel do passageiro)

Plano de 20/11/2026, depois das fotos do carro: o vão do rádio é **1-DIN** e o Pioneer fica. A tela vai num suporte no
tampo do painel; a central e o que era a caixinha de serviço viram **uma caixa só**, embaixo do painel do passageiro
(fora do porta-luvas fechado, por causa do calor).

| # | Peça | Qtd | Medida | Liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 1.1 | Orange Pi 5 8 GB + NVMe 256 GB | 1 | 100 × 62 (placa) | — | JÁ | — |
| 1.2 | **Tela 13,3" Full HD 1920×1080 touch capacitivo** (escolhida em 20/11/2026; para filme com o carro parado) | 1 | ~306 × 184 × 8 *est.*; moldura 323 × 201 | HDMI (cabo 90°) e USB do Orange Pi | COMPRAR [VERIFICAR no anúncio: HDMI, touch por USB, alimentação 5 V/12 V, brilho] | R$ 1.529,41 · amazon.com.br/dp/B0GCHZ8DC8 (3,7 · 14) |
| 1.2b | Tela 7" 1024×600 (já comprada): fica para a bancada e os testes | 1 | 164,9 × 100 × 7,7 | — | JÁ | R$ 178,46 |
| 1.3 | Case de alumínio do Orange Pi 5 com fan (do **Orange Pi 5**, com espaço para o NVMe) | 1 | ~104 × 66 × 24 *est.* | fan no 5 V | COMPRAR | Ali R$ 41,19 |
| 1.4 | **2 ventoinhas Noctua NF-A8 5V PWM 80 mm** na tampa da central (entrada e saída; a ideia do empurra e puxa) | 2 | 80 × 80 × 25 | 5 V (USB do hub ou conversor) | COMPRAR (troca a Noctua de 40 mm) | 2 × R$ 152,93 · amazon.com.br/dp/B07DXMF32M (4,8 · 541) · opção barata: par de 80 mm USB 5 V por R$ 42,75 (amazon.com.br/dp/B0H8N7V52R, sem avaliações) |
| 1.4b | **Mangueira sanfonada de 50 mm** (~1 m) + 2 abraçadeiras, do bocal até a saída de ar do passageiro | 1 | — | bocal ↔ saída de ar | **NOVO** / LOJA (autopeças, "duto de 2 polegadas") [VERIFICAR o encaixe na saída de ar] | — |
| 1.5 | Conversor 12→5 V 10 A IP67 (dentro da caixa da central) | 1 | 66 × 60 × 22 (Zaitronics) | fusível → 12 V do relé ACC | COMPRAR | Ali R$ 32,30 |
| 1.6 | **Cabo USB-C macho com ponta em fio, 5 A, curto** | 1 | — | conversor → Orange Pi | **NOVO** | R$ 49,47 · amazon.com.br/dp/B0HNC9CSP8 (USB-C **90°** com 2 fios; sem avaliações) |
| 1.7 | **Cabo HDMI 2 m com plugue em 90°** (central → tela no painel) | 1 | — | Orange Pi → tela | **NOVO** | R$ 17,90 · amazon.com.br/dp/B075QN42TR (4,8 · 10,4 mil) |
| 1.8 | **Extensão USB de 3 m** para o touch da tela (o cabo da tela é curto) | 1 | — | hub → tela | **NOVO** [VERIFICAR o conector da tela] | R$ 13,90 · amazon.com.br/dp/B076BQ3S1G (4,7 · 971) |
| 1.9 | **Medidor INA226** (fica perto do Orange Pi: I2C é curto) | 1 | ~25 × 17 *est.* | I2C do Orange Pi; fio de 12 V | COMPRAR | Ali R$ 9,54 |
| 1.10 | Moldura de 13,3" (frente e traseira, cada uma em 2 partes) e suporte no tampo do painel | 1 jogo | moldura 323 × 201; suporte 180 × 100 × 50; todas as peças cabem em mesa de 220 × 220 | — | IMPRIMIR (`caixa-harumi/` 1b, 1c, 1d) | — |
| 1.12 | **Parafuso M6 × 60 + porca autotravante + 2 arruelas** (eixo da articulação) e 4 parafusos 4,2 mm para o suporte | 1 jogo | — | suporte ↔ moldura | **NOVO** / LOJA | — |
| 1.11 | Espaçadores de nylon M2.5 | 1 kit | — | — | COMPRAR | Ali R$ 26,29 |

## 2. Caixa da central (embaixo do painel do passageiro)

| # | Peça | Qtd | Medida | Liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 2.1 | Hub USB 3.0 7 portas | 1 | 145 × 58 × 26 (ORICO) | Orange Pi pelo cabo 2.2 | COMPRAR | Ali R$ 166,40 |
| 2.2 | ~~Cabo USB entre as caixas~~ | — | — | — | não precisa mais: hub e Orange Pi estão na mesma caixa (usa o cabo do hub) | — |
| 2.3 | **Alimentação do hub em 12 V estabilizado** (conversor buck-boost 12 V ou hub de 5 V) | 1 | *est.* 60 × 40 × 20 | fusível → ACC | **NOVO** (ver P3 da compatibilidade) | Ali R$ 46,51 (segundo SK35L ajustado em 12 V) · alternativa à prova d'água: R$ 132,32 · amazon.com.br/dp/B081RG8XP5 |
| 2.4 | Modem 4G Huawei E3372h (bandas **B3 e B28**) | 1 | 88 × 28 × 11,5 (Huawei) | hub | COMPRAR | Ali R$ 182,13 |
| 2.5 | **Chip de dados 4G** (operadora com B28 na sua região) | 1 | — | modem | **NOVO** | plano mensal |
| 2.6 | **Extensor USB curto (20 cm)** para o modem ficar deitado | 1 | — | hub → modem | **NOVO** | R$ 12,99 · amazon.com.br/dp/B0HFYKL1RB |
| 2.7 | OPC: antenas externas do modem (conector TS9) | 2 | — | modem | **NOVO** OPC | — |
| 2.8 | Bluetooth USB TP-Link UB500 (Linux; recebe o TPMS) | 1 | ~15 × 19 × 7 *est.* | hub | COMPRAR | R$ 55,00 |
| 2.9 | Adaptador USB-serial FT232RL (scanner SSM1) | 1 | ~36 × 18 *est.* | hub; cabo 7.2 | COMPRAR | Ali R$ 9,84 |
| 2.10 | Placa de captura USB (RCA → USB, UVC) | 1 | ~60 × 25 × 12 *est.* | hub; vídeo do kit 360 | COMPRAR | Ali R$ 98,79 |
| 2.11 | Optoacoplador PC817 4 canais (variação **entrada 12 V**) | 1 | ~40 × 30 × 15 *est.* | ACC, ré, luz do painel → GPIO do Orange Pi | COMPRAR | Ali R$ 6,26 |
| 2.12 | **Cabo de 6 vias (GPIO)** do PC817 ao Orange Pi + conector Dupont/JST | 1 | ~1 m | PC817 → pinos do Orange Pi | **NOVO** | R$ 14,17 · amazon.com.br/dp/B0BY5KLWS4 (jumpers fêmea-fêmea) |
| 2.13 | Relé temporizador ACC | 1 | ~50 × 26 × 18 *est.* | ACC + 12 V permanente | COMPRAR | Ali R$ 20,51 |
| 2.14 | Caixa da central + tampa com 2 ventoinhas de 80 mm + bocal do ar-condicionado | 1 | 205 × 195 × 73 (233 com as orelhas); bocal 80 × 80 × 66 | — | IMPRIMIR (`caixa-harumi/` 6, 7, 8) | — |

## 3. GPS, voz e câmera da frente

| # | Peça | Qtd | Medida | Onde fica / liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 3.1 | GPS USB VK-162 (cabo de ~2 m) | 1 | 49 × 38 × 16 (Electropeak) | topo do painel, perto do para-brisa; hub | COMPRAR | Ali R$ 24,33 (M8030: R$ 136,13) |
| 3.2 | **Chapinha de metal + fita VHB** (base do GPS magnético) | 1 | — | painel | LOJA | — |
| 3.3 | **Extensão USB de 1 m**, se o cabo do GPS não alcançar o hub | 1 | — | GPS → hub | **NOVO** (medir antes) | R$ 16,42 · amazon.com.br/dp/B07XQHPWRL (4,8 · 1,1 mil) |
| 3.4 | Microfone USB de lapela (cabo 2 m) | 1 | clipe ~20 × 10 *est.* | coluna A ou teto, perto do motorista; hub | COMPRAR | R$ 21,33 |
| 3.5 | OPC: câmera USB 1080p 130° (dashcam da frente) | 1 | ~40 × 40 × 30 *est.* | atrás do retrovisor; hub | COMPRAR OPC | Ali R$ 53,85 |
| 3.6 | OPC: MPU6050 (impacto, modo vigia) | 1 | 21 × 16 (GY-521) *est.* | I2C do Orange Pi, dentro da 2-DIN | COMPRAR OPC | Ali R$ 11,40 |

## 4. Som (o rádio é um **Pioneer 1-DIN**: se tiver AUX, o amplificador sai)

| # | Peça | Qtd | Medida | Onde fica / liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 4.0 | **Cabo P2 × P2 2 m** (isolador → AUX do Pioneer) | 1 | — | atrás do console | **NOVO** (se o Pioneer tiver AUX) | R$ 20,61 · amazon.com.br/dp/B07VPDW9JR (4,6 · 1,6 mil) |
| 4.1 | Isolador de ruído P2 | 1 | — | saída P2 do Orange Pi | COMPRAR | Ali R$ 21,47 |
| 4.2 | Cabo P2 macho → 2 RCA | 1 | — | isolador → amplificador | **SÓ SEM AUX** | R$ 9,63 · amazon.com.br/dp/B07B3PH6GS (1,8 m; 4,5 · 544) |
| 4.3 | Amplificador 12 V 4 canais com fio remoto | 1 | [VERIFICAR medida do TS 400x4] | embaixo do banco do passageiro; alto-falantes originais | **SÓ SEM AUX** | **Taramps TS 400x4**: R$ 148,10 · amazon.com.br/dp/B00FGV0V0W (4,8 · 1,6 mil) |
| 4.4 | Cabo RCA de 5 m (até o banco) | 1 | — | central → amplificador | **SÓ SEM AUX**, se o 4.2 não alcançar | R$ 26,99 · amazon.com.br/dp/B0GD8R5J63 |
| 4.5 | Cabo 4 mm² + fusível de 30 A junto da bateria (conforme o manual do amplificador) | ~4 m | — | bateria → amplificador | **NOVO** / LOJA | — |
| 4.6 | Fio do remoto (0,5 mm²) | ~3 m | — | relé ACC → amplificador | **NOVO** / LOJA | — |
| 4.7 | Fio paralelo 1,5 mm² para alto-falantes (se o chicote original não servir) | ~4 m | — | amplificador → alto-falantes | LOJA | — |

## 5. Dados do carro

| # | Peça | Qtd | Medida | Onde fica / liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 5.1 | FT232RL (item 2.9) | — | — | — | — | — |
| 5.2 | **Conector do SSM1 (Select Monitor) do Impreza 93** + fios | 1 | — | conector de diagnóstico sob o painel → FT232RL | **NOVO** [VERIFICAR: fotografar o conector e a etiqueta da ECU antes] | — |
| 5.3 | TPMS Bluetooth, 4 sensores externos | 1 jogo | — | válvulas dos pneus; Bluetooth 2.8 | COMPRAR [mandar o modelo antes] | R$ 165,28 |
| 5.4 | Fios de sinal para o PC817: ACC, luz de ré, luz do painel | ~5 m | — | chicote → PC817 | LOJA | — |

## 6. Energia e chicote

| # | Peça | Qtd | Onde fica | Status | Preço |
|---|---|---|---|---|---|
| 6.1 | Porta-fusível em linha à prova d'água | 3 (central, hub, nós) | perto da caixa de fusíveis / bateria | COMPRAR (lista tem 1) | R$ 68,71 cada |
| 6.2 | Kit de fusíveis lâmina 2–30 A | 1 | — | COMPRAR | R$ 9,97 |
| 6.3 | **Derivador de fusível ("add-a-fuse")** para tirar ACC e 12 V permanente sem cortar fio | 2 | caixa de fusíveis | **NOVO** / LOJA | R$ 88,72 (2 un.) · amazon.com.br/dp/B07C585XDC [VERIFICAR: fusível lâmina padrão ou mini no Impreza] |
| 6.4 | Cabo paralelo 1,5 mm² (~5 m) e 4 mm² (~4 m), terminais, conectores tipo Wago | — | — | LOJA | — |
| 6.5 | Diodos TVS 12 V + filtro LC | 3 (2 nós + central) | entrada de cada conversor | LOJA | — |
| 6.6 | Fita de tecido, abraçadeiras, passa-fios de borracha, termorretrátil | — | — | LOJA | — |

## 7. Modo vigia (bateria extra)

| # | Peça | Qtd | Medida | Onde fica / liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 7.1 | Bateria LiFePO4 12 V 6–7 Ah (provisória: selada 12 V 7 Ah) | 1 | selada: 151 × 65 × 94 (RS / Exalium) | porta-malas, presa com cinta | COMPRAR | R$ 97,70 (selada) |
| 7.2 | **Suporte/cinta de fixação da bateria** + caixa ventilada | 1 | — | porta-malas | **NOVO** / LOJA | — |
| 7.3 | Carregador: buck-boost CC/CV SK35L (14,4 V no lítio; 13,8 V na selada) | 1 | ~70 × 40 × 25 *est.* | junto da bateria | COMPRAR | Ali R$ 46,51 |
| 7.4 | Protetor de tensão baixa XH-M609 | 1 | ~70 × 40 × 25 *est.* | saída da bateria → central no modo vigia | COMPRAR | Ali R$ 11,90 |
| 7.5 | Relé automotivo 12 V 40 A com soquete (carrega só com o motor ligado) | 1 | 28 × 28 × 25 *est.* | entre a bateria do carro e o carregador | LOJA | R$ 44,97 · amazon.com.br/dp/B08Q2CRRDM (relé reversor 40 A com soquete e fusível) |
| 7.6 | **Fusível junto da bateria extra** (porta-fusível 6.1) | 1 | — | positivo da bateria extra | **NOVO** | — |
| 7.7 | **Diodo ou relé de comutação** (central puxa do carro ou da bateria extra, sem ligar as duas) | 1 | — | entrada da central | **NOVO** [VERIFICAR o esquema antes] | R$ 44,97 · o mesmo relé reversor do 7.5 (NF = carro, NA = bateria extra) |
| 7.8 | Cabo 4 mm² do porta-malas até o painel | ~5 m | — | sob o carpete | LOJA | — |

## 8. Visão 360 e sensores de distância

| # | Peça | Qtd | Medida | Onde fica / liga em | Status | Preço |
|---|---|---|---|---|---|---|
| 8.1 | Kit 360 com DVR (**com saída AV**) e 4 câmeras | 1 | DVR ~120 × 90 × 25 *est.* | DVR sob o banco; câmeras na grade, retrovisores e tampa traseira | COMPRAR | R$ 1.314,70 |
| 8.2 | **Conectores e extensões das câmeras** (vêm no kit? conferir; senão, extensões de 4 pinos do mesmo padrão) | 4 | — | câmera → DVR | **NOVO** [VERIFICAR no kit] | normalmente vêm no kit [VERIFICAR no anúncio] |
| 8.3 | **Cabo RCA de vídeo** do DVR à placa de captura (2.10) | 1 | ~2 m | sob o banco → porta-luvas | **NOVO** | R$ 26,99 · amazon.com.br/dp/B0GD8R5J63 (RCA 5 m; usa 1 via) |
| 8.4 | Alimentação e fio de ré do DVR (12 V + sinal de ré) | — | — | ACC e luz de ré | LOJA | — |
| 8.5 | Ultrassom JSN-SR04T (mesmo modelo nos 12, **módulo + sonda**) | 12 | placa 41 × 28,5 × 12; furo ~23 | para-choques e laterais | COMPRAR | Ali 12 × R$ 10,21 |
| 8.6 | Radar HLK-LD2451 | 4 | 70 × 35 (Hi-Link) | cantos dos para-choques, por dentro | COMPRAR | Ali 4 × R$ 43,79 |
| 8.7 | Lidar TFmini Plus | 1 | ~35 × 18,5 × 21 *est.* | atrás da grade | COMPRAR | Ali R$ 312,98 |
| 8.8 | ESP32-S3 N16R8 DevKitC-1 | 2 | ~63 × 25 *est.* | um em cada nó | COMPRAR | Ali 2 × R$ 36,13 |
| 8.9 | Conversor Mini560 PRO 5 V | 2 | ~20 × 17 *est.* | um em cada nó | COMPRAR | Ali 2 × R$ 11,15 |
| 8.10 | **Cabo USB do nó dianteiro até o hub** (comprido, ~2 m, passando pela parede corta-fogo) | 1 | — | ESP32 dianteiro → hub | **NOVO** | R$ 67,68 · amazon.com.br/dp/B009GUMVXE (extensão USB 3 m; 4,6 · 5,9 mil) |
| 8.11 | Caixa + tampa do nó, anéis, suportes | — | caixa 110 × 75 × 40 | — | IMPRIMIR (`sensores-360/`) | — |
| 8.12 | Placas perfuradas 5×7 cm, prensa-cabos PG7, conectores à prova d'água de 4 vias, resistores, cabo manga 4 vias | — | — | — | COMPRAR / LOJA | ver listas |

## 9. Ferramentas e montagem

Multímetro · ferro de solda e estanho · broca escalonada (furos dos ultrassons) · parafusos M3 × 10 auto-atarraxantes,
M3 × 16 com porca, M4 com porca · impressão 3D em ASA (serviço local).

## O que entrou nesta revisão

Os itens **NOVO** são, em geral, cabos e conectores que ligam uma peça na outra e não estavam em nenhuma lista. Os
principais:
- cabos de 90° e o USB-C de força da central;
- cabo USB entre as duas caixas;
- alimentação estável do hub;
- chip 4G e extensor do modem;
- cabo GPIO do PC817;
- toda a parte de som;
- conector do SSM1;
- fixação, fusível e comutação da bateria extra;
- conectores das câmeras e o cabo de vídeo do 360;
- cabo USB do nó dianteiro;
- derivadores de fusível.

**Ainda sem preço** (pesquisar antes de fechar o orçamento): os itens NOVO e o amplificador.


## Orçamento (20/11/2026, plano da tela no painel)

| Parte | Lista econômica | Lista Amazon |
|---|---|---|
| Itens das listas de compras (fases 1 a 6, sem opcionais) | ≈ R$ 3.800 (R$ 3.431,98 + ~R$ 368 de impostos do AliExpress) | R$ 5.676,99 |
| Tela 13,3" Full HD (1.2) | R$ 1.529,41 | R$ 1.529,41 |
| 2 Noctua NF-A8 no lugar da Noctua de 40 mm (1.4) | + R$ 196,38 | + R$ 196,38 |
| Itens NOVO com preço, **Pioneer com AUX** (1.6, 1.7, 1.8, 2.3, 2.6, 2.12, 3.3, 4.0, 6.1 ×2, 6.3, 7.5, 7.7, 8.3, 8.10) | R$ 602,72 | R$ 688,53 (hub com o estabilizador à prova d'água) |
| **Total online, Pioneer com AUX** | **≈ R$ 6.128** | **≈ R$ 8.091** |
| Se o Pioneer **não** tiver AUX (troca o 4.0 pelo amplificador 4.3 e o cabo 4.2) | ≈ R$ 6.265 | ≈ R$ 8.228 |
| Com o par de ventoinhas baratas em vez das Noctua | − R$ 263,11 | − R$ 263,11 |

Preços da busca da própria Amazon Brasil em 20/11/2026 (páginas de produto não abriram para conferir variação, frete e
vendedor). As duas cópias extras do porta-fusível (6.1) estão a R$ 68,71 cada; em autopeças costuma sair bem mais barato.

**Fora do total:**
- itens de loja local: parafuso M6 da articulação, fios, terminais, Wago, TVS, fita, abraçadeiras e, sem AUX, o cabo de 4 mm² e o fusível de 30 A do amplificador;
- chip 4G (plano mensal);
- conector do SSM1;
- fixação da bateria extra;
- impressão 3D;
- opcionais.

# Base de conhecimento — Subaru Impreza SW 1993, EJ18 1.8, automático (Brasil)

> Para uso da Harumi (copiloto local). Pesquisa web feita em 03/11/2026, só com leitura de páginas (nada foi instalado).
> Legenda de confiança: **[2+]** = confirmado em 2 ou mais fontes independentes · **[1]** = só 1 fonte · **[inf]** = inferência minha a partir das fontes (não está escrito em nenhuma delas) · **[nf]** = não encontrado.
> Regra para a Harumi: quando um item for [1] ou [inf], dizer ao motorista que é "provável" e pedir confirmação. Nunca apresentar como certo.
> Muitas fontes boas (ausubaru, scoobynet, legacycentral, nasioc, openlaborproject, bolidenforum, 2carpros, manualslib) recusaram o acesso automático (erro 403/conexão). Por isso alguns itens ficaram com 1 fonte.

---

## 1. Identificação

### 1.1 Chassi / código do modelo
| Item | Valor | Confiança | Fonte |
|---|---|---|---|
| Geração | 1ª geração do Impreza (1992/93–2000). Sedã = GC, perua (wagon/SW) = **GF**, cupê = GM | [2+] | https://legacypic.uk/car/specs.php?id=6507 ; https://legacypic.uk/car/specs.php?id=1120 ; pesquisa legacypic/rolling.hu (catálogo "Impreza Estate (GF)") https://shop.rolling.hu/catalog/SCHAEFFLER/subaru-impreza-estate-gf-18-i-awd-gf6 |
| Perua 1.8 **FWD** automática | Código **GF5** (ex.: GF5AU5R, mercado Austrália/Tailândia, E-4AT, FWD, produção 12/1992–09/1993) | [1] | https://legacypic.uk/car/specs.php?id=6507 |
| Perua 1.8 **AWD** automática | Código **GF6** (ex.: GF6A5AR, JDM "HX Edition-S", motor EJ18E, E-4AT tipo TZ102ZW3AA, tração integral ACT-4 com embreagem multidisco, produção 10/1992–08/1993) | [1] (GF6 = 1.8 AWD também aparece no catálogo rolling.hu "1.8 i AWD (GF6)") → [2+] para "GF6 = perua 1.8 AWD" | https://legacypic.uk/car/specs.php?id=1120 ; https://shop.rolling.hu/catalog/SCHAEFFLER/subaru-impreza-estate-gf-18-i-awd-gf6 |
| Havia FWD e AWD? | Sim, existiam as duas no mundo (GF5 FWD / GF6 AWD) | [2+] (legacypic GF5 FWD + GF6 AWD) | links acima |
| **Brasil** | A tabela FIPE de 1993 lista só três Impreza: "GL 1.6/1.8 16V", "GL 4x4 1.8 16V" e "**SW GL 1.6/1.8/2.0 4x4 16V**". Ou seja, a perua 1993 no Brasil aparece apenas como **4x4** | [1] | https://carzin.com.br/tabela-fipe/carros/subaru/impreza/1993/ ; https://carzin.com.br/tabela-fipe/carros/subaru/impreza/1993/sw-gl-16-18-20-4x4-16v.html (código FIPE 027016-4) |
| Conclusão para o carro do usuário | Muito provavelmente **GF6 (perua 1.8 AWD, 4EAT)**. Confirmar pelo chassi (VIN começa com JF1GF…; ver letras/números seguintes) e pela plaqueta | [inf] | — |
| Carro importado (origem) | FIPE/fichacompleta indicam "importado"; não achei importador nem histórico de vendas no Brasil | [1] / [nf] | https://www.fichacompleta.com.br/en/carros/subaru/impreza-gl-1-8-1993 |

**Onde fica a plaqueta/etiqueta e o código da ECU:** [nf] para a 1993 especificamente. O código interno da ECU (ROM ID) pode ser lido pelo próprio protocolo SSM1 (comando "Get ROM ID", seção 2). A etiqueta física da ECU só olhando o módulo (seção 8).

### 1.2 Motor EJ18
| Item | Valor | Confiança | Fonte |
|---|---|---|---|
| Código | EJ18 (JDM: EJ18E; algumas listagens: EJ18S) | [2+] | fichacompleta (acima); legacypic id=1120; https://www.amsoil.com/lookup/auto-and-light-truck/1994/subaru/impreza/1-8l-4-cyl-engine-code-2-ej18s-x/ |
| Arquitetura | Boxer 4 cil., 1.820 cm³, diâm. 87,9 × curso 75 mm, taxa 9,5:1, aspirado | [2+] (cilindrada e taxa em fichacompleta e legacypic) | fichacompleta; legacypic id=1120 |
| Comando | **SOHC**, 16 válvulas, correia dentada | [2+] | fichacompleta; legacypic id=1120 |
| Potência / torque | Varia por mercado: BR (fichacompleta) 105 cv a 5.600 rpm / 15 kgfm a 4.400 rpm; Europa (cars-data) ~103 cv / 147 N·m; JDM 115 PS a 6.000 / 154 N·m a 4.500 | [2+] para faixa ~103–115 cv | fichacompleta; https://cars-data.com/en/subaru/impreza/1993-sedan/1-8-gl-awd-9337--9337 ; legacypic id=1120 |
| Injeção | Multiponto (MPFI), ECU JECS com sensor de fluxo de ar (MAF) | [2+] (multiponto: fichacompleta; MAF na pinagem rusEFI e no mapa SSM1 que tem "AirflowSensor" e nenhum MAP para o 1993 NA) | fichacompleta; https://wiki.rusefi.com/Subaru-Impreza-1991-1996 ; SelectMonitor.ini (seção 3) |
| Ordem de ignição | **1-3-2-4** | [2+] | https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/powertrain_management/ignition_system/firing_order/component_information/specifications/ ; https://automotivetechinfo.com/2005/08/pre-obd-ii-diagnostics-ignition-the-way-they-were/ |
| Ignição | Bobina única Hitachi CM12-100 (primário 0,63–0,77 Ω; secundário 10,4–15,6 kΩ) → sistema com distribuidor acionado pelo comando | [1] bobina; [1]+[inf] distribuidor | https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/powertrain_management/ignition_system/ignition_coil/component_information/specifications/ ; distribuidor citado em https://www.au7o.io/known-issues/subaru-impreza?year=1993 (site agregador, baixa confiabilidade) |
| Motor interferente? | **Não interferente** (SOHC EJ até 1996): se a correia romper, em tese não empena válvula, mas o carro para e precisa ressincronizar | [2+] | https://wikipedia2006.classicistranieri.com/en/s/u/b/Subaru_EJ_engine_d232.html ; https://aa.co.nz/cars/ask-an-expert/faults-reliability-service-and-repair/show/5012 |

### 1.3 Câmbio e tração
| Item | Valor | Confiança | Fonte |
|---|---|---|---|
| Câmbio | 4 marchas automático com controle eletrônico ("E-4AT" / 4EAT), TCU própria com memória de falhas e modo de emergência | [2+] | legacypic id=1120 e id=6507; https://automotivetechinfo.com/1998/01/subaru-4eat-transmissions |
| Geração do 4EAT | Família 4EAT "Phase 1" (produzida ~1987.5–1998). Impreza 1993–94 tem botão MANUAL, como o Legacy 1990–94 | [1] | https://automotivetechinfo.com/1998/01/subaru-4eat-transmissions ; https://automotivetechinfo.com/2004/02/subaru-4eat-phase-1-transmission-diagnosis-and-service |
| Tração AWD do automático | Embreagem de transferência multidisco (MPT) no prolongamento do câmbio, controlada pelo **solenoide Duty C**; mais duty = menos tração traseira. Existe soquete de fusível "FWD" no cofre para forçar tração dianteira (uso de diagnóstico/elevador/dinamômetro) | [2+] (MPT/Duty C em 2 artigos EndWrench + agregadores) | https://automotivetechinfo.com/1998/01/subaru-4eat-transmissions ; https://automotivetechinfo.com/2004/02/subaru-4eat-phase-1-transmission-diagnosis-and-service |

---

## 2. Diagnóstico eletrônico

### 2.1 Protocolo
| Item | Valor | Confiança | Fonte |
|---|---|---|---|
| Protocolo | **SSM1 / Subaru Select Monitor (1ª geração)**: serial TTL 5 V, **1953 baud, 8 bits, paridade par (E), 1 stop** (8E1), sem controle de fluxo | [2+] | http://www.alcyone.org.uk/ssm/protocol.html ; https://wiki.rusefi.com/Subaru-Impreza-1991-1996 ; https://hackaday.com/tag/ssm1/ ; https://habr.com/en/articles/149182 |
| ECU | Fabricante JECS, CPU Mitsubishi M37791 (família 7700); valores de 16 bits little-endian (descrito para o SVX; o site diz que vale em boa parte para ECUs JECS Subaru 1992–96) | [1]+[inf] | http://www.alcyone.org.uk/ssm/ecuinfo.html ; http://www.alcyone.org.uk/ssm/ |
| Transição OBD-II | Subaru começa OBD-II em 1995 (Legacy/2.2) e completa em 1996 (regra dos EUA). Um 1993 é **pré-OBD-II**, SSM1 | [2+] | https://automotivetechinfo.com/2002/06/obd-ii-service-on-subaru-vehicles ; https://ahgautoservice.com/when-did-subaru-start-using-obd2 |
| ELM327 funciona? | **Não.** ELM320–327 usam conjunto fixo de comandos AT, incompatível com o protocolo Subaru; SSM1 nem é OBD-II | [2+] | https://www.scoobynet.com/general-technical-10/670577-my93-95-laptop-diagnostics.html (via resumo de busca; página bloqueou leitura direta) ; https://hackaday.com/tag/ssm1/ |

### 2.2 Conectores de diagnóstico
| Item | Valor | Confiança | Fonte |
|---|---|---|---|
| Conector do Select Monitor | **Amarelo, 9 pinos**. Pino 2 = TX (saída da ECU), 3 = RX, 5 = +12 V, 9 = terra. Mesmo plugue físico do rádio Subaru antigo (Scosche SU02B / Metra 70-1780 / Autoleads PC2-29-4 servem de contraparte) | [2+] (pinos 2/3/9 em pinouts.ru e microtopia; pino 5 = 12 V em alcyone e microtopia) | http://www.alcyone.org.uk/ssm/ports.html ; https://pinouts.ru/CarElectronics/subaru_old_9pin.shtml ; https://sites.google.com/a/microtopia.org/microtopia/personal/subaru-ej22e-diagnostics |
| Localização no Impreza 1993 | [nf] confiável. Fontes divergem: uma diz atrás do lado direito do painel no Impreza, outra (ALLDATA citado em fórum) diz lado esquerdo sob o painel; no SVX é no painel lateral do motorista | [1] cada, conflitantes | resumo de busca de https://thesubaruforums.com/threads/missing-a-key-concept-on-reading-subaru-trouble-codes.6318 (403) ; http://www.alcyone.org.uk/ssm/ports.html |
| Conectores de modo | Dois pares de plugues soltos no chicote: **Test Mode = verdes**; **Read Memory = pretos**. Na ECU: read memory = pino 12 do conector B96 aterrado; test = pino 13 do B96 aterrado (pinagem EDM turbo EJ20G — pode diferir no EJ18) | Cores: [1] (verde = teste também na EndWrench → verde [2+]); pinos: [1] | https://automotivetechinfo.com/2005/08/pre-obd-ii-diagnostics-ignition-the-way-they-were/ ; https://wiki.rusefi.com/Subaru-Impreza-1991-1996 |
| Nos fios da ECU (EJ20G) | SSM: B96 pino 7 (Tx) e 8 (Rx) | [1] | https://wiki.rusefi.com/Subaru-Impreza-1991-1996 |

### 2.3 Ler códigos sem scanner (piscadas)
Modos (EndWrench): **U-check** (luz Check Engine do painel acende para falhas que afetam partida/rodagem), **D-check / Test mode**, **Read Memory**, **Clear Memory**. [1] — https://automotivetechinfo.com/2005/08/pre-obd-ii-diagnostics-ignition-the-way-they-were/

- **Read Memory (códigos gravados):** ignição ON, motor desligado, **conectar Read Memory (pretos)**, Test Mode desconectado; ler as piscadas na luz Check Engine / LED da ECU. [1, via resumo de busca de trecho de manual; não li a página original]
- **D-check (teste dinâmico):** motor aquecido, desliga, **conectar os verdes**, liga ignição e observa a luz; depois motor funcionando. [2+ para "verdes = D-check"] — EndWrench acima.
- **Apagar memória:** ambos os pares conectados, ignição ON e motor funcionando (segundo trecho de manual em resumo de busca). [1, não verificado diretamente] — **atenção: apagar códigos é ação de escrita/intervenção; a Harumi não deve fazer, só orientar.**
- **Leitura das piscadas:** piscada longa (~1,2 s) = dezena; curta (~0,2 s) = unidade; pausa ~1,8 s e repete. Ex.: código 23 = 2 longas + 3 curtas. [2+] — EndWrench acima; https://groups.google.com/g/alt.autos.subaru/c/Wnk03E7K0sw
- LED na ECU: em modelos antigos, o "O2 monitor lamp" na própria ECU pisca com sonda funcionando quando o motor está quente. [1] — EndWrench.

### 2.4 Códigos de falha do motor (ECU JECS, 2 dígitos)
A lista abaixo vem principalmente do mapa de bits do SVX (JECS, mesma família) e foi cruzada com relatos de Impreza 1993. O EJ18 (4 cil., 1 sonda, aspirado, sem EGR na maioria dos mercados) **não usa** os códigos de 5º/6º injetor, 2ª sonda, 2º sensor de detonação etc.

| Código | Significado | Confiança | Fonte |
|---|---|---|---|
| 11 | Sensor de ângulo do virabrequim (crank) | [2+] | alcyone ecuerror ; resumo de busca (Impreza 1.8 1995) |
| 12 | Sinal do motor de partida (starter switch) | [2+] | alcyone ecuerror ; relato Impreza 1993 em resumo de busca |
| 13 | Sensor de comando (cam) | [2+] | alcyone ; EndWrench (11/13 podem surgir falsamente após o motor morrer/girar ao contrário) |
| 14 / 15 / 16 / 17 | Injetor 1 / 2 / 3 / 4 | [1] | http://www.alcyone.org.uk/ssm/ecuerror.html |
| 21 | Sensor de temperatura do líquido de arrefecimento | [2+] | alcyone ; https://www.iatn.net/techhelp/29/6196/item (Impreza 1993 1.8) |
| 22 | Sensor de detonação (knock) | [2+] | alcyone ; EndWrench |
| 23 | Medidor de massa de ar (MAF) | [2+] | alcyone ; EndWrench (exemplo "23") ; resumo Impreza 1.8 1995 |
| 24 | Válvula de ar de marcha lenta (bypass / ISC / "idle-up") | [2+] | alcyone ("Bypass") ; IATN Impreza 1993 ("idle-up solenoid") |
| 31 | Sensor de posição da borboleta (TPS) | [2+] | alcyone ; resumo de lista ausubaru |
| 32 | Sonda lambda (O2) | [2+] | alcyone ; EndWrench (32 = O2 "afogada" no Legacy) |
| 33 | Sensor de velocidade do veículo (VSS, no velocímetro) | [2+] | alcyone ("VSS2") ; resumo IATN Impreza 1993 |
| 34 | Solenoide de EGR (só versões com EGR, ex. Califórnia/EUA) | [2+] | alcyone ; IATN Impreza 1993 |
| 35 | Solenoide de purga do cânister | [1] | alcyone |
| 41 | Autoaprendizado de mistura (A/F learning) — mistura pobre/rica fora do limite | [2+] | alcyone ; EndWrench (41 por filtro de combustível entupido) |
| 42 | Interruptor de marcha lenta (idle switch, no TPS) | [2+] | EndWrench ; resumo lista ausubaru |
| 45 | Sensor de pressão atmosférica (se equipado) | [1] | alcyone |
| 49 | Resistor de CO (ajuste de CO, mercados sem sonda/alguns EDM) | [1] | alcyone |
| 51 | Interruptor de neutro / inibidor | [1] | alcyone |
| 52 | Interruptor de Park | [1] | alcyone |
| 55 / 56 | Temperatura EGR / sistema EGR | [1] | alcyone |

Mapa de bits via SSM1 (SVX; **endereços provavelmente diferentes no EJ18** — não usar sem validar): atuais em 0x1026–0x1029, memória em 0x12B9–0x12BC. [1] — http://www.alcyone.org.uk/ssm/ecuerror.html

### 2.5 Câmbio automático (TCU 4EAT)
**Códigos (4EAT da época, 2 dígitos)** — [2+] (fórum polonês "Transmission Tips" + mapa de bits da TCU no alcyone coincidem):

| Código | Item |
|---|---|
| 11 | Solenoide Duty A (pressão de linha) |
| 12 | Solenoide Duty B (lock-up do conversor) |
| 13 | Solenoide de troca 3 |
| 14 | Solenoide de troca 2 |
| 15 | Solenoide de troca 1 |
| 21 | Sensor de temperatura do ATF |
| 22 | Sensor de pressão atmosférica |
| 23 | Sinal de rotação do motor |
| 24 | Solenoide Duty C (embreagem de transferência AWD) |
| 25 | Sinal de controle de torque |
| 31 | Sensor da borboleta |
| 32 | Sensor de velocidade 1 |
| 33 | Sensor de velocidade 2 |

Fontes: https://forum-subaru.pl/viewtopic.php?t=5196 ; http://www.alcyone.org.uk/ssm/tcuerror.html

**Como ler (Legacy 1990–94 / carros com luz POWER):** motor aquecido rodando >20 km/h; parar, desligar e ligar ignição e confirmar luz POWER; desligar; alavanca em D com MANUAL ligado; ligar ignição; ir para 3 e desligar MANUAL; 2 e ligar MANUAL; 1 e desligar MANUAL; pisar levemente no acelerador (abre o idle switch) e contar as piscadas da luz POWER. Piscar 4 vezes por segundo contínuo = normal nesse procedimento. Para códigos antigos, sequência inversa. [1] — https://forum-subaru.pl/viewtopic.php?t=5196
- **Impreza 1993:** se o painel não tiver luz POWER, a luz usada é provavelmente a **"AT OIL TEMP"** (a partir do fim dos anos 90 é ela quem pisca códigos). [inf] — confirmar no painel do carro.
- **Luz AT OIL TEMP em modelos posteriores (referência):** acesa com motor em funcionamento = ATF quente; acende na checagem de lâmpadas; piscando ao ligar = TCU tem código gravado. Em 2000+: 2 Hz = normal, 4 Hz = problema de alimentação/terra. [2+ para modelos ≥1999; aplicação ao 1993 = inf] — https://groups.google.com/g/alt.autos.subaru/c/tLS0YFcIc8Q ; resumo do manual Legacy 2000 em pesquisa.
- SSM1 da TCU: comando de leitura diferente do motor (byte **0x45** em vez de 0x78). Códigos atuais nos endereços 0x0001 e 0x0005, anteriores em 0x0003 e 0x0004 (SVX). [1] — http://www.alcyone.org.uk/ssm/protocol.html ; http://www.alcyone.org.uk/ssm/tcuerror.html

### 2.6 Interfaces e softwares
| Ferramenta | Suporta SSM1 de 1993? | Confiança | Fonte |
|---|---|---|---|
| **EvoScan** + cabo "Subaru Select Monitor I (SSMI)" (USB, ponta 9 pinos amarela + ponta 16 pinos para 1996–99; US$ 157, software +US$ 20) | **Sim**, anunciado para 1990–1998 | [2+] (loja + relato de uso em EJ22 1990–95) | https://evoscan.com/product/subaru-select-monitor-i-suits-all-1990-1998-subaru-vehicles/ ; https://sites.google.com/a/microtopia.org/microtopia/personal/subaru-ej22e-diagnostics |
| Cabo caseiro FTDI **TTL-232R-5V** (USB→TTL 5 V) no plugue amarelo | Sim (é o meio físico do SSM1) | [2+] | microtopia (acima) ; http://www.alcyone.org.uk/ssm/ports.html |
| Arduino/Teensy + conversor de nível 3,3→5 V | Sim, já foi feito (Impreza STi 1997 JDM, Forester 1998) | [2+] | https://github.com/P1kachu/ssm1-gc8 ; https://habr.com/en/articles/149182 |
| Select Monitor (Kevin Frank / VWRX), JECScan, Alcyone (Linux), "Select Monitor Software" de N. Mori (2023, foco SVX) | Sim (SSM1), cobertura por ROM ID | [1] | http://www.alcyone.org.uk/ssm/software.html |
| OBDKey (modo SSM) + app Torque (Android) | Citado como capaz de ler SSM em OBD-I Subaru | [1] (não confirmado no texto lido) | microtopia (resumo da página) |
| **FreeSSM** | Foco em 1999+ (SSM2). SSM1 só em beta e, segundo o mantenedor, só para ABS | [2+] | https://github.com/Comer352L/FreeSSM/issues/20 ; https://www.autoinstruct.com.au/?p=11549 |
| **RomRaider** | Logger é SSM2 (4800 bps, ISO9141). Não serve para SSM1 | [2+] | https://mailserver.romraider.com/index.php/RomRaider/SsmProtocol ; resumo de busca (aviso para não misturar) |
| Ecuexplorer, Learning View | [nf] sobre SSM1 | [nf] | — |
| ELM327 | Não funciona | [2+] | seção 2.1 |

---

## 3. Parâmetros ao vivo via SSM1 (o mais crítico)

### 3.1 Comandos (todos são 4 bytes)
| Comando | Bytes | Observação | Confiança | Fonte |
|---|---|---|---|---|
| Ler endereço da ECU (motor) | `78 MSB LSB 00` | A ECU passa a enviar o valor **repetidamente** até receber Stop. O 4º byte é ignorado, mas tem de ser enviado | [2+] | alcyone protocol ; P1kachu ; habr |
| Ler TCU (câmbio) | `45 MSB LSB 00` | | [1] | alcyone protocol |
| Parar | `12 00 00 00` | | [2+] | alcyone ; P1kachu ; habr |
| ROM ID | `00 46 48 49` | Só funciona **com uma leitura já em andamento** (ex.: mandar `78 00 00 00` antes) | [2+] | alcyone ; P1kachu repo ; habr |
| Escrita | `AA MSB LSB dado` | **PROIBIDO na Harumi** (só leitura). Listado aqui apenas para que o software bloqueie esse byte | [1] | alcyone protocol |
| Resposta | 3 bytes: `MSB LSB DADO` (eco do endereço + 1 byte de valor) | | [1] | alcyone protocol |

Exemplos de ROM ID já vistos: Forester 1998 = A30117 (habr); STi 1997 JDM = A3113 (P1kachu). **O ROM ID do carro do usuário define a tabela de endereços correta.**

### 3.2 Endereços — atenção: dependem do ROM ID
Fonte principal: arquivo `SelectMonitor.ini` (software Select Monitor), publicado no repositório https://github.com/P1kachu/ssm1-gc8 (lido em https://raw.githubusercontent.com/P1kachu/ssm1-gc8/master/resources/code/SelectMonitor.ini). Ele tem uma seção **`[7332]` "1993-1994 NA (untested)"** — aspirado 1993–94, provavelmente Legacy/Impreza JECS, **marcada pelo próprio autor como não testada**. O mesmo arquivo usa os mesmos endereços (133x) como padrão `[null]`, e uma página independente (ROM 7432A1, Legacy EJ22 UK 1996) confirma vários deles.

| Parâmetro | Endereço `[7332]` | Confirmação independente | Confiança |
|---|---|---|---|
| Tensão da bateria | 0x1335 | 1335 no EJ22 1996 (microtopia) | [2+] (para a família 133x) |
| Velocidade | 0x1336 | 1336 microtopia | [2+] |
| Temp. do líquido | 0x1337 | 1337 microtopia | [2+] |
| Rotação | 0x1338 | 1338 microtopia | [2+] |
| Avanço de ignição | 0x1323 | microtopia dá 109A (ROM diferente) | [1] |
| Sinal do MAF | 0x1307 | 1307 microtopia | [2+] |
| Carga (load) | 0x1305 | 1305 microtopia | [2+] |
| TPS | 0x1329 | 1329 microtopia | [2+] |
| Largura de pulso do injetor | 0x1306 | 1306 microtopia | [2+] |
| Duty da válvula de marcha lenta (ISC/IAC) | 0x1314 | 1314 microtopia | [2+] |
| Sonda O2 (média) | 0x1310 | 1310 microtopia | [2+] |
| O2 mín./máx. | 0 (não mapeado em [7332]); 133B/133A no EJ22 | — | [1] |
| Correção de detonação | 0x1328 | 1328 microtopia | [2+] |
| Correção A/F | 0x133E | microtopia dá 10A2 | [1] |
| Pressão atmosf., MAP, boost | não mapeado (aspirado) | — | — |

Fonte microtopia: https://sites.google.com/a/microtopia.org/microtopia/personal/subaru-ej22e-diagnostics (endereços atribuídos a "b3lha", ROM 7432A1, com aviso de que variam por ECU).

Outras tabelas existentes, **que NÃO servem para este carro** mas mostram que os endereços mudam: SVX EG33 (102F bateria, 1071 velocidade, 106F rpm, 1185 temperatura…) — http://www.alcyone.org.uk/ssm/ecureverse.html ; ECUs 1997+ (0x0007 bateria, 0x0008 velocidade, 0x0009 rpm, 0x000A temperatura…) — P1kachu.

**Regra para a Harumi:** ao conectar, ler o ROM ID; se não for 73xx/compatível, **não exibir valores** até validar (ex.: rpm de 0x1338 deve bater com o conta-giros; temperatura deve subir ao aquecer; bateria ~12–14 V).

### 3.3 Fórmulas de conversão (valor bruto = 1 byte, 0–255)
| Parâmetro | Fórmula | Confiança | Fonte |
|---|---|---|---|
| Bateria (V) | bruto × 0,08 | [2+] | alcyone ecureverse (SVX) ; código P1kachu (STi 1997) |
| Velocidade (km/h) | bruto × 2 | [2+] | alcyone ; P1kachu |
| Rotação (rpm) | bruto × 25 | [2+] | alcyone ; P1kachu |
| Temp. líquido (°C) | bruto − 50 | [2+] | alcyone ; P1kachu (autor diz "°C assumido") |
| TPS (%) | bruto × 100 / 255 (P1kachu usa /256) | [2+] | alcyone ; P1kachu |
| MAF (%) | bruto × 100 / 255 | [2+] | alcyone ; P1kachu |
| Avanço (°) | bruto (sem conversão) | [1] | alcyone |
| Pulso do injetor (ms) | bruto × 256 / 1000 | [1] | alcyone |
| ISC/IAC duty (%) | bruto × 100 / 255 | [1] | alcyone |
| Sonda O2 (mV) | bruto × 5000 / 512 (média); mín./máx.: × 5000 / 256 | [1] | alcyone |
| Correção A/F | bruto − 128 (próximo de 0 = neutro) | [2+] | alcyone ; microtopia (valores giram em torno de 128) |
| Correção de detonação | bruto (sem fórmula) | [1] | alcyone |
| Carga (load) | bruto (sem unidade) | [1] | alcyone |

**Ressalva:** as fórmulas foram documentadas para o SVX (EG33) e para o STi 1997; aplicar ao EJ18 1993 é [inf] razoável (mesma família JECS/SSM1), mas validar com o carro (ex.: rpm × 25 conferido no conta-giros).

### 3.4 Sinais binários disponíveis em ECUs SSM1 da época (sem endereço confirmado)
Interruptor de ignição, modo AT, test mode, read memory, neutro/park, idle switch, A/C (botão e relé), relé da ventoinha, relé da bomba, purga, detonação detectada. [1] — microtopia. Endereços: [nf].

---

## 4. Faixas normais e alertas
| Item | Normal | Alerta sugerido | Confiança | Fonte |
|---|---|---|---|---|
| Marcha lenta (aquecido, sem carga) | **700 ± 100 rpm** | < 550 ou > 1.000 rpm aquecido, ou oscilando | [1] (manual do próprio 1993 1.8) | https://workshop-manuals.com/subaru/impreza_sedan_awd/f4-1820cc_1.8l_sohc/powertrain_management/fuel_delivery_and_air_induction/idle_speed/system_information/specifications/ |
| Marcha lenta com A/C ligado | **850 ± 100 rpm** | — | [1] | idem |
| Temp. do líquido (motor quente) | ~80–100 °C | > 105 °C: alerta; > 110 °C: parar | [1] (manual Subaru de 2004, outro motor) + [inf] limites | resumo de busca de manuais 2004/2006 (raig0.planet.ee) |
| Bateria com motor ligado | ~12–15 V (carregando ~13,5–14,5) | < 12,5 V com motor ligado (alternador) ou > 15 V (regulador) | [1] (manual de 2004) + [inf] | idem |
| Sonda O2 (aquecido, malha fechada) | Oscila ~0,3–0,7 V (rico 0,7–1,0; pobre 0–0,2) | parada fixa em rico ou pobre | [2+] | microtopia ; rusEFI |
| Correção A/F | perto de 0 em marcha lenta estável | desvio grande e permanente (ver código 41) | [1] | microtopia |
| TPS (tensão) | Fechado ~4,7 V, aberto ~0,9 V (sinal invertido no EJ20G turbo) | — | [1], pode não valer para EJ18 | rusEFI |
| Compressão | 1.079–1.275 kPa (156–185 psi); limite 883 kPa; diferença máx. entre cilindros 196 kPa | — | [1] (manual 1993 1.8) | https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/engine_cooling_and_exhaust/engine/compression_check/system_information/specifications/ |
| Pressão de óleo | Não é lida pela ECU (só luz de pressão no painel). Valor de manual: [nf] | luz acesa com motor ligado = parar | [inf] | — |
| Temperatura do ATF | Só lida pela TCU (não pela ECU). Faixa de referência: ~80 °C em teste (Legacy 2000). Ponto de acendimento da luz AT OIL TEMP do 1993: [nf] (está numa imagem do manual) | Luz AT OIL TEMP acesa com motor ligado = parar e esfriar | [1] / [nf] | resumo do manual Legacy 2000 ; https://workshop-manuals.com/subaru/impreza_sedan_awd/f4-1820cc_1.8l_sohc/instrument_panel_gauges_and_warning_indicators/temperature_warning_indicator_a/t/component_information/specifications/ |
| Tempo de engate (teste do câmbio) | N→D < 1,2 s; N→R < 1,5 s | acima disso: suspeita de pressão baixa/embreagens | [1] | https://automotivetechinfo.com/1998/01/subaru-4eat-transmissions |

**Luz Check Engine:** fixa = verificar logo; piscando com motor andando = falha grave (provável falha de ignição), reduzir e parar. [1] Exceção: com os conectores de teste/memória ligados, a luz pisca de propósito para mostrar códigos (seção 2.3) [inf] — https://www.carcarekiosk.com/video/1994_Subaru_Impreza_L_1.8L_4_Cyl._Sedan/check_engine_light/diagnose

---

## 5. Problemas conhecidos (sintoma → causa provável → o que checar)
| Tema | Sintoma | Causa provável | Checar | Confiança / fonte |
|---|---|---|---|---|
| Junta de cabeçote | Superaquecimento, bolhas no reservatório, perda de água | Problema famoso é do **EJ22/EJ25**, não do EJ18 | Teste de CO₂ no radiador, compressão | [2+] que EJ18 é pouco afetado — https://curbsideclassic.com/cars-of-a-lifetime/coal-1993-subaru-impreza-l-the-allure-of-the-pleiades (resumo; página bloqueou) ; resumos de agregadores |
| Vazamento nas tampas de válvulas | Cheiro de óleo queimado, óleo nas tampas | Junta e anéis dos tubos de vela ressecam | Inspeção visual; trocar kit da junta | [2+] — https://iheartjapanesecars.blogspot.com/2016/03/subaru-engine-oil-leak-causes.html ; https://ricksfreeautorepairadvice.com/common-subaru-oil-leaks-and-how-to-prevent-them/ |
| Retentores dianteiros do comando/virabrequim | Óleo atrás da capa da correia, pingos na frente | Retentores velhos (EJ18/EJ22/EJ25 com correia) | Trocar junto com a correia dentada | [2+] — mesmas fontes |
| Placa separadora de óleo (traseira do bloco) | Pingo entre motor e câmbio | Placa plástica de fábrica que racha; troca por metálica exige tirar motor/câmbio | Localizar vazamento na junção motor/câmbio | [2+] — iheartjapanesecars ; au7o (agregador) |
| Distribuidor | Falha, marcha lenta irregular, óleo na tampa | Tampa/rotor corroídos ou trincados; anel de vedação do distribuidor vaza óleo para dentro | Abrir tampa, olhar rotor/óleo | [1] (agregador) |
| Correia dentada / tensor / polias | Barulho na frente do motor; motor para e não pega | Correia vencida; tensor automático com vazamento; polias com folga | Inspeção a cada 30.000 mi; motor não interferente | [2+] — seção 6 |
| Marcha lenta oscilando | Rotação sobe e desce, assobio | Carbonização da válvula ISC/IAC (bypass); idle switch/TPS; vazamento de vácuo | Duty da ISC (0x1314), código 24/42; limpar ISC antes de trocar | [2+] — https://www.underhoodservice.com/?p=43516 (tech tip Subaru, EJ22) ; https://www.aa1car.com/library/problem_idle_surge.htm |
| Sonda O2 | Consumo alto, código 32 | Sonda velha ou molhada | Ver oscilação da O2 ao vivo | [1] (EndWrench: 32 por sonda alagada) |
| Mistura pobre | Código 41, falta de força | Filtro de combustível entupido, vazamento de ar | Correção A/F | [1] EndWrench |
| Sensor de detonação | Código 22, perda de potência | Fio interno partido no sensor | Correção de detonação, código 22 | [1] EndWrench |
| Câmbio: trancos | Trocas duras ou "escorregando" | Resistores dos solenoides queimados; solenoide de pressão; ATF velho | Códigos TCU 11–15; nível/cor do ATF | [1] — https://www.youcanic.com/subaru-transmission-problems/ |
| Câmbio: "torque bind" | Carro trepida/freia em curvas fechadas e lentas no seco | Embreagem de transferência travada ou solenoide **Duty C** sujo/travado | Teste com fusível no soquete "FWD" (se some, é o sistema AWD); código 24 TCU | [2+] — EndWrench 4EAT ; au7o (agregador) |
| Câmbio: cuidado no elevador | Carro pode se mover com uma roda erguida e motor ligado | AWD eletrônico | Colocar fusível 15 A no soquete FWD antes | [1] — https://automotivetechinfo.com/2004/02/subaru-4eat-phase-1-transmission-diagnosis-and-service |
| Diferencial traseiro (AWD) | Ruído/uivo | Óleo velho/baixo | Nível; trocar GL-5 | [inf] |
| Homocinéticas | Estalos em curva | Coifa rasgada | Inspecionar coifas | [nf] específico |
| Cabos de vela / bobina | Falhas sob carga, código não aparece | Cabos ressecados | Resistência da bobina (seção 1.2) | [inf] |
| Catalisador, A/C, coxins | — | — | — | [nf] específico do modelo |
| Ferrugem | Caixa de roda traseira e soleiras | Idade | Inspeção | [1] agregador (au7o) |
| Rolamentos de roda dianteiros | Ronco que muda em curva | Desgaste, rodas maiores | Folga/ruído | [1] agregador |

Fóruns brasileiros ("Subaru Clube", "subarubrasil"): **não encontrados** nas buscas (nenhum resultado em português relevante).

---

## 6. Manutenção
| Item | Valor | Confiança | Fonte |
|---|---|---|---|
| Óleo do motor | ~4,0 L (4,2 qt EUA); viscosidade de época 5W-30 (frio) / 10W-30 ou 10W-40 | [2+] para ~4 L | https://www.amsoil.com/lookup/auto-and-light-truck/1994/subaru/impreza/1-8l-4-cyl-engine-code-2-ej18s-x/ ; resumo bolidenforum (1994 Impreza LS 1.8) |
| ATF — tipo | Dexron II (época); hoje Subaru ATF/ATF-HP também indicado como compatível. Manual 1993 diz tipo "AF" | [2+] Dexron II | resumos bolidenforum e bobistheoilguy ; https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/maintenance/fluids/fluid_a/t/component_information/specifications/capacity_specifications/ |
| ATF — capacidade total | ~7,9 L (8,3 qt) | [2+] | resumos bolidenforum (1994 LS 1.8 e Loyale 1.8) |
| ATF — troca simples (dreno) | ~2,5 L; depois aquecer, passar todas as marchas e conferir na posição P | [1] | workshop-manuals (acima) |
| Diferencial dianteiro (separado no 4EAT) | Óleo de engrenagem **GL-5** (não ATF); ~1,2 L (valor de outros modelos) | [1] tipo (correção oficial Subaru) ; [1] volume | https://automotivetechinfo.com/2002/06/subaru-4eat service-correction/ ; https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/maintenance/fluids/fluid_differential/component_information/specifications/capacity_specifications/ |
| Diferencial traseiro (AWD) | **0,8 L**, GL-5 75W-90/80W-90 | [2+] | workshop-manuals (acima) ; resumo bolidenforum (0,76–0,8 L) |
| Líquido de arrefecimento | Capacidade e tipo: [nf] | [nf] | — |
| Velas | NGK **BKR6E-11** (OEM 22401AA310); folga **1,0–1,1 mm**; aperto 41–47 N·m (30–35 lbf·ft) | Folga e torque: [2+] (manual + varejista 0,044") ; modelo: [1] | https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/maintenance/tune-up_and_engine_performance_checks/spark_plug/component_information/specifications/ ; resumo de busca (go-parts / ACDelco 41-602) |
| Correia dentada | Inspecionar a cada 30.000 mi (~48.000 km); **trocar a cada 60.000 mi (~96.000 km)** (fora da Califórnia). Por idade, muitos recomendam ~7 anos — num carro de 1993, se não há registro, **trocar já** | [2+] | https://automotivetechinfo.com/2007/07/subaru-timing-belt-inspection-and-replacement-step-by-step ; resumo de busca (go-parts / ahgautoservice) |
| Junto com a correia | Trocar correias de acessórios; avaliar polias, tensor automático, retentores e bomba d'água (kits do EJ18 incluem bomba) | [2+] | automotivetechinfo (acima) ; https://www.godpt.com/products/timing-belt-kit-hydraulic-tensioner-water-pump-fit-subaru-ej18-ej22-90-feb-97 |
| Torques críticos (cabeçote, polia, etc.) | [nf] (páginas com torque bloquearam acesso) | [nf] | — |
| Ponto de ignição | [nf] valor; procedimento: ligar conectores verdes e checar com lâmpada em marcha lenta | [1] procedimento | EndWrench (seção 2.3) |

---

## 7. Manuais (não baixados)
| Título | URL | Tamanho | Oficial? | Direitos autorais (aparente) |
|---|---|---|---|---|
| Dados de oficina online — Impreza Wagon AWD 1.8 SOHC 1993 (especificações, códigos, diagramas; parte dos valores está em imagens) | https://workshop-manuals.com/subaru/impreza_wagon_awd/f4-1820cc_1.8l_sohc/fullindex | página web | Não (base estilo Mitchell/ALLDATA republicada) | Conteúdo de terceiros com anúncios; uso para consulta |
| "1993-1996impreza.pdf" (documento OEM, citado como tendo "Diagnosis Chart with Trouble Code") + fotos `1993ecu.jpg`, `1993ecu1.jpg`, `93pins.jpeg`, `subaru-ej16-or18-wiring-diagram.gif` | https://github.com/rusefi/rusefi_documentation/tree/master/OEM-Docs/Subaru | não informado | Material de fábrica (Subaru) | Repositório público de projeto open source; o material de fábrica em si continua da Subaru — direitos não liberados explicitamente |
| Site Alcyone (SSM do SVX: protocolo, ECU/TCU, códigos, softwares) | http://www.alcyone.org.uk/ssm/ | páginas web | Não (entusiasta) | Documentação comunitária |
| Pinagem ECU Impreza 1991–1996 (rusEFI, EJ20G EDM) | https://wiki.rusefi.com/Subaru-Impreza-1991-1996 | página web | Não | Wiki aberto |
| Subaru EndWrench — artigos técnicos (pré-OBD-II, 4EAT Phase 1, correia dentada) | https://automotivetechinfo.com/2005/08/pre-obd-ii-diagnostics-ignition-the-way-they-were/ ; https://automotivetechinfo.com/2004/02/subaru-4eat-phase-1-transmission-diagnosis-and-service ; https://automotivetechinfo.com/1998/01/subaru-4eat-transmissions | páginas + PDFs (ex.: "Subaru Pre OBD II Diagnostics and Ignition" ~278 KB) | **Sim** (revista técnica da Subaru of America) | Publicação da Subaru, disponibilizada gratuitamente |
| Manuais Subaru diversos (2002–2004 Impreza, EJ22, EA82, WRX DOHC 22 MB) — **não há 1993** | https://raig0.planet.ee/subaru/Manuals/ | variados (ex.: EJ22 Repair Manual 5,7 MB) | Material de fábrica | Hospedagem não oficial; direitos da Subaru |
| Workshop Manual Impreza 1993–1996 (pago) | https://www.emanualonline.com/cars/subaru/impreza/subaru-impreza-workshop-manual-1993-1996-emo-75057.html | não informado | Revenda | Comercial; legitimidade da licença não verificada |
| Haynes Impreza (cobre EJ18) | https://us.haynes.com/pages/odb-fault-codes-car-subaru-impreza | — | Não (editora) | Comercial |
| **Evitar:** PDFs "subaru impreza service manual 1993…" em domínios como openlearning.sky.it, romagis.rcc.int, moments.wbcsd.org, ahecdata.utah.edu, navigator.inspirato.com | — | — | — | Parecem páginas de spam/SEO em sites invadidos; **não abrir** |

Manual do proprietário 1993 no site oficial da Subaru: [nf].

---

## 8. Lacunas (o que falta confirmar)
1. **Código exato do carro** (GF6 AWD x GF5 FWD): olhar o chassi/VIN e a plaqueta no cofre. A FIPE sugere 4x4 no Brasil, mas é [1].
2. **ROM ID da ECU**: só lendo pelo SSM1 (`78 00 00 00` + `00 46 48 49`). Define se a tabela `[7332]` (endereços 0x13xx) vale. Até lá, endereços = [inf].
3. **Localização da ECU e dos conectores** no Impreza 1993 com volante à esquerda: fontes conflitam. Foto da ECU (etiqueta com part number e código) e dos plugues amarelo/verde/preto resolve.
4. **Endereços dos códigos de falha via SSM1** para o EJ18 (os conhecidos são do SVX). Sem isso, a Harumi deve ler códigos pelo método das piscadas, e não por endereço.
5. **TCU do Impreza 1993**: qual luz pisca os códigos (POWER, MANUAL ou AT OIL TEMP) e o procedimento exato. Foto do painel aceso na checagem de lâmpadas ajuda.
6. **Endereços SSM1 da TCU** (temperatura do ATF, marcha, duty C): não encontrados para este câmbio.
7. Ponto de ignição, temperatura da válvula termostática, pressão de óleo, capacidade/tipo do arrefecimento, torques de cabeçote/polia: não encontrados (estão em imagens ou em sites que bloquearam acesso).
8. Se o carro tem EGR, sensor atmosférico ou resistor de CO (versão de mercado): ver na foto do cofre/chicote.
9. Fóruns brasileiros e histórico de importação no Brasil: não encontrados.

**Segurança da integração:** a Harumi só deve enviar os bytes `78…`, `45…`, `12 00 00 00` e `00 46 48 49`. Bloquear qualquer `AA…` (escrita), não aterrar os conectores verdes/pretos automaticamente e nunca apagar códigos.

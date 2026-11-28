# Compatibilidade das peças (20/11/2026)

Conferência das duas listas (`LISTA-DE-COMPRAS.md` e `LISTA-DE-COMPRAS-ECONOMICA.md`) contra o sistema real:
Orange Pi 5 (RK3588S, 8 GB, NVMe), Ubuntu 26.04, rede do carro de ~11 a ~14,8 V com picos, Subaru 1993 (SSM1, sem OBD-II).

**Limite desta conferência:** os anúncios não puderam ser abertos (o AliExpress não carregou os detalhes no navegador
da sessão; a Amazon pediu verificação anti-robô). A análise usa as especificações conhecidas de cada modelo, **de
memória**; o que depende do anúncio está marcado **[VERIFICAR]**, com o que procurar.

Legenda: **OK** compatível · **ATENÇÃO** compatível com um cuidado · **PROBLEMA** do jeito que está não funciona ou falta peça.

## Problemas (resolver antes de comprar)

| # | Peça | Problema | O que fazer |
|---|---|---|---|
| P1 | Saída de som | O Orange Pi 5 tem saída P2 (3,5 mm), mas o som só chega aos alto-falantes se o rádio do carro tiver **entrada AUX**. Rádio original de 1993 não tem. O isolador de ruído sozinho não resolve. | Dizer qual rádio está no carro. Se não tiver AUX: rádio 1-DIN com AUX/USB (barato) ou um amplificador 12 V pequeno ligado direto nos alto-falantes. |
| P2 | Ventoinha Noctua NF-A4x10 5V **PWM** | Conector de 4 pinos; o conector de ventoinha do Orange Pi 5 é de 2 pinos pequeno [VERIFICAR o tipo na placa]. Não encaixa sem adaptador. Além disso, você já tem caixa com ventoinha e dissipadores, e a lista também tem o case de alumínio com fan: são três soluções para a mesma coisa. | Escolher uma. Recomendo o case de alumínio com fan (fica dentro da caixa 2-DIN) e cortar a Noctua, ou comprar a versão **NF-A4x10 5V** sem PWM e ligar no 5 V do conversor. |
| P3 | Hub USB com fonte 12 V (UGREEN ou ORICO) | No carro não há tomada: o hub teria de ser ligado direto nos 12 V, que chegam a 14,8 V com o motor ligado e têm picos. A tolerância de entrada do hub não é informada [VERIFICAR]. | Alimentar o hub por um conversor estabilizado de 12 V (buck-boost) ou trocar por hub alimentado em **5 V** ligado ao conversor 12→5 V 10 A (que tem folga). |
| P4 | Cabo de força do Orange Pi | O conversor 12→5 V 10 A sai em fio; o Orange Pi 5 se alimenta pelo USB-C (5 V, até 4 A). Falta na lista o **cabo USB-C com ponta em fio**, de bitola grossa (≥ 20 AWG, curto). | Acrescentar "cabo USB-C macho pigtail 5 A". Cabo fino derruba a tensão e a placa reinicia sob carga. |

### P1 resolvido no papel: som sem o rádio (rádio original, sem AUX, informado em 20/11/2026)

A caixa 2-DIN da Harumi (`caixa-harumi/`) entra **no vão do rádio**: o rádio original sai de qualquer jeito. O som
passa a ser assim:

```
Orange Pi (saída P2) → isolador de ruído P2 → cabo P2 → 2 RCA → amplificador 12 V 4 canais → alto-falantes originais
                                                                   ↑ remoto (liga/desliga) no ACC, depois do relé temporizador
```

| Item novo | Qtd | Observação |
|---|---|---|
| Amplificador automotivo 12 V **4 canais**, entrada RCA, com fio remoto | 1 | Pequeno (ex.: linha Taramps TS 400x4 ou módulo TDA7850 4×50 W, de memória) [VERIFICAR preço e anúncio]. 4 canais se o carro tiver 4 alto-falantes; 2 canais se tiver só os da frente. |
| Cabo P2 macho → 2 RCA macho (1 m) | 1 | Entre o isolador e o amplificador. |
| Cabo 4 mm² + fusível de 30 A junto da bateria | — | Alimentação do amplificador; o valor do fusível segue o manual do amplificador escolhido. |
| Fio paralelo 1,5 mm² para alto-falantes | ~4 m | Só se o chicote original não for aproveitado. |

Cuidados:
- Ligar o **remoto do amplificador depois** que o Orange Pi estiver ligado e desligar **antes** dele desligar,
  para evitar o estalo na partida. O sinal sai do mesmo circuito ACC + relé temporizador.
- Identificar no conector do rádio original quais fios são dos alto-falantes (multímetro, ~4 Ω cada par) antes de cortar.
- Volume: o amplificador fica fixo em ganho baixo; o volume é controlado pela Harumi.
- O rádio FM some. A Harumi já tem rádio pela internet; FM offline exigiria um receptor USB (RTL-SDR), opcional.
- Se o chiado da saída P2 do Orange Pi incomodar, uma placa de som USB resolve (opcional, ocupa uma porta do hub).

## Atenção (compatível com um cuidado)

| Peça | Cuidado |
|---|---|
| Case de alumínio Orange Pi 5 | Tem de ser do **Orange Pi 5** (não 5 Plus, 5 Pro, 5 Max nem 5B: placas diferentes). Confirmar que o fundo tem espaço para o **NVMe** já instalado [VERIFICAR no anúncio]. |
| Optoacoplador PC817 4 canais | Escolher a variação para **entrada de 12 V** (o resistor de entrada muda); a de 3,3/5 V queima com 12 V. A saída deve ser alimentada com **3,3 V** do Orange Pi, não 5 V. |
| Modem 4G Huawei E3372h-607 | No Linux funciona sem driver (modo HiLink, aparece como rede). As bandas eu não confirmo de memória: exigir **B3 (1800) e B28 (700)**, de preferência também B7 (2600) [VERIFICAR com o vendedor]. Sem B28 perde sinal na estrada. |
| Bluetooth USB | O Orange Pi 5 não tem Bluetooth embutido. O **TP-Link UB500** (chip Realtek RTL8761BU) é suportado no Ubuntu. O UGREEN do AliExpress não informa o chip: há modelos com chip Barrot que **não funcionam no Linux** [VERIFICAR]. Recomendo pagar mais pelo UB500. |
| TPMS Bluetooth | Ainda sem o protocolo. Só serve se os sensores transmitirem por anúncio BLE que dê para decodificar. Mande o nome do modelo ou do aplicativo antes de comprar. |
| Adaptador FT232RL (SSM1) | O de R$ 9,84 quase certamente é chip clone; no Linux funciona com o driver padrão. O SSM1 usa velocidade não padrão (1953 bps, de memória), e o FT232R aceita. Deixar o jumper em **5 V**. |
| Medidor INA226 | Usar só para medir **tensão** (entrada até 36 V). Não passar corrente do carro pelo resistor de medição dele (ele aguenta pouco). Precisa ligar o I2C do Orange Pi. |
| Ultrassom JSN-SR04T / AJ-SR04M (Ali) | O anúncio mistura dois modelos. Comprar os 12 **do mesmo modelo** e na variação **módulo + sensor** (R$ 10,21 cada parece ser só uma parte) [VERIFICAR]. Zona morta de ~20–25 cm. |
| Placa de captura Ezcap158 | Confirmar que é **UVC** (funciona sem driver); se não for, confirmar o chip [VERIFICAR]. |
| Kit 360 | Continua dependendo de ter **saída AV/CVBS**; sem ela, a placa de captura não tem o que ler. |
| Mini560 PRO 5 V | Confirmar a tensão máxima de entrada [VERIFICAR]; com o TVS e o filtro do projeto fica protegido. |
| GPS VK-162 de R$ 24,33 | Funciona (gpsd); sem GLONASS, demora mais a achar sinal. O do Amazon com M8030 é melhor. |
| Bateria do vigia | O carregador SK35L muda a tensão conforme a bateria: **14,4 V** para LiFePO4, **13,8 V** para a selada. Ajustar antes de ligar. |

## Compatíveis

Conversor 12→5 V 10 A (variação 10 A) · relé temporizador ACC (até ~10 A, sobra) · fusíveis e porta-fusível ·
microfone USB (sem driver) · isolador de ruído P2 (depois de resolver P1) · XH-M609 · ESP32-S3 N16R8 (pinos 26–37
já evitados no projeto) · radar HLK-LD2451 (5 V, UART 3,3 V) · lidar TFmini Plus (5 V, UART 3,3 V) · resistores ·
cabo manga · espaçadores · câmera USB opcional · MPU6050 opcional · tela 7" já comprada (HDMI + USB do touch).

## Portas USB (conta feita)

O Orange Pi 5 tem 1 USB 3 + 2 USB 2 (o USB-C é a alimentação). Dispositivos: modem, GPS, microfone, Bluetooth,
FT232RL, captura, ESP32 do nó dianteiro, touch da tela e câmera opcional = **9**. O hub de 7 portas é necessário.

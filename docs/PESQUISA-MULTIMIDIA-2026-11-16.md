# Pesquisa: o que as multimídias têm e o que falta na Harumi OS (16/11/2026)

Alvo: Harumi OS no Orange Pi 5 (8 GB, RK3588S, Ubuntu 26.04), Subaru Impreza perua 1993 (EJ18, automático, sem CAN/OBD-II, protocolo SSM1). Premissas: internet própria (4G), IA embarcada, **sem depender de celular**.

## Método

- Três pesquisas paralelas (P-A: Tesla, Rivian, Polestar, Android Automotive/Google built-in; P-B: CarPlay, Android Auto, BMW iDrive, Mercedes MBUX; P-C: centrais chinesas e projetos Linux abertos).
- Motor de busca: ferramenta WebSearch do Claude Code (**não é o Google**; o provedor não é informado). Cada página citada foi aberta e conferida (WebFetch ou navegador embutido), salvo onde marcado.
- Classes de fonte: **A** documentação oficial · **B** release/página do fabricante · **C** imprensa independente · **D** loja/fórum/espelho de manual (**não confirmado**).
- Trechos: paráfrase fiel com a seção indicada, para conferência na fonte (regra de direitos autorais do ambiente limita citações literais).
- Nenhum dado pessoal ou do projeto foi enviado nas buscas.

## 1. O que o mercado tem (resumo por tema, com fonte)

### Navegação
| Recurso | Quem tem | Fonte (classe) |
|---|---|---|
| Mapa sempre na tela + curva a curva | Tesla, Rivian, Polestar, Google built-in | tesla.com/ownersmanual/model3, "Map Overview" (A); rivian.com/connect-plus (B) |
| Mapas offline baixados pelo padrão de trajetos; vencem em 1 ano | Polestar 2 (2025), Google built-in | polestar.com/us/manual/polestar-2/2025 (A); support.google.com/built-in/answer/11013995 (A) |
| Trânsito ao vivo, evitar pedágio/balsa | Tesla; Polestar só no plano Plus | manual Tesla, "Navigation Settings" (A); polestar.com connected-services (B) |
| Relatar ocorrência na rota (acidente, obra) | Google built-in | support.google.com/built-in/answer/16537773 (A) |
| Mapa 3D com prédios e relevo | Android Auto (anúncio 12/05/2026) | blog.google android-in-cars-updates (B) |
| Destino previsto (agenda, mensagens) | CarPlay | apple.com/ios/carplay (B) |
| Busca conversacional de lugares, com memória | Mercedes CLA (Google) | googlecloudpresscorner.com, 13/01/2025 (B) |
| Computador de bordo por viagem | Tesla | manual Tesla, "Trip Information" (A) |

### Mídia e entretenimento
| Recurso | Quem tem | Fonte |
|---|---|---|
| Rádio, Bluetooth, USB (fonte local, sem internet) | Tesla; Rivian | manual Tesla, "Media" (A); rivian.com/support media-apps (A) |
| Streaming (Spotify, TuneIn) com dados próprios | Tesla, Rivian (Connect+), Google | idem (A) |
| Vídeo só parado; andando pausa o vídeo e mantém o áudio | Tesla, Android Auto, regra AAOS "Distraction Optimized" | manual Tesla, "Theater" (A); source.android.com driver_distraction (A) |
| Rádio pela internet, diretório aberto e gratuito | Radio Browser (API livre) | api.radio-browser.info (A) |
| Equalizador, limitador, volume automático | Centrais chinesas (DSP); Linux: EasyEffects/PipeWire | github.com/wwmm/easyeffects (A) |
| Volume por velocidade | ATOTO (pelo GNSS da central) | atotodirect.com (D, não confirmado) |
| Jogos/Toybox só parado | Tesla | manual Tesla, "Theater, Arcade, and Toybox" (A) |

### Voz e IA
| Recurso | Quem tem | Fonte |
|---|---|---|
| Assistente conversacional (Grok, Gemini, MBUX/ChatGPT) | Tesla (exige conexão), Rivian (inglês, Connect+), Google, Mercedes | tesla.com/support/grok (A); android.com/auto (B); press kit CLA (B) |
| Perguntas sobre o manual do carro | Rivian, Google/Volvo (Brasil, 03/06/2025) | PDF R2 Rivian (B); support.google.com/built-in/answer/15462891 (A); volvocars.com/br (B) |
| Explicar alertas e guiar a solução | Rivian; Tesla tem tabela de códigos | PDF R2 Rivian (B); manual Tesla, "Troubleshooting Alerts" (A) |
| Voz offline (só o básico) | Google built-in | support.google.com/built-in/answer/11013995 (A) |
| Rotinas se-então | Mercedes Classe E | media.mercedes-benz.ca (B, página hoje 404) |

### Câmeras, segurança e privacidade
| Recurso | Quem tem | Fonte |
|---|---|---|
| Dashcam em loop (sobrescreve o mais antigo), salvar trecho com um toque | Tesla, Rivian, Polestar 4, Mercedes CLA no Brasil | manual Tesla, "Dashcam" (A); manual Polestar 4 2026 (A); vrum.com.br 26/10/2026 (C) |
| Requisitos de mídia: ≥ 64 GB, ≥ 4 MB/s, exFAT | Tesla | manual Tesla (A) |
| Gravação só local, criptografia opcional | Tesla, Polestar | manual Tesla, "Dashcam" (A) |
| Vigilância parado (Sentry, Gear Guard) | Tesla, Rivian | manual Tesla (A); rivian.com/support (A) |
| Câmera de ré USB por V4L2 | Linux: GStreamer v4l2src; openDsh | gstreamer.freedesktop.org (A); github.com/openDsh/dash (A) |
| Guias de ré dinâmicas | Centrais chinesas (exigem ângulo de direção) | vhedia.tawk.help (D), no Subaru só **guias estáticas** |
| Controles de privacidade por câmera e localização | Rivian, Google | rivian.com/support (A); support.google.com/built-in/answer/9941814 (A) |
| PIN para dirigir, modo manobrista | Tesla | manual Tesla (A) |
| Perfil de convidado sem dados persistentes | Polestar, AAOS, BMW | manual Polestar 4 (A); source.android.com multi_user (A) |

### Sistema, energia e hardware
| Recurso | Quem tem | Fonte |
|---|---|---|
| OTA com volta à versão anterior (A/B) | Tesla, Rivian, Polestar, Mercedes; Linux: RAUC | rauc.io (A); manuais (A) |
| Desligamento seguro pelo pós-chave (ACC) com corte retardado | Crankshaft (5 s), CarPiHAT | github.com/opencardev/crankshaft wiki (A); cnx-software.com (C) |
| Entradas isoladas de ré e iluminação | CarPiHAT | cnx-software.com (C) |
| GPS (posição e velocidade) | gpsd | gpsd.gitlab.io (A) |
| Modem 4G | ModemManager + NetworkManager | modemmanager.org (A) |
| TPMS por BLE ou 433 MHz | bleak; rtl_433 | github.com/andi38/TPMS (A); github.com/merbanan/rtl_433 (A) |
| Tema dia/noite pelo sol | astral (Python) | astral.readthedocs.io (A) |
| Comandos do volante/GPIO como teclas | openDsh; python-evdev | github.com/openDsh/dash (A) |
| Painel digital com estilos (velocímetro, conta-giros, combustível, temperatura) | CarPlay Ultra, BMW, Mercedes | apple.com/newsroom 05/2025 (B) |
| Widgets/cards na tela inicial | CarPlay Ultra, Android Auto, MBUX Zero Layer | idem (B) |

### Específico do Subaru 1993
- **SSM1**: serial 1953 baud, TTL 5 V; fornece velocidade, rotação e temperatura da água, p1kachu.pluggi.fr, 28/12/2018 (C). **[VERIFICAR ECU e pinagem do EJ18 1993 antes de ligar qualquer fio.]** OBD-II/ELM327 e FreeSSM (só a partir de 1999) **não servem**.
- Nenhum projeto aberto serve de base pronta para o OPi5: AGL só suporta Raspberry Pi 4 (docs.automotivelinux.org, A); openDsh e OpenAuto parados desde 2024; Crankshaft ativo, mas para Raspberry Pi e Android Auto.
- Risco de plataforma: a imagem comunitária de Ubuntu para RK35xx (Joshua-Riek) foi **arquivada** (GitHub, A). Decodificação de vídeo por hardware entrou no kernel principal; **codificação ainda não** (Collabora, B), a dashcam pode precisar gravar por software. [VERIFICAR no Ubuntu 26.04 da placa]

## 2. O que a Harumi já tem (estado em 16/11/2026)

| Tema | Na Harumi | Observação |
|---|---|---|
| Mapa sempre aberto, busca, rota, mapa offline Brasil (2,9 GB) | Sim | Roteamento é online; sem GPS ainda |
| Postos (18.259) e card de combustível | Sim | Offline |
| YouTube, navegador, Claude, ChatGPT, Waze dentro da Harumi | Sim | Electron WebContentsView |
| Bloqueio de vídeo andando (pausa > 8 km/h) | Sim | Depende do GPS para valer |
| Spotify (dispositivo Spotify Connect) | Parcial | Controle na tela aguarda o Client ID |
| IA local (Qwen 3.5 2B, ~14,5 tok/s) + respostas do manual do carro | Sim | Offline |
| Painel do carro (velocímetro, 6 blocos de estado) | Sim | Velocidade espera GPS/SSM1 |
| Teclado na tela pt-BR, favoritos Casa/Trabalho, dock editável, volume | Sim | - |
| Infraestrutura de módulos e plugins (T0) | Sim | `linux/modules/*.js`, `linux/plugins/*.py`, `harumi_store.py` |
| Auditoria de acessibilidade/CSP (T7) | Sim | 0 alvos < 44 px, 0 textos < 14 px, 0 contraste baixo, 0 erros |

## 3. O que falta: lista priorizada

Nota = 2·Valor + Segurança − Esforço − Risco (cada um de 1 a 5). Dep = depende de hardware ainda não instalado.

| # | Item | V | S | E | R | Nota | Dep | Fase |
|---|---|---|---|---|---|---|---|---|
| 1 | Fonte de GPS (gpsd) + simulador com selo "SIMULAÇÃO", desligado por padrão | 5 | 5 | 2 | 1 | 12 | GPS USB | T1 (software já) |
| 2 | Política térmica: suspender a IA acima de ~80 °C, retomar abaixo de ~70 °C | 4 | 5 | 1 | 1 | 11 | - | T4 |
| 3 | Privacidade: modo manobrista com PIN (hash com sal, 0600), "apagar tudo", porta 9222 só com `HARUMI_DEBUG=1` | 4 | 5 | 2 | 1 | 10 | - | T3 |
| 4 | Garagem: computador de bordo, abastecimentos com km/l, lembretes de manutenção digitados pelo usuário | 5 | 2 | 2 | 1 | 9 | - | T2 |
| 5 | Novos comandos locais da assistente (volume, abrir app, "quanto falta", modo tela limpa) | 4 | 3 | 2 | 1 | 8 | - | T5 |
| 6 | Conforto: modo tela limpa, relógio grande, lembrete de descanso a cada 2 h | 3 | 4 | 1 | 1 | 8 | - | T6 |
| 7 | Desligamento seguro pelo ACC (relé/optoacoplador no GPIO) | 5 | 5 | 3 | 2 | 10 | Módulo ACC | Hardware |
| 8 | Câmera de ré USB (V4L2/GStreamer) com guias estáticas, entrada de ré isolada | 5 | 5 | 3 | 2 | 10 | Câmera + optoacoplador | Hardware |
| 9 | Leitura SSM1 (velocidade, rotação, temperatura), somente leitura | 5 | 4 | 4 | 3 | 7 | Cabo SSM1 | Hardware |
| 10 | Voz falada (TTS: Piper ou espeak) | 4 | 4 | 2 | 1 | 9 | Alto-falante | Fase C (autorizar download) |
| 11 | Rádio pela internet (Radio Browser) e música local (MPD) | 4 | 2 | 2 | 1 | 7 | - | Fase C |
| 12 | Roteamento offline (OSRM/Valhalla com recorte do PR) | 4 | 3 | 4 | 3 | 4 | - | Fase C (download grande; após a fonte 5V 4A) |
| 13 | Controle do Spotify na tela (Web API, PKCE, Client ID do usuário) | 4 | 1 | 2 | 2 | 5 | Client ID | Fase C |
| 14 | Gerenciador de rede/4G (ModemManager) na tela | 4 | 2 | 3 | 2 | 5 | Modem 4G | Fase C |
| 15 | Dashcam em loop (`ffmpeg -f segment`, sobrescreve o mais antigo, só local) | 4 | 4 | 3 | 3 | 6 | Câmera; codificação por hardware [VERIFICAR] | Hardware |
| 16 | Tema dia/noite pelo sol (astral) ou fio de iluminação | 2 | 3 | 1 | 1 | 5 | - | Depois |
| 17 | Equalizador (EasyEffects) e volume por velocidade | 3 | 1 | 2 | 2 | 3 | GPS/SSM1 | Depois |
| 18 | TPMS (BLE ou 433 MHz) | 2 | 3 | 3 | 2 | 2 | Sensores | Depois |
| 19 | OTA com volta à versão anterior (RAUC ou git + verificação) | 3 | 3 | 4 | 3 | 2 | - | Depois |

**Fora do escopo** (dependem de celular ou de CAN): CarPlay/Android Auto, mensagens e chamadas por Bluetooth, leitura de sinais pelo barramento do veículo (VHAL), guias de ré dinâmicas.

## 4. Diferenciais que a Harumi já tem sobre a concorrência

1. **IA local e offline.** Grok, Rivian Assistant e MBUX exigem nuvem e assinatura; o Google offline só faz o básico. A Harumi responde sobre o manual do carro sem internet.
2. **Mapa do Brasil inteiro offline**, sem vencimento de 1 ano.
3. **Sem conta nem assinatura**: e dados ficam na placa (LGPD).

## 5. Lacunas desta pesquisa

- Fichas oficiais Teyes e Aikon não indexadas; trechos de centrais chinesas vieram de lojas (classe D).
- Mapas offline da Tesla e da Rivian: sem fonte encontrada (não significa que não exista).
- Disponibilidade no Brasil confirmada só para CarPlay (lista oficial da Apple) e indícios para Google built-in/Volvo e Mercedes CLA.
- Suporte do Ubuntu 26.04 a codificação de vídeo por hardware no OPi5: não verificado.

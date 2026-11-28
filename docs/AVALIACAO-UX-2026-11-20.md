# Avaliação de UX da Harumi OS e novos temas (20/11/2026)

Avaliação heurística feita na placa (Orange Pi 5, monitor 2560×1440) e na cópia do Windows em 1024×600 (tela de 7" do
carro), com os testes automáticos `tools/ux_walkthrough.py` (9 tarefas) e `tools/ux_audit.py` (alvos, textos, nome
acessível, contraste, CSP) e uma medição extra com os limites de carro.

## Referências usadas

| Fonte | O que diz | URL |
|---|---|---|
| Android for Cars (Google) | alvo de toque mínimo 76×76dp; texto de decisão 32dp e secundário 24dp; ícones ≥ 36dp; entender o estado em até 2 s | developers.google.com/cars/design/android-auto/design-system/sizing e …/design-foundations/visual-principles |
| Android for Cars — cor | contraste ≥ 4,5:1; cores "construídas a partir do preto"; tema claro de dia e escuro à noite; acento com moderação | developers.google.com/cars/design/automotive-os/design-system/color |
| NHTSA (2013, voluntário) | olhada ≤ 2 s; total ≤ 12 s por tarefa (critério aplicado a discagem e rádio, não à digitação de destino) | nhtsa.gov — Visual-Manual Driver Distraction Guidelines |
| Polestar 2 | modo "Calm": só velocidade e o essencial; interface minimalista, sem cores berrantes | polestar.com/…/polestar-2/infotainment; Engadget (2019) |
| BMW Panoramic iDrive | layout da tela central personalizável por widgets | bmwgroup.com/en/news/general/2025/newidrive.html |
| CarPlay Ultra | temas com cores e fundo personalizáveis; widgets na tela e no painel | apple.com/newsroom/2025/05/carplay-ultra… |
| Tesla (v11/v12) | cartões, visualização central do carro, player de mídia fixo | notateslaapp.com (fonte de entusiastas, não oficial) |

## Medições (tela inicial, 1024×600)

| Critério | Antes | Depois | Padrão de carro |
|---|---|---|---|
| Botões com lado < 64 px | 22 de 30 | 17 de 30 (Calma: 17) | 0 abaixo de 76 dp |
| Textos < 24 px | 23 de 24 | ainda a maioria | secundário 24 dp |
| Mediana do tamanho de texto | 15 px | 16–20 px nas telas | 24–32 dp |
| Contraste < 4,5:1 (auditoria) | 0 (Harumi) | 0 nos 3 temas | ≥ 4,5:1 |
| Teste de uso | 9/9 | 9/9 | — |

Tempo e toques das tarefas na placa: buscar destino 7 toques / 15,6 s; perguntar à Harumi 7 / 8,1 s; YouTube 8 / 21,5 s
(abrir, tela cheia, digitar, buscar, fechar); volume 5 / 4,5 s; achar Ajuste de Internet 5 / 3,1 s; ver painel do carro 3 / 1,5 s.

## Achados (gravidade 1 = leve, 4 = crítica)

| # | Gravidade | Achado | Situação |
|---|---|---|---|
| 1 | 3 | Alvos de toque e textos abaixo do padrão automotivo; na tela de 7" o padrão inteiro não cabe | Corrigido em parte: controles principais com 64 px, secundários com 56 px, textos das telas maiores; tema Calma vai além |
| 2 | 3 | Digitar destino leva 15,6 s e 7 toques (acima dos 12 s de referência) | Mitigado: digitação já bloqueia com o carro andando; usar voz ("me leva para…") e Casa/Trabalho. Pendente: favoritos recentes com um toque |
| 3 | 2 | "3D" no canto do topo é informação técnica sem valor para o motorista | Corrigido (removido) |
| 4 | 2 | Tela Carro mostrava quatro "—" sem explicar | Corrigido: frase "Sensores do carro ainda não instalados…" até haver dado |
| 5 | 2 | Dois ícones de carro na barra (Vista do carro à esquerda e "Carro" no dock) | Corrigido: o "Carro" do dock virou Waze (troca feita uma vez no dock salvo); "Carro" na gaveta abre o painel do carro |
| 6 | 2 | Topo com jargão: "Rede do Orange Pi" e "Placa 47 °C" | Corrigido: topo mostra "Online" ou "Sem internet · mapa offline"; a temperatura só aparece a partir de 75 °C ("Central quente") |
| 7 | 2 | Botões "Trocar" e tela cheia em todas as telas chamam atenção o tempo todo | Corrigido: um único botão "•••" por tela; o menu traz "Abrir em tela cheia", o conteúdo, o layout e o navegador |
| 8 | 2 | Tema Dia com mapa escuro | Corrigido: mapa claro no Dia (inversão de cor com correção de matiz); 60 quadros/s com zoom na placa |
| 9 | 3 | No tema Dia, teclado com "Fechar teclado" quase invisível (1,04:1) e botões do app original em 4,0:1 | Corrigido (0 problemas de contraste nos 3 temas) |
| 10 | 1 | Ícones da barra sem rótulo (estrela = Harumi, câmera = Câmeras) | Corrigido: rótulo sob os ícones em telas a partir de 1280×761 (na de 7" não cabe) |

## Temas novos (Ajustes › Aparência)

- **Harumi** — o visual de sempre (rosa suave sobre ameixa escura).
- **Calma** — inspirado no modo Calm do Polestar: grafite, um acento areia, sem bordas nem sombras, números e textos
  maiores, botões de mídia e de troca maiores. Para estrada.
- **Dia** — claro, texto quase preto, acento azul-petróleo; para sol forte (recomendação do Android for Cars).
- **Automático** — Dia das 6h às 18h e Harumi no resto (horário fixo e aproximado: sem GPS não há nascer/pôr do sol).

Todos passaram na auditoria (0 alvos < 44 px, 0 textos < 14 px, 0 botões sem nome, 0 contraste baixo, 0 erro de CSP).

## O que não foi testado

- Toque real no monitor/tela de 7" (os testes usam eventos simulados).
- Leitura sob sol forte e à noite dentro do carro.
- Medição de olhada (eye-tracking); os tempos acima são da automação, não de uma pessoa.

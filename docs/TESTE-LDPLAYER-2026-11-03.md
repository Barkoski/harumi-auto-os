# Teste no LDPlayer — 03/11/2026

APK do commit `6c55276` (0.3.15-dev.1), instalado no LDPlayer do Lucas (`emulator-5554`).

## Ambiente

| Item | Valor |
|---|---|
| Android | 14 (API 34), x86_64, WebView Chrome 124 |
| RAM | 8 GB (igual ao anúncio da central) |
| Tela | Alterada de 1920×1080/280 dpi para **2000×1200/240 dpi**, a resolução anunciada da central. O valor de 240 dpi é suposição e precisa ser medido na central. |
| Fuso | Continua `America/Santiago`. Mudar exige root; o horário atual coincide com o de Brasília (−03). |
| Idioma | Continua pt-PT. Mudar exige o menu de Configurações do LDPlayer. |

Para desfazer a tela: `adb shell wm size reset` e `adb shell wm density reset`.

## Resultados

| Teste | Resultado |
|---|---|
| Abertura do app | OK, 2,8 s. Sem travamento e sem erro de JavaScript. |
| Layout em 2000×1200 | OK. Único problema: o texto "Internet disponível" fica cortado na barra lateral. |
| Cópia dos modelos (v2) | Ocorreu na primeira conversa (`.ready` = `v2:731386193:24`) |
| Conversa | Respondeu e falou com a voz Supertonic. Primeiro texto em 10–14 s; respostas curtas instantâneas pelo atalho local. |
| "Por favor, tudo bem?" | Correto: "Oi, Lucas! Tudo bem por aqui. E você?" |
| "Qual a capital do Paraná?" | Correto: Curitiba |
| "O que é diagnóstico diferencial?" | Foi para a conversa (correto). A resposta puxou para falha mecânica e atingiu o limite de 60 s, ficando parcial. |
| "Quero ir para a praia, o que recomenda?" | Foi para a conversa (correto), mas a resposta falou do diagnóstico do carro sem que ele fosse mencionado. |
| "Me conta uma curiosidade sobre o Impreza" | O modelo não contou nenhuma curiosidade e só devolveu a pergunta. |
| "Abra o Spotify" (não instalado) | A Harumi disse "Vou abrir seu aplicativo de música" e logo depois veio o aviso "Nenhum app identificado". As duas mensagens se contradizem. |
| "Trace uma rota para o centro de Londrina" | Pediu confirmação. Sem app de mapas instalado, mostrou aviso claro e não travou. |
| "Como está o carro?" | Disse que não há adaptador e não inventou leituras. O texto começa com "DESCONECTADO" em caixa alta. |
| Parar no meio da resposta | Parou na hora. A conversa seguinte funcionou normalmente. |
| Mapa interno (Rondonópolis → Londrina) | Rota de 1.100 km e 14 h 57 min, desenhada no mapa |
| Atlas Brasil, Aplicativos, Câmeras 360° | Abriram. Sem app de câmera instalado, o atalho de câmeras mostra o seletor de apps. |
| Voltar | Fecha o painel ou diálogo aberto; com nada aberto, sai do app |
| **Troca dia/noite** | **Falha confirmada:** a tela é recriada e a conversa se perde. Na central, isso pode acontecer quando o farol é ligado. Falta `configChanges` no manifesto. |

## Limites deste teste

- O LDPlayer roda no processador do PC, por isso a velocidade da IA aqui não vale para a central.
- O microfone não foi testado, porque o LDPlayer não tem microfone real configurado.
- Nenhum app de terceiros foi instalado (Maps, Waze, Spotify), então só os avisos de "não instalado" foram testados.

## Correções (mesmo dia) e reteste no LDPlayer

| Falha | Correção | Reteste |
|---|---|---|
| Troca dia/noite apagava a conversa | `configChanges` na MainActivity: a tela não é mais recriada | OK. A conversa ficou intacta na ida para noite e na volta para dia. |
| A resposta sobre a praia falava do diagnóstico | O estado do scanner só entra no prompt quando a pergunta é sobre o carro (`LocalCommandParser.aboutCar`) | OK. A resposta não mencionou o carro. |
| "Abra o Spotify" prometia abrir e depois falhava | A Harumi verifica antes se há app de música | OK: "Não encontrei um aplicativo de música instalado…" |
| Rota sem app de mapas | Mesma verificação antes de prometer | OK: "Não encontrei Waze, Google Maps…" |
| "DESCONECTADO" em caixa alta | Texto reescrito em linguagem natural | OK |
| "Internet disponível" cortado | O texto da barra lateral quebra linha | Não conferido em captura |
| Curiosidade sobre o Impreza | Liberar respostas de conhecimento geral fez o modelo **inventar nomes e datas**, então a liberação foi desfeita. A Harumi volta a dizer que não sabe com segurança. | Comportamento esperado: preferir "não sei" a inventar |

O botão **Instalar apps essenciais** foi adicionado em Aplicativos. Ele abre a Play Store no próximo app que falta, na ordem Waze, Google Maps, YouTube e Spotify, e a contagem é atualizada ao voltar. No reteste, o botão abriu a Play Store. O LDPlayer pede login no Google, então nenhum app foi instalado.

Verificação: 114 testes unitários sem falhas e lint sem erros. Respostas longas ainda atingem o limite de 60 s no LDPlayer, que usa o processador do PC; isso precisa ser medido na central.

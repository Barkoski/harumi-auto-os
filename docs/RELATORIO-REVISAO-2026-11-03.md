# Revisão noturna — 03/11/2026

Branch `revisao-noturna-2026-11-03`. **Nada foi commitado**: as mudanças estão na pasta, aguardando sua decisão. O `main` continua como você deixou (commits `385d440` e `b4a972d`).

## Situação verificada

| Verificação | Resultado |
|---|---|
| Build `assembleDebug` (app + kit) | OK |
| Testes unitários | **113 passaram, 0 falhas** (eram 51 ontem) |
| Lint | 0 erros, 8 avisos (iguais aos de antes) |
| Emulador (Android 11, 1920×1080) | App abre sem travamento nem erro de JavaScript; atlas abre; **Voltar fecha o painel** e só sai do app quando nada está aberto; DF do atlas tocável |
| Central real | **Não testado** — nenhum aparelho conectado |

A versão nova que você mencionou é o APK "0.3.15 - nova interface e voz" (03/11, 03:00). O código dela é o mesmo do ponto inicial salvo no Git; suas mudanças de interface foram preservadas.

## O que foi corrigido

**Parte Android (Java/C++)** — revisão completa não achou defeito grave; 13 de gravidade média/baixa:
- "Por favor, tudo bem?" mostrava balão vazio e falso erro de voz → corrigido.
- "Parar" tocado no início de uma resposta podia ser ignorado → corrigido também durante a carga da IA.
- Microfone e áudio da voz não eram liberados em alguns erros → corrigido.
- Lista de apps recalculada várias vezes por segundo na tela principal (lentidão) → cálculo único.
- Mapas falhavam com disco cheio mesmo com internet; limpeza de cache rodava na tela principal → corrigido.
- Instalação dos modelos podia falhar se a tela fosse recriada; modelo trocado não era detectado → corrigido. **Efeito:** na primeira abertura após instalar este APK, os ~700 MB de modelos serão copiados de novo (uma vez).
- "o que é diagnóstico diferencial?" era tratado como pedido de diagnóstico do carro; "quero ir para a praia, o que recomenda?" virava rota com destino errado → agora vão para a conversa.
- Ícone com erro podia derrubar o app → tratado.

**Interface** — nenhum defeito grave, nenhuma injeção de conteúdo:
- Botão **Voltar** do Android fechava o app inteiro → agora fecha o painel aberto.
- Mensagem atrasada abria a conversa por cima do mapa/apps → não abre mais.
- Parar apagava a resposta parcial → preservada.
- Botões abaixo de 48 px e textos de 8–10 px → mínimo 48 px (44 px em telas baixas) e 11 px. Cores e layout não mudaram. Com poucos apps, a aba Instalados agora fica alinhada ao topo.
- Espaçamento quebrado no WebView antigo, avatar piscando, foco perdido ao fechar o mapa, links que não abriam → corrigidos.

**Documentos**: STATUS, ADR-008, GUIA-INICIAL, componentes-ia.json, OTIMIZACAO-0311 e TERCEIROS alinhados ao código (voz Supertonic, contexto 4096, sherpa 2.0.1). TERCEIROS ganhou lista de pendências de licença.

## Sua visão e a avaliação do consultor

**Modelo de IA (Qwen3.5 0.8B):** serve como voz e personalidade da Harumi (conversa curta em português). **Não serve para decidir ações sozinho nem para interpretar o scanner** — modelos desse porte erram intenções e inventam números. Recomendação: comandos sempre resolvidos por regras; a IA só *propõe*; um validador local decide; ações físicas sempre pedem sua confirmação. Não trocar de modelo antes de medir velocidade e temperatura na central (estimativas, não medições: 1,5–2B ainda aceitável; 3–4B lento para voz).

**Construído esta noite (fundações testadas, ainda não ligadas à tela):**
- `ai/tools/`: lista de ferramentas permitidas, validador, classes de risco e confirmação com prazo. A IA nunca executa nada fora da lista; ações físicas exigem confirmação.
- `diagnostics/ssm1/`: leitor do protocolo Subaru (SSM1), **somente leitura** — um teste garante que não existe comando de escrita para a ECU — com simulador. `DiagnosticRules` gera o texto falado copiando os números exatos.
- `location/`: base do GPS independente (leitura NMEA, qualidade do sinal, velocidade para bloquear vídeo em movimento). Não pede permissão de localização ainda.
- `docs/ADR-009-navegacao-offline.md` e `docs/ADR-010-atuadores-e-luz.md` (minutas).

**Por pilar:**
- **GPS independente:** imediato e sem código — instalar Organic Maps ou OsmAnd com o Brasil offline (a Harumi já abre esses apps). Depois, dentro da Harumi: GPS da central + mapa offline (MapLibre) + rotas offline (GraphHopper); 2–6 GB fora do APK (estimativa).
- **Scanner:** o Impreza 1993 provavelmente usa o protocolo SSM1 da Subaru, anterior ao OBD-II (**de memória — confirmar**). Um ELM327 comum provavelmente não funciona. Endereços, velocidade e fórmulas no código estão marcados como "não verificado".
- **Câmeras, rádio, 360°, equalizador, CarPlay/AA:** continuam do sistema original; a Harumi abre esses apps. Capturar câmera por fora arrisca a câmera de ré.
- **Luz:** só auxiliar/interna, por módulo de relés com fusível e interruptor físico; farol, freio e seta nunca por software.
- **YouTube/apps:** abrir e controlar mídia, sim; controlar o app por dentro, não. Bloquear vídeo em movimento (norma do Contran: **confirmar na fonte oficial**).

## O que depende de você

1. **Rodar o kit na central** (`compatibility/LEIA-ME-CENTRAL.md`) e me mandar o JSON — destrava quase tudo.
2. **Fotografar** o conector de diagnóstico do Impreza e a etiqueta da ECU antes de comprar qualquer adaptador.
3. Dizer **quais luzes** quer controlar.
4. Seu celular é **Android ou iPhone**? (define o app companheiro).
5. Instalar Organic Maps/OsmAnd com o Brasil offline como GPS de reserva.
6. Limite de velocidade para bloquear vídeo (o código usa 10 km/h provisório).
7. Aceitar de 2 a 6 GB para mapas offline.
8. Decidir se eu salvo (commit) esta revisão no branch.

## Pendências e avisos

- Testar na central: fala da Harumi cortada por avisos do Waze; troca dia/noite recriando a tela e recarregando a IA.
- Diagnóstico: quando o adaptador falha, a tela diz "desconectado" em vez de "indisponível"; leitura sem fonte pode derrubar o monitor (relevante só com scanner real).
- O APK deste build foi assinado com a chave de depuração padrão do Windows (`~/.android`), a mesma das versões anteriores instaladas no emulador.
- **No emulador**, durante o teste, um toque meu abriu sem querer o seletor de app de um atalho e mudou a associação de um módulo (aviso "Associação atualizada"). Afeta só o emulador; confira em Configurar atalhos.

# Estado em 03/11/2026 — 0.3.15-dev.1

Integração local de LLM, reconhecimento e voz feminina implementada e executada em Android emulado. Comandos tipados de mapas/música/rotas e consulta de diagnóstico integrados à conversa. Pipeline de voz testado com áudio sintético; ruído e microfone da central não homologados.

O modelo é carregado sob demanda. A captura só ocorre por toque e permissão. Câmeras, áudio OEM e MCU permanecem independentes do LLM. HOME desabilitada em todos os builds.

Diagnóstico físico: DESCONECTADO. Contrato de adaptador somente leitura preparado; não existe transporte validado para o Subaru. Não há serviço persistente/boot automático. G2–G4 continuam pendentes. G1 tem evidência de emulador, não de central real.

ABI da central, SoC, RAM disponível, consumo, temperatura, latência real e comportamento de ré/360°/telefonia/ACC precisam de medição no hardware. Informações declaradas pelo sistema não autenticam o hardware.

O histórico v0.2 continua nos registros anteriores. Esta versão substitui a entrega anterior para testes de IA. Sem repositório remoto, publicação ou firmware modificado.

## Voz selecionada

F3 do Supertonic 3, conforme opção 2 aprovada por Lucas. Refinamento: 24 passos, velocidade 1.25, silêncio 0.72 e pronúncia Harumi → Rarumi apenas no texto de síntese. Modelos preparados em pasta privada models-v2, sem reutilizar marcador de instalação do Kokoro. Os arquivos antigos não foram apagados automaticamente. A descrição da versão 0.3 em VALIDACAO-IA.md é histórica.

Atualização 0.3.2: voz F3 com entusiasmo aprovada por Lucas; perfil 1.25/0.72 e apresentação iguais à amostra. Ver docs/VALIDACAO-032.md.

Atualização 0.3.3: Falar com Harumi na HOME, painel Conexões, status observado pelo Android e atalhos Wi-Fi/Bluetooth/redes. Bluetooth/USB físicos dependem da central. Ver docs/VALIDACAO-033.md.

Atualização 0.3.4: opção USB retirada; Wi-Fi/Bluetooth recolhidos como configuração inicial. Status da rede automático. Ativação universal do roteador do telefone não implementada; conferir docs/INTERNET-AUTOMATICA.md. Escopo inclui iPhone e Android de várias marcas.

Atualização 0.3.5: personagem animada com saudação, espera, escuta, processamento e fala; visível na conversa. Ver docs/HARUMI-CONSOLE.md.

Atualização 0.3.6: interface escura e rosa inspirada na Harumi IA, com elementos de OS dos anos 1990; personagem sem quadriculado, composta sobre o painel. Ver docs/INTERFACE-RETRO-036.md.

Atualização 0.3.7: visual retrô substituído pelo estilo original da Harumi IA, adaptado à multimídia. Ver docs/INTERFACE-ORIGINAL-037.md.

Atualização 0.3.8: estrutura da primeira interface com botões grandes, identidade preta/rosa da Harumi e efeitos; seletor de múltiplos apps instalados para navegação/música. Ver docs/INTERFACE-E-APPS-038.md.

Atualização 0.3.9: referência comercial identificada como Aikon Fóton F09-88256/360/G3 conforme código fornecido e catálogo oficial. Política ABI/API, inventário e exportação local no app e em verificador leve independente. Hardware de Lucas ainda não homologado. Ver docs/COMPATIBILIDADE-FOTON-G3.md.

Atualização 0.3.10: personagem parada fora da resposta falada, correção do ciclo da autorização inicial de microfone, falhas/interrupções visíveis e tempo transcorrido. LLM real testado na bancada; entrada de áudio do LDPlayer ainda pendente. Ver docs/RESPOSTA-E-ANIMACAO-0310.md.

Atualização 0.3.11: respostas sociais por regras, prompt/contexto menores, runtime reutilizado, até quatro threads e orçamento de inferência; ações aparecem antes da síntese terminar. Medidas e limites em docs/OTIMIZACAO-0311.md; mapas e pesquisa próprios ainda planejados em docs/MAPAS-E-IA-LOCAL.md.

Atualização 0.3.12: atlas dos estados e fotos das capitais offline; cache PCM da voz aprovada para respostas fixas.

Atualização 0.3.13: planejamento gráfico entre cidades, rota viária real OSRM, mapa OpenStreetMap com zoom/arrasto, comandos locais entre duas cidades e estimativas sem trânsito. Não inclui acompanhamento GPS nem recálculo automático. Ver docs/MAPA-ROTAS-0313.md.

Atualização 0.3.14: painel Aplicativos, catálogo de referência Fóton, inventário do Android, abertura e acesso à loja oficial; funções OEM associáveis aos apps da própria central. Nenhum app de terceiros incorporado ou instalado automaticamente. Pesquisa, fontes e limites em docs/APPS-FOTON-0314.md.

Atualização 0.3.15: launcher inspirado na referência enviada, com dock, grade de ícones, apps instalados com ícones nativos e controles de mídia do Android. Contexto de 4096 tokens, até quatro trocas completas, geração parcial visível e Continuação explícita. Captura não para no primeiro segmento Vosk; janela de 45 s, pausa de 1,8 s após endpoint e conclusão manual. Mensagens até 1600 caracteres. Ver docs/ENTREGA-0315.md.

Revisão 03/11/2026: correções de robustez (diagnóstico único, recriação da WebView, cancelamento da IA) e kit de coleta da central ampliado (compatibility/LEIA-ME-CENTRAL.md).

Botão de voz (ASSIST/VOICE_COMMAND) registrado na MainActivity: abre o painel e ouve. A testar na central com o botão físico/volante; no emulador: `adb shell am start -a android.intent.action.ASSIST`.

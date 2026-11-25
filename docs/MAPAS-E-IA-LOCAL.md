# Harumi: latência, IA e mapas offline

Proposta de evolução de 02/11/2026, a partir da ideia de Lucas. Este documento diferencia a otimização implementada em 0.3.11 dos serviços de mapa e pesquisa que ainda não estão implementados.

## Modelo pronto ou treinado do zero

Recomendação: usar um modelo pronto quantizado de 0,5–1 bilhão de parâmetros e personalizar instruções, ações e acesso a dados. Comparar qualidade em português, latência e RAM na central antes de trocar o Qwen3.5-0.8B atual. Tamanho menor não garante melhor experiência; a troca por 0,5B ainda não foi medida. O [Qwen2.5-0.5B-Instruct oficial](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) é um candidato para comparação, não um substituto já escolhido ou instalado.

Treinar um modelo do zero não é o próximo passo recomendado para este produto. Um eventual ajuste fino pode melhorar estilo ou interpretação de pedidos depois que tivermos testes e exemplos. Não substituirá mapas, algoritmos de rota, índices de endereços ou atualização de informações.

O modelo deve conversar, interpretar a intenção e resumir evidências. Não é um banco confiável de todas as estradas/cidades e não deve calcular coordenadas, distâncias ou trajetos a partir de texto gerado.

## O que mudou na 0.3.11

- Frases sociais curtas como Tudo bem? e o cumprimento repetido do relato usam regras exatas, sem inferência. Pedidos adicionais não são consumidos pelo atalho: Oi, trace uma rota... continua pelo caminho de rota; perguntas sobre o carro seguem diagnóstico. Isso é uma resposta local programada, não demonstração de LLM mais rápido.
- Texto de instrução e histórico enviados ao LLM menores; respostas orientadas a uma ou duas frases. Sem inventar pesquisa web ou recomendações locais quando não há fontes conectadas.
- Contexto nativo de 1024 tokens, até 64 tokens de saída e até quatro threads, conforme CPUs reportadas. Orçamento cooperativo de 20 segundos para a inferência, incluindo processamento do prompt; preparação/cópia de arquivos, carregamento do modelo e voz ficam fora desse orçamento. Não é uma garantia de tempo total de resposta. Pode produzir resposta parcial ou erro de tempo. O orçamento é verificado pelo callback do runtime e entre tokens.
- Contexto nativo reutiliza alocações entre perguntas, limpando todo o estado KV/recorrente a cada geração. Não tenta reusar parcialmente o histórico interno do Qwen híbrido. A memória extra do contexto fica residente até fechar o motor.
- Seletor/confirmador de aplicativos e rotas é apresentado sem aguardar a síntese da frase. A saída para outro aplicativo pode cancelar a fala restante, preservando o áudio do app de destino.
- Modelo e voz aprovados mantidos. Não foi treinado, convertido ou baixado outro modelo nesta etapa. Personagem continua parada fora da fala.

## Arquitetura recomendada para mapas

| Camada | Responsabilidade | Situação |
|---|---|---|
| Atalhos locais | Cumprimentos, comandos, diagnóstico real disponível | Implementada; sem depender do LLM para essas ações |
| Conversa local | Português e explicações curtas com fontes fornecidas | LLM local implementado; qualidade e desempenho físico pendentes |
| Navegadores externos | Maps, Waze e apps offline instalados | Seletores implementados; entrega de destino e navegação real precisam de teste por app |
| Pacotes geográficos | Mapa, grafo viário, endereços e POIs por região | Não implementados dentro da Harumi |
| Base de cidades | Conteúdo de referência com fonte e data | Não implementada |
| Pesquisa online | Buscar informação atual, retornar fonte e momento da consulta | Não implementada; app ainda não tem cliente de pesquisa web |

Duas opções de uso são viáveis e devem coexistir: abrir um navegador externo, ou navegar em uma solução offline. O primeiro backend offline recomendado para validação é um aplicativo pronto, como OsmAnd, via integração documentada. Um mapa realmente embutido e personalizado na Harumi é uma etapa posterior, com motor de desenho e motor de rotas próprios/integrados.

O [OsmAnd documenta navegação offline](https://osmand.net/docs/user/navigation/) e [conteúdo Wikipedia por região](https://osmand.net/docs/user/plugins/wikipedia/). Download, disponibilidade e eventuais recursos/licenças dependem da distribuição e do pacote escolhido. O aplicativo instalado não autoriza a Harumi a ler livremente seu armazenamento privado; o acesso deve usar interfaces documentadas ou pacotes próprios.

Para um mapa visual próprio, [MapLibre Native Android](https://maplibre.org/maplibre-native/android/api/-map-libre%20-native%20-android/org.maplibre.android.offline/index.html) oferece recursos de regiões offline. Ele desenha mapas; a aplicação ainda precisa de busca de endereços, GPS, cálculo de rotas, recálculo, instruções e gerenciamento de áudio. Um motor como [BRouter](https://brouter.de/) exemplifica cálculo offline separado do desenho do mapa. A seleção final do motor exige teste Android/ARM64 e revisão das licenças e formatos.

## Dados locais: pacotes, não treinamento do modelo

Começar por regiões escolhidas por Lucas, em vez de prometer todos os detalhes de todo o país. Um pacote de região deve conter:

- Dados viários e de mapa, índice de endereços e pontos de interesse compatíveis com os motores escolhidos.
- Informações de cidades e atrações com nome, coordenadas quando existentes, categorias, fonte, idioma e data da base.
- Manifesto de versão, cobertura geográfica, tamanho instalado, hashes, licença/atribuição e dependências. Instalação/atualização atômica, validação dos arquivos e espaço livre antes de ativar.
- Recurso para listar regiões disponíveis e mostrar claramente quando um destino está fora da cobertura.

Dados OSM podem fundamentar os pacotes, com atribuição e condições de uso aplicáveis. Não baixar cidades inteiras por raspagem de tile.openstreetmap.org: a [política oficial desse serviço](https://operations.osmfoundation.org/policies/tiles/) proíbe esse uso. Utilizar extratos/pacotes licenciados para offline ou um provedor que o permita. O banco local da Harumi não será uma cópia dos downloads privados do Google Maps ou Waze.

## Exemplo: O que tem de legal para fazer em uma cidade?

1. Identificar a cidade; perguntar qual cidade se houver ambiguidade. Localização atual exige permissão e não deve ser inferida.
2. Consultar o índice local de atrações e a base de referência daquela região.
3. Filtrar resultados por categoria/distância apenas quando houver dados para isso. O LLM resume esses registros e preserva a fonte.
4. Se não houver cobertura, informar a ausência e oferecer pesquisa online. Não completar com lugares inventados pelo modelo.
5. Horários de funcionamento, disponibilidade, preços, obras e trânsito exigem fonte recente. Offline, mostrar que a informação pode estar desatualizada; sem Internet, não afirmar que um estabelecimento está aberto agora.

Para online, escolher um serviço de busca/POIs com cobertura e termos adequados, limitar o que é enviado e armazenar credenciais apenas no cliente nativo/serviço. Abrir um navegador com uma pesquisa e trazer uma resposta fundamentada para dentro da Harumi são integrações diferentes. Nenhuma delas foi apresentada como pronta neste APK.

## Exemplo: Trace uma rota para X

- Caminho externo: escolher app instalado e entregar um endereço/destino por uma interface aceita por ele. [Maps URLs](https://developers.google.com/maps/documentation/urls/get-started) são uma interface documentada do Google; a interface atual usa intents Android e não garante que qualquer app inicie navegação curva a curva.
- Caminho offline: geocodificar X na base local, confirmar o ponto e calcular no grafo baixado. O desenho do mapa sozinho não calcula o trajeto.
- Se faltarem mapa, grafo ou dados do destino, explicar o que falta e oferecer o app externo. Sem inventar duração, trânsito ou distância.

## Critérios antes de chamar isso de pronto

Provar, na central: rota entre dois pontos dentro de uma região baixada sem rede; recálculo; busca de endereços ambíguos; destino fora da cobertura; região ausente; atualização interrompida; GPS sem sinal; convivência com chamadas/rádio/voz; e retorno imediato às câmeras OEM. Para recomendações, testar registros reais, fontes/datas, dados ausentes e ausência de rede. Essas etapas não foram executadas neste trabalho.

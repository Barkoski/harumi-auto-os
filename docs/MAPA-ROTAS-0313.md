# Planejamento de trajetos — 0.3.13-dev.1

## Uso

Navegação → Traçar rota no mapa. Escolha cidade / UF na origem e no destino. Rondonópolis / MT e Londrina / PR vêm preenchidas como exemplo, mas o cálculo só começa ao tocar em Traçar rota. A linha acompanha a geometria real de vias retornada pelo OSRM, não uma linha reta inventada. Há zoom, arrasto, inversão dos pontos e enquadramento do trajeto inteiro.

Comando determinístico por texto ou voz reconhecida: “Harumi, me trace uma rota de Rondonópolis, Mato Grosso para Londrina, no Paraná”. Abre o planejador sem executar o modelo de linguagem. Comando MAP também abre o planejador. Pedido só de destino mantém confirmação nativa e abertura de app externo. Reconhecimento de fala depende da qualidade da transcrição local; teste de microfone físico continua pendente.

## Dados e rede

5.534 centros de cidades correspondidos por nome/UF entre IBGE e GeoNames. Coordenadas são os pontos da localidade na fonte; não são endereços de rua. Municípios sem correspondência exata não recebem coordenadas inventadas. Nomes repetidos precisam da UF. Relatório: data/brazil/city-centers-report.json.

Mapa de ruas: tiles OpenStreetMap visíveis na tela, cache mínimo de sete dias, sem prefetch ou download em massa. Rotas: serviço demonstrativo OSRM, perfil carro, geometria completa, cache local de 24 horas, limite de uma requisição/segundo. Cache antigo só é usado se já existe e houver falha de rede, identificado na tela pela data. Não é uma promessa de mapas offline. Políticas/fontes em TERCEIROS.md.

INTERNET foi adicionada ao manifesto. WebView continua confinada à origem appassets, com carregamentos de rede bloqueados. MapNetworkGateway intercepta somente dois caminhos locais e acessa dois hosts HTTPS fixos; valida coordenadas brasileiras e índices de tiles, limita tamanho/tempo, não segue redirecionamentos e não fornece proxy genérico. Coordenadas e área do mapa vão aos provedores; mensagens, áudio e inferência permanecem locais.

## Validação

45 testes unitários, lint sem erros e assembleDebug aprovados. UI 1024x600, 1024x480, 800x480 e 390x844 com serviço real: Rondonópolis–Londrina, geometria viária, tiles carregados, inversão, cidade inválida e falha de rede sem rota antiga. Atlas anterior e tela inicial continuam aprovados em quatro resoluções.

Android de bancada API30 x86_64 WebView83: rota e tiles reais, comando nativo de duas cidades, modal integralmente dentro da viewport e falha de rota não armazenada sem Internet. Evidências route-android.png, route-android-test.json e road-map-tests.json. Corrigido inset CSS para top/right/bottom/left explícitos, compatíveis com WebView83. Não foi operado o LDPlayer do usuário.

## Limites

Planejamento experimental pessoal, sem SLA do serviço público. Sem trânsito em tempo real, navegação por GPS, instruções por manobra, recálculo automático, alertas viários ou motor nacional offline. Estimativa não inclui paradas; conferir caminho e condições antes da viagem. Não homologado na central física. Nenhuma alteração de firmware, MCU ou HOME.

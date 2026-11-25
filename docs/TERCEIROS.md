# Componentes e fontes

As versões, arquivos e hashes estão em componentes-ia.json. O GGUF foi conferido contra o SHA-256 LFS do repositório de origem.

- Qwen3.5-0.8B: https://huggingface.co/Qwen/Qwen3.5-0.8B (licença Apache-2.0 declarada pelo autor). Quantização: Unsloth, revisão fixada no inventário.
- llama.cpp: MIT; licença preservada em vendor/llama.cpp/LICENSE. Apenas runtime, headers, ggml, CMake e dependências do runtime foram extraídos do commit fixado; UI e ferramentas desktop não fazem parte do build.
- sherpa-onnx 2.0.1 (atual): https://github.com/k2-fsa/sherpa-onnx/tree/v2.0.1. AAR oficial completo, API Java/Kotlin e bibliotecas nativas da mesma versão.
- Supertonic 3 INT8 (atual): https://huggingface.co/Supertone/supertonic-3; detalhes na seção "Atualização de voz em 0.3.1".
- Histórico da 0.3.0 (não fazem parte do APK atual): sherpa-onnx 1.13.8 e os itens Kokoro-82M e eSpeak-NG abaixo.
- [Histórico 0.3.0] Kokoro-82M: https://huggingface.co/hexgrad/Kokoro-82M. Licença e arquivos do pacote ONNX preservados. Voz brasileira feminina pf_dora: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md. Metadado do modelo usado: 42->pf_dora.
- Vosk: https://github.com/alphacep/vosk-api e https://alphacephei.com/vosk/models. Modelo português pequeno 0.3, sem serviço remoto.
- ONNX Runtime, Kotlin stdlib e JNA acompanham dependências nativas/JVM dos respectivos motores. Confira os avisos e licenças upstream antes de redistribuir.
- [Histórico 0.3.0] A versão sherpa-onnx 1.13.8 utilizava eSpeak-NG para fonemização local; ele possui licença própria GPL. Fontes e licença: https://github.com/espeak-ng/espeak-ng. A entrega é de desenvolvimento; não foi feita análise de licenciamento para distribuição comercial.

Não há voz clonada de uma pessoa fornecida pelo usuário, credencial de API, cliente remoto de IA ou cobrança por inferência nesta implementação.

## Atualização de voz em 0.3.1

A voz atual é Supertonic 3 INT8 (https://huggingface.co/Supertone/supertonic-3), executada por sherpa-onnx 2.0.1. O repositório do autor declara licença OpenRAIL para o modelo; o pacote também inclui sua licença e documentação. As referências anteriores a Kokoro e eSpeak-NG descrevem a versão 0.3.0 e não o motor de voz incluído no novo APK. Fontes do motor: https://github.com/k2-fsa/sherpa-onnx/tree/v2.0.1. Pacote: sherpa-onnx-supertonic-3-tts-int8-2026-05-11. F3 foi conferida contra o embedding oficial, índice 2. Sem treinamento ou clonagem da vocalista de referência.


## Mapas 0.3.13

Leaflet 1.9.4, BSD-2-Clause: assets/vendor/leaflet/LICENSE; https://leafletjs.com/. Tiles: © OpenStreetMap contributors, ODbL; https://www.openstreetmap.org/copyright. Uso somente da área exibida, sem prefetch ou download em massa; cache HTTP local mínimo de sete dias; User-Agent próprio. Política: https://operations.osmfoundation.org/policies/tiles/.

Roteamento: servidor demonstrativo OSRM https://router.project-osrm.org, uso pessoal experimental, no máximo uma requisição por segundo, sem SLA ou garantia de atualização. https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server. Configuração comercial/de produção e motor offline ainda pendentes.

Centros das cidades: GeoNames CC BY 4.0, conferência de nomes/UF na base IBGE. Relatório de cobertura data/brazil/city-centers-report.json. Fotos do atlas: créditos e licenças individuais em assets/atlas/atlas-data.json.


## Ícones 0.3.15

Ícones dos aplicativos instalados são fornecidos pelo PackageManager do Android e usados como atalhos de identificação. Imagens de referência dos apps comuns foram obtidas nas páginas oficiais da Play Store, com URLs em assets/icons/sources.json; marcas pertencem aos respectivos titulares. Ícones das funções Harumi são SVGs locais desenhados para esta interface.

## Pendências de licença

Lista de pontos a verificar; não são conclusões jurídicas.

- O texto da licença OpenRAIL-M do Supertonic não está incluído no pacote.
- Fotos do atlas sob CC BY-SA/CC BY exigem atribuição visível ao usuário.
- Quatro fotos (MS, RN, RS, TO) constam apenas com licença "Attribution"; a licença exata precisa ser confirmada.
- Dados OpenStreetMap (ODbL) e Wikivoyage (CC BY-SA 4.0) foram usados na preparação dos dados.
- O servidor OSRM de demonstração não tem SLA e recebe as coordenadas das rotas.
- Ícones de aplicativos de terceiros são marcas dos respectivos titulares.
- Referência visual e de voz "Harumi IA" sem autorização documentada.

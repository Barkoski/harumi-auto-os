# ADR-011: Orange Pi 5 com Ubuntu é a plataforma principal; o app Android fica congelado

Status: Aceita.
Data: 20/11/2026.
Decisor: Lucas.

## Contexto

- O projeto tem duas bases: o app Android (para a central original, ver ADR-001 na especificação HAO-TECH-001) e a camada
  Linux (`linux/`: servidor Python + interface Electron) que roda no Orange Pi 5 (RK3588S, 8 GB, Ubuntu 26.04).
- Desde 16/11/2026 todo o desenvolvimento novo acontece na camada Linux: mapa offline do Brasil instalado na placa, IA local
  (Qwen 3.5 2B via llama.cpp), tela dividida e layout personalizado, temas, módulos do carro, saudação, Waze no lugar do mapa.
- Uma revisão externa (20/11/2026) apontou que as duas bases não são versões equivalentes de um mesmo sistema e que o backend
  RKLLM (NPU) adicionado ao app Android não acelera a versão Linux.

## Decisão

1. **Orange Pi 5 + Ubuntu é a plataforma principal.** Recursos novos, testes e homologação são feitos nela.
2. **O app Android fica congelado:** sem recursos novos; só correção se for reaproveitado. Os arquivos continuam no repositório
   como referência (base do carro, parser de comandos, interface web em `app/src/main/assets`, que a camada Linux reutiliza).
3. **O trabalho RKLLM do Android fica guardado, sem commit e sem compilar.** Antes de qualquer teste ele precisa de:
   o SDK e o modelo RKLLM (não estão no projeto) e a correção do cancelamento — o `epoch` chega ao código nativo e não é
   usado, e `generate` zera o sinal de cancelamento ao começar, então um "Parar" que chegue nesse instante se perde
   (`app/src/main/cpp/rkllm_jni.cpp`, linha 71; `RkllmLanguageModel.java`, linha 30).
4. **A homologação passa a ter uma matriz própria do Orange Pi** (`docs/homologacao/orange-pi.csv`). A matriz antiga
   (`docs/homologacao/testes.csv`, 26 testes `NOT_RUN`) é da central Android e continua valendo só para ela.

## Consequências

- `app/src/main/assets` continua sendo a interface base; a camada Linux injeta seus módulos sem editar esses arquivos.
- A IA da placa é o llama.cpp na CPU (núcleos grandes). A NPU do RK3588 usa no Ubuntu o driver "rocket", que não roda RKLLM;
  acelerar a IA na NPU fica em aberto.
- O diagnóstico SSM1 (somente leitura) segue pendente na placa: falta o cabo, identificar a ECU/ROM do carro e confirmar os
  endereços, hoje marcados como não verificados.
- Rotas offline (atualizado em 20/11/2026): a placa roda o GraphHopper 11.1 local (serviço harumi-routes, núcleos pequenos,
  ~250 MB de RAM) com o grafo do Brasil `grafo-brasil` (perfil de carro padrão). O servidor tenta a rota local primeiro e só
  usa o OSRM online se ela falhar. O grafo `grafo-brasil-v2` não serve no Linux: foi gerado com o perfil de carro próprio do
  app Android (HarumiGraphHopper). Java: pacote openjdk-21-jre-headless do Ubuntu.

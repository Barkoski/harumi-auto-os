# ADR-010: Atuadores externos, luz auxiliar e limites do diagnóstico

Status: Proposta, aguarda dados da central e decisão do Lucas.
Data: 03/11/2026.
Decisor: Lucas.

Convenção deste documento: o que não foi conferido em arquivo do projeto está marcado "(de memória, confirmar na fonte oficial)" ou "(estimativa)". Nada foi pesquisado na internet. Não é parecer jurídico nem projeto de engenharia elétrica.

## Contexto

- A central não tem saídas para acionar luz (a confirmar com o kit e a documentação do fabricante; nada no projeto indica saída de potência).
- A especificação (docs/especificacao/HAO-TECH-001-v0.2.0.txt) registra: ADR-001 Stock Android first (sem root, flash ou firmware); ADR-003 vídeo OEM fora do processo Harumi (câmera de ré e 360° não são capturadas pela UI); ADR-004 core sem autoridade direta (toda ação passa por roteador/allowlist local); ADR-007 diagnóstico Subaru somente leitura (aceita como diretriz, habilitação condicionada à interface e à documentação técnica; linha 1279 do arquivo).
- O ADR-008 já define que o texto produzido pelo LLM não é executado como comando.

## Objetivo

Permitir, no futuro, controle por software de iluminação que não seja de segurança, sem tocar na eletrônica original do carro nem nas funções que a lei e a segurança exigem.

## Proposta

### Módulo externo

- Um módulo separado da central (exemplo: ESP32 com relés, cada saída com fusível dimensionado por quem instalar), ligado à Harumi por Bluetooth ou Wi-Fi local. Protocolo e autenticação do pareamento: a definir.
- Escopo permitido: apenas luz AUXILIAR (ex.: faróis adicionais) ou luz INTERNA (ex.: iluminação de ambiente).
- Escopo proibido por software, sempre: farol, lanterna, freio e seta. Esses circuitos não passam pelo módulo.

### Regras de segurança

1. Interruptor físico que sobrepõe tudo: com ele desligado, nenhuma luz acende, qualquer que seja o comando.
2. Falha segura: relé desligado por padrão; se faltar comunicação, o módulo travar ou cair a energia, as saídas voltam a desligado. Avaliar tempo máximo ligado sem renovação do comando (a definir).
3. Instalação por eletricista automotivo: fiação, fusíveis, relés e bitola são responsabilidade dele. A Harumi não substitui projeto elétrico.
4. Toda ação física exige confirmação do usuário na tela (RiskClass PHYSICAL). Nota: ai/tools ainda não existe no projeto (busca feita em 03/11/2026 não encontrou RiskClass), então o nome vem desta proposta e deve ser alinhado quando ai/tools for criado.
5. O LLM nunca aciona diretamente. No máximo interpreta o pedido; quem executa é o roteador/allowlist (ADR-004), depois da confirmação nativa.
6. Registro de auditoria local: data/hora, comando pedido, origem (toque ou voz), confirmação e resultado.
7. Sem acionamento por mensagem, rede ou notificação externa.

### Normas

- Iluminação adicional em veículos: existem regras do Contran sobre faróis auxiliares e luzes adicionais (de memória, confirmar na fonte oficial). Quais resoluções, condições de uso e se há exigência de homologação não foi verificado. Antes de instalar, Lucas ou o eletricista deve conferir a norma vigente.
- Vídeo em tela visível ao condutor com o veículo em movimento: há restrição em norma do Contran (de memória, confirmar na fonte oficial). Mantém-se a política atual de câmeras e vídeo no OEM (ADR-001/003).

### Diagnóstico SSM1

- Somente leitura. Nunca escrever na ECU, conforme o ADR-007 da especificação (docs/especificacao/HAO-TECH-001-v0.2.0.txt). Habilitação depende da interface e da documentação técnica; o protocolo SSM1 e o conector não foram conferidos neste ADR.
- Sem apagar códigos de falha, sem alterar mapas, sem reprogramar.
- Valores só são exibidos se vierem do adaptador; nunca fabricados (regra já presente no ADR-008).

### Fora de escopo

Câmeras, rádio e visão 360° permanecem do OEM (ADR-001/003). O módulo de luz não interage com esses sistemas.

## Alternativas

- Não fazer: nenhum risco novo, sem luz por software.
- Interruptor físico comum: mais simples e confiável; é a base de comparação para medir o ganho real do controle por software.
- Acionar luzes originais do carro por software: rejeitado, pelas regras acima.

## Consequências

Mais hardware e instalação, com custo de peças e mão de obra (sem estimativa). Nova superfície de risco, por isso a confirmação, a auditoria e o interruptor físico. Qualquer erro de software deve resultar em luz apagada, não acesa.

## Pendências

- Confirmar com o fabricante da central se há GPIO, saída ou barramento acessível. Se não houver, o módulo externo é o caminho.
- Escolher Bluetooth ou Wi-Fi e desenhar pareamento e autenticação.
- Definir com o eletricista o modelo de potência (consumo, fusíveis, relés).
- Conferir as normas do Contran em fonte oficial e decidir se algo exige homologação.
- Criar ai/tools e alinhar o nome RiskClass PHYSICAL.
- Testes de bancada: queda de energia, perda de Bluetooth/Wi-Fi, reinício da central, comando repetido.

# Harumi 0.3.11-dev.1: otimização e proposta de mapas

Nota: documento histórico da 0.3.11; valores atuais em ADR-008-IA-local.md.

38 testes unitários passaram; build e lint sem erros. O mesmo Qwen3.5-0.8B foi mantido. Modelo 0,5B e treinamento próprio não foram implementados ou comparados nesta entrega.

Cumprimentos comuns passam por regras locais, sem LLM. Isso resolve a espera pelo texto da frase Tudo bem? sem alegar que toda a IA ficou instantânea. Perguntas abertas usam instrução e histórico menores, contexto de 1024 tokens, até 64 tokens de saída, até quatro threads e alocações reutilizadas com limpeza completa do estado interno. Orçamento cooperativo de inferência de 20 segundos; carregamento e voz não estão incluídos. Há possibilidade de resposta parcial/erro ao atingir o orçamento. Estado de raciocínio incompleto não é exibido.

Atalhos e confirmação de destino são apresentados antes da síntese de voz terminar. Ao sair para outro app, a fala pode ser cancelada para preservar o app de destino. A saída não é tratada como falha da ação já encaminhada. Personagem segue parada fora da reprodução falada; visual preto/rosa e voz F3 aprovados mantidos.

## Tempos observados no APK final, Android 11/API 30 emulado

- Quick deterministic reply: texto 0.422 s; início da voz 3.906 s.
- Real LLM generation with reused native runtime: texto 11.484 s; início da voz 16.109 s.
- Real LLM generation with reused native runtime: texto 12.235 s; início da voz 16.579 s.
- Route confirmation appears without waiting for synthesis: texto n/a s; início da voz n/a s.

Os valores incluem observação por automação e refletem esta bancada x86_64, não a central ARM ou uma garantia no LDPlayer. A confirmação de rota inclui o tempo de dump da interface Android e não mede sua latência exata. Não foi executada navegação real dentro de um app de mapas. Perguntas abertas diferentes não constituem comparação A/B de velocidade com a versão antiga.

Na 0.3.10, a mesma frase de cumprimento passava pelo LLM e foi observada em 23–30 segundos até o texto. Na versão atual, essa frase usa resposta programada. Foram testadas separadamente duas gerações reais do LLM no mesmo processo para verificar reutilização do contexto, além de voz e animação. A qualidade de conversa do modelo pequeno ainda precisa de avaliação; latência não comprova exatidão factual.

## Mapas e pesquisa

A arquitetura recomendada está em MAPAS-E-IA-LOCAL.md, com fontes oficiais. Mapas locais, motor de rotas próprio, base turística e pesquisa online NÃO foram incluídos neste APK. O seletor de aplicativos externos permanece disponível. Os dados geográficos devem ficar em pacotes separados do modelo, com fonte, cobertura e atualização. Não foi baixada uma base nacional, contratado serviço ou adicionada API remota.

Arquivo APK pronto para atualização. Não foi instalado no LDPlayer que Lucas estava usando: o pedido anterior foi continuar pelo código. Microfone/voz real do host e central física continuam sem homologação. HOME permanece desabilitada; não há diagnóstico físico do Subaru.

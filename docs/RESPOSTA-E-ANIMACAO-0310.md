# Resposta, microfone e animação: 0.3.10-dev.1

Lucas informou que o LDPlayer não reconheceu sua voz nem respondeu ao texto e pediu que a personagem ficasse parada fora da resposta. A instalação identificada por leitura do Android era 0.3.7-dev.1, processo/biblioteca x86_64. O arquivo do Qwen tinha 532.517.120 bytes e o marcador de preparação existia. RECORD_AUDIO estava autorizado; AppOps registrava acesso anterior de aproximadamente 10,9 segundos. Isso comprova presença do modelo/permissão/acesso, não que o áudio do Windows chegou ao reconhecedor ou qual foi a causa da resposta ausente.

Não foi feito teste posterior com voz real no LDPlayer: Lucas pediu para continuar pelo código enquanto utilizava o computador. O LDPlayer não foi atualizado com esta versão. Foi habilitada depuração local para inspeção e reiniciado anteriormente durante o diagnóstico; não foi habilitado root. Nenhum outro programa foi encerrado.

## Alterações

- Personagem inicia parada, sem saudação automática nem loop em espera. Permanece estática ao ouvir/processar. Movimento apenas no estado de reprodução da resposta falada, voltando ao quadro parado depois. Preferência de movimento reduzido e pausa ao sair continuam respeitadas. O antigo parâmetro de prévia animacoes=1 não inicia demonstração automaticamente.
- Autorização inicial do microfone agenda a captura para a retomada da tela, evitando pedir escuta enquanto o controlador está pausado. Verifica retorno de startListening e microfone silenciado pelo Android, com mensagem se falhar.
- Erros de IA/voz deixam estado final e mensagem visíveis, em vez de a conclusão sobrescrever tudo com Pronta. Logs registram a exceção técnica; a pergunta não foi adicionada aos logs.
- Cancelamento manual e interrupção por saída de primeiro plano ficam explícitos. A interface mostra segundos transcorridos durante a operação.
- Voz F3 aprovada, modelo local, comandos e visual preto/rosa preservados. Nenhuma API de IA remota adicionada.

## Verificação

32 testes unitários passaram; build e lint sem erros. Seis verificações no navegador confirmaram quadro parado em espera/escuta/processamento, movimento somente na fala e contador/estado de erro. Layouts da multimídia sem rolagem; celular admite rolagem vertical.

Cinco regressões em Android 11/API 30 de bancada passaram: quadro inicial parado; concessão inicial real de permissão seguida de captura; resposta pelo LLM real à frase digitada no relato; animação durante TTS real; retorno ao quadro parado. O tempo de resposta em texto está no JSON anexo (primeira execução observada nesta rodada ficou em torno de 30 segundos). Não é promessa de latência na central ou no LDPlayer.

A bancada usou outro emulador, em porta separada, sem áudio do host. Captura iniciada não equivale a validação da voz real/microfone do Windows. O motivo específico da falha antiga no LDPlayer não foi reproduzido/concluído. A lentidão, interrupções e mensagens agora são mais observáveis; testar entrada de áudio do LDPlayer continua necessário.

## Uso

Atualize o APK no LDPlayer preservando os dados. Teste primeiro por texto e aguarde o contador; use Parar se quiser interromper. A autorização do Android não seleciona automaticamente um microfone físico do Windows. Na próxima sessão de teste na janela, conferir a entrada selecionada em Áudio do LDPlayer e a captura efetiva. A Harumi continua sem diagnóstico físico do Subaru; HOME desabilitada.

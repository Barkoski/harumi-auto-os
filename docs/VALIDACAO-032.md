# Harumi Auto OS 0.3.2-dev.1 — voz aprovada

Atualização solicitada por Lucas após aprovar a amostra Harumi-F3-entusiasmo.mp3.

Voz Supertonic 3 F3, speaker 2; idioma pt; 24 passos; velocidade 1.25; silêncio 0.72. Parâmetros centralizados em VoiceProfile.java e iguais aos da amostra aprovada. Pronúncia Harumi → Rarumi apenas ao sintetizar. Grafia Harumi preservada.

A apresentação usa a mesma frase aprovada: “Oi, Lucas! Eu sou a Harumi! Quer que eu abra o mapa? Me diz: pra onde a gente vai hoje?”. Saudações simples usam essa resposta local. Conversa com o modelo continua disponível. O prompt pede entusiasmo moderado em saudações e sobriedade em diagnóstico/alertas.

## Verificado em 02/11/2026

- Build debug arm64-v8a e x86_64 concluído.
- 16 testes unitários sem falha, incluindo perfil da amostra, pronúncia e saudações.
- Lint sem erros; avisos da configuração Android/WebView/dependências registrados no projeto.
- Instalação em Android 11/API 30 emulado e teste integrado com Wi-Fi e dados desligados: OK (1 test).
- Modelo local gerou resposta, F3 sintetizou áudio e Vosk reconheceu: “abra o mapa para encontrar o meu destino”, convertida em ação MAP permitida.
- Perfil confirmado no teste Android: velocidade 1.25, silêncio 0.7200000286102295, nome enviado à síntese Rarumi.

O teste emulado não homologa a multimídia física. Diagnóstico do Subaru continua sem adaptador e HOME desabilitada. Não houve alteração de firmware.

O APK mantém applicationId, assinatura debug e pasta de modelos da versão 0.3.1, permitindo atualização sem nova alteração dos arquivos dos modelos. Instalação em central real continua pendente.

Houve uma execução anterior em que a transcrição da fala sintética acelerada não foi classificada como MAP. A reexecução com evidência ampliada passou; não foi comprovada uma correção da variabilidade do ASR. A precisão no microfone real e no ruído da cabine segue pendente.


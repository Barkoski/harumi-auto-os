# 0.3.12: mapa do Brasil

Frontend-design aplicado, preservando botões grandes e identidade preta/rosa aprovada. Atlas local com limites oficiais IBGE, 26 estados + DF, seleção persistida, fotos das 27 capitais e créditos individuais. Navegação abre o atlas; botão Maps/Waze mantém o seletor de apps; destino da capital passa pela confirmação nativa existente. Cancelamento silencioso evita reabrir a conversa ao sair.

Verificação: 41 testes unitários sem falhas, lint e assembleDebug aprovados; quatro resoluções, 27 fotos e escolha/fechamento/encaminhamento testados. Android de bancada API30 x86_64 WebView83 com rede desligada: atlas, foto, confirmação Rio de Janeiro e fechamento silencioso aprovados. Nenhuma alteração no LDPlayer do usuário nesta retomada. Ajuste final de altura das fotos verificado no navegador e incluído na compilação final.

Voz: cache PCM de respostas fixas mantém perfil feminino aprovado. Benchmark docs/evidencias/latency-0312-results.json. Não representa velocidade geral do modelo. Modelo não foi treinado com os mapas.

Base nacional separada em outputs/Harumi - Base Brasil: SQLite 2.941.317.120 bytes, PBF bruto 2.101.692.313 bytes, manifestos e limites no LEIA-ME. Não é motor pronto de rotas nem integração RAG concluída. Fotos/limites do atlas estão no APK; banco grande não está.

APK de bancada assinado debug e SHA256 em outputs/Harumi Auto OS 0.3.12 - mapa Brasil. Não homologado na central física. Firmware/MCU/HOME preservados.

# Harumi Compat: roteiro para a central (Aikon Fóton G3)

O app **Harumi Compat** só lê informações da central (tela, câmeras, apps instalados, áudio etc.) e gera um relatório. Ele **não altera nada** na central, não usa internet, não lê contatos, contas nem números de telefone. Pode ser desinstalado depois.

## Passo a passo

1. **No computador:** copie o arquivo `compatibility-debug.apk` para o pendrive (pode ficar na raiz).
2. **Na central:** espetar o pendrive na entrada USB.
3. Abra o **gerenciador de arquivos** da central, entre no pendrive e toque no arquivo `compatibility-debug.apk`.
4. Se aparecer aviso de **"fontes desconhecidas"** ou "instalação bloqueada": toque em **Configurações** e ative **Permitir desta fonte** para o gerenciador de arquivos. Volte e toque no APK de novo.
5. Toque em **Instalar**. Se aparecer aviso de segurança do tipo "app não verificado", escolha **Instalar mesmo assim**.
6. Abra o app **Harumi Compat** (ícone "Harumi Compatibilidade"). O relatório aparece na tela sozinho.
7. Toque em um dos botões grandes:
   - **Compartilhar:** abre a lista de apps para enviar o texto do relatório (e-mail, WhatsApp etc.), se a central tiver algum.
   - **Salvar relatório:** grava o arquivo `Harumi-central.json`. Escolha o **pendrive** como destino.
8. **Envie o arquivo** `Harumi-central.json` (ou o texto compartilhado) para mim. Se a central não tiver como enviar, leve o pendrive ao computador e envie de lá.

## Se der problema

- Se **Compartilhar** não abrir nada, use **Salvar relatório**.
- Se não aparecer onde salvar, tire uma foto da tela e envie.
- Se a instalação for bloqueada, anote a mensagem que aparece.

## Depois

Para remover: Configurações > Apps > **Harumi Compatibilidade** > Desinstalar. Isso não afeta mais nada na central.

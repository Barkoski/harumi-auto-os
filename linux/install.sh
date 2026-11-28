#!/bin/sh
# Instala a Harumi como servicos do usuario (systemd --user) no Orange Pi.
# Uso (como o usuario da sessao grafica, ex. orangepi):  sh ~/harumi/install.sh
set -eu
umask 022  # os arquivos de servico sairam graváveis por qualquer usuario (20/11/2026)
H="$HOME/harumi"
U="$HOME/.config/systemd/user"
A="$HOME/.config/autostart"
mkdir -p "$U" "$A" "$HOME/.local/share/harumi/mapas"
chmod +x "$H/spotify_event.py" 2>/dev/null || true

cat > "$U/harumi-server.service" <<EOF
[Unit]
Description=Harumi Auto OS - servidor local da interface
After=network-online.target

[Service]
WorkingDirectory=$H
ExecStart=/usr/bin/python3 $H/harumi_server.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

# Moldura: Electron (apps embutidos dentro da Harumi) quando instalado em ~/harumi/electron; senao Chromium em quiosque.
if [ -x "$H/electron/electron" ] && [ -f "$H/shell/main.js" ]; then
  KIOSK_CMD="$H/electron/electron $H/shell --ozone-platform=wayland"
else
  KIOSK_CMD="/usr/bin/chromium --kiosk --app=http://127.0.0.1:8765/assets/index.html --ozone-platform=wayland --user-data-dir=$HOME/.config/harumi-chromium --no-first-run --noerrdialogs --disable-session-crashed-bubble --disable-translate --autoplay-policy=no-user-gesture-required --password-store=basic"
  # Porta de depuracao (cdp.py) so na bancada: HARUMI_DEBUG=1 ./install.sh
  if [ "${HARUMI_DEBUG:-0}" = "1" ]; then KIOSK_CMD="$KIOSK_CMD --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222"; fi
fi

cat > "$U/harumi-kiosk.service" <<EOF
[Unit]
Description=Harumi Auto OS - interface em tela cheia
After=harumi-server.service graphical-session.target
Requires=harumi-server.service
PartOf=graphical-session.target

[Service]
ExecStartPre=/bin/sh -c 'for i in \$(seq 1 50); do /usr/bin/curl -sf -o /dev/null http://127.0.0.1:8765/assets/index.html && exit 0; sleep 0.2; done; exit 1'
ExecStart=$KIOSK_CMD
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
EOF

# Spotify Connect (librespot). Requer login unico: sh ~/harumi/bin/spotify-login.sh (grava a credencial no cache).
if [ -x "$H/bin/librespot" ]; then
cat > "$U/harumi-spotify.service" <<EOF
[Unit]
Description=Harumi Auto OS - Spotify Connect (librespot)
After=network-online.target sound.target

[Service]
ExecStart=$H/bin/librespot --name Harumi --device-type automobile --backend pulseaudio --bitrate 320 --cache $HOME/.cache/harumi/spotify --initial-volume 60 --onevent $H/spotify_event.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
fi

# IA local (llama.cpp + Qwen3.5 2B) nos 4 nucleos grandes (A76). Modelo e binarios em ~/harumi/llm.
LLM_BIN="$H/llm/llama.cpp/build/bin/llama-server"
LLM_MODEL="$H/llm/models/Qwen3.5-2B-Q4_0.gguf"
if [ -x "$LLM_BIN" ] && [ -s "$LLM_MODEL" ]; then
cat > "$U/harumi-llm.service" <<EOF
[Unit]
Description=Harumi Auto OS - IA local (llama-server, Qwen3.5 2B)

[Service]
# Partida em dia quente: espera a placa ficar abaixo de 70 C (no maximo 10 min); mapa e musica ja funcionam enquanto isso.
ExecStartPre=/bin/sh -c 'for i in \$(seq 1 120); do t=\$(cat /sys/class/thermal/thermal_zone0/temp); [ "\$t" -lt 70000 ] && exit 0; sleep 5; done; exit 0'
TimeoutStartSec=11min
ExecStart=/usr/bin/taskset -c 4-7 $LLM_BIN -m $LLM_MODEL -t 4 -c 4096 --host 127.0.0.1 --port 8090 --no-webui
Restart=on-failure
RestartSec=5
Nice=5

[Install]
WantedBy=default.target
EOF
fi

# Rota offline (GraphHopper 11.1 + grafo do Brasil) nos 4 nucleos pequenos (A55), longe da IA. Copiar antes para
# ~/.local/share/harumi/rotas: graphhopper-web-11.1.jar e grafo-brasil/ (gerados no PC, ver docs/ADR-011).
GH_DIR="$HOME/.local/share/harumi/rotas"
if command -v java >/dev/null && [ -s "$GH_DIR/graphhopper-web-11.1.jar" ] && [ -d "$GH_DIR/grafo-brasil" ]; then
cat > "$U/harumi-routes.service" <<EOF
[Unit]
Description=Harumi Auto OS - rota offline (GraphHopper local)

[Service]
WorkingDirectory=$GH_DIR
ExecStart=/usr/bin/taskset -c 0-3 /usr/bin/java -Xms128m -Xmx768m -jar $GH_DIR/graphhopper-web-11.1.jar server $H/rotas/gh-config.yml
Restart=on-failure
RestartSec=10
Nice=10

[Install]
WantedBy=default.target
EOF
fi

systemctl --user daemon-reload
[ -f "$U/harumi-llm.service" ] && systemctl --user enable --now harumi-llm.service
[ -f "$U/harumi-routes.service" ] && systemctl --user enable --now harumi-routes.service
systemctl --user enable harumi-server.service harumi-kiosk.service
[ -f "$U/harumi-spotify.service" ] && systemctl --user enable --now harumi-spotify.service
systemctl --user restart harumi-server.service
systemctl --user restart harumi-kiosk.service || true
[ -f "$H/root/install-root.sh" ] && echo "Falta a parte de root (governador termico): sudo sh $H/root/install-root.sh"
echo "Harumi instalada. Servidor: http://127.0.0.1:8765/assets/index.html"

#!/bin/sh
# Login unico do librespot (OAuth). Grava a credencial em ~/.cache/harumi/spotify.
mkdir -p "$HOME/.cache/harumi/spotify"
exec "$HOME/harumi/bin/librespot" --name Harumi --device-type automobile --backend alsa \
  --device plughw:CARD=rockchipes8388,DEV=0 --bitrate 320 --cache "$HOME/.cache/harumi/spotify" \
  --enable-oauth --oauth-port 5588

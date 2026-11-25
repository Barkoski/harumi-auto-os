#!/bin/sh
# Baixa os icones oficiais dos apps web para ~/harumi/app-icons (uso pessoal na Harumi do carro).
# Os icones sao marcas de cada empresa: ficam so no aparelho e NAO entram no repositorio.
set -eu
D="$HOME/harumi/app-icons"
mkdir -p "$D"
UA="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
get() { # id url
  tmp="$D/$1.tmp"
  if curl -fsSL -A "$UA" --max-filesize 200000 -o "$tmp" "$2"; then
    case "$2" in *.ico) ext=ico ;; *.svg) ext=svg ;; *) ext=png ;; esac
    rm -f "$D/$1".png "$D/$1".ico "$D/$1".svg
    mv "$tmp" "$D/$1.$ext"
    echo "$1.$ext $(wc -c < "$D/$1.$ext") bytes"
  else
    rm -f "$tmp"; echo "$1: falhou ($2)"
  fi
}
get claude  https://claude.ai/apple-touch-icon.png
get chatgpt https://chatgpt.com/cdn/assets/favicon-180x180.9e0103ce69.png
get waze    https://www.waze.com/apple-touch-icon.png
get spotify https://open.spotify.com/favicon.ico
get youtube https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png
get browser https://www.google.com/images/branding/googleg/1x/googleg_standard_color_128dp.png

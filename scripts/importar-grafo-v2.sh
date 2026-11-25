#!/usr/bin/env bash
# Gera o grafo de rotas do Brasil com o peso proprio (sem Janino). Roda no PC (Git Bash), uns 16 min, -Xmx8g.
# Uso: bash scripts/importar-grafo-v2.sh  (variaveis: HM=D:/HarumiMapa)
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; HM="${HM:-D:/HarumiMapa}"
JD="$(ls -d "$HM"/ferramentas/jdk21/*/ | head -1)"; JARW="$HM/ferramentas/graphhopper-web-11.1.jar"
OUT="$HM/saida/classes-import"; mkdir -p "$OUT"
"$JD/bin/javac.exe" --release 17 -nowarn -cp "$JARW" -d "$OUT" "$HERE/app/src/main/java/com/harumi/autoos/navigation/gh/HarumiGraphHopper.java" "$HERE/scripts/graphhopper-android/HarumiImport.java"
"$JD/bin/java.exe" -Xmx8g -cp "$JARW;$OUT" HarumiImport "$HM/baixados/brazil-latest.osm.pbf" "$HM/saida/grafo-brasil-v2"

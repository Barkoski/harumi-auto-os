#!/usr/bin/env bash
# Gera app/libs/graphhopper-core-11.1-android.jar: o graphhopper-core 11.1 original (Maven Central) com
# com/graphhopper/storage/MMapDataAccess*.class trocada pela versao ajustada em scripts/graphhopper-android/
# (sem ByteBuffer.get/put absoluto em bloco, que e Java 13 e nao existe no Android 14).
# Uso: bash scripts/build-graphhopper-android.sh [caminho-do-JDK17]   (precisa de javac, jar, curl, unzip)
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
JDK="${1:-${JAVA_HOME:-}}"; JAVAC="${JDK:+$JDK/bin/}javac"; JAR="${JDK:+$JDK/bin/}jar"
V=11.1; M=https://repo1.maven.org/maven2
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
curl -fsSL -o "$W/core.jar" "$M/com/graphhopper/graphhopper-core/$V/graphhopper-core-$V.jar"
curl -fsSL -o "$W/slf4j.jar" "$M/org/slf4j/slf4j-api/2.0.17/slf4j-api-2.0.17.jar"
curl -fsSL -o "$W/webapi.jar" "$M/com/graphhopper/graphhopper-web-api/$V/graphhopper-web-api-$V.jar"
curl -fsSL -o "$W/hppc.jar" "$M/com/carrotsearch/hppc/0.8.1/hppc-0.8.1.jar"
mkdir "$W/x" "$W/out"; (cd "$W/x" && unzip -q ../core.jar)
rm -f "$W/x"/com/graphhopper/storage/MMapDataAccess*.class
P() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi; }  # Git Bash: javac.exe precisa de caminhos do Windows
SEP=":"; command -v cygpath >/dev/null 2>&1 && SEP=";"
"$JAVAC" --release 17 -nowarn -cp "$(P "$W/core.jar")$SEP$(P "$W/slf4j.jar")$SEP$(P "$W/hppc.jar")$SEP$(P "$W/webapi.jar")" -d "$(P "$W/x")" "$(P "$HERE/scripts/graphhopper-android/com/graphhopper/storage/MMapDataAccess.java")"
mkdir -p "$HERE/app/libs"
(cd "$W/x" && "$JAR" cf "$(P "$W/patched.jar")" .)
cp "$W/patched.jar" "$HERE/app/libs/graphhopper-core-$V-android.jar"
echo "OK: app/libs/graphhopper-core-$V-android.jar"

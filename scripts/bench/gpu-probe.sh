#!/usr/bin/env bash
# Sonda de capacidade grafica (WebGL2 + FPS) da WebView da Harumi, via adb/DevTools. Nao altera dados do aparelho.
# Requer o app com diag-gpu.html instalado. Uso: bash scripts/bench/gpu-probe.sh [serial-adb]  (padrao: emulator-5554)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ADB="${ADB:-$HERE/../../../work/android-toolchain/android-sdk/platform-tools/adb.exe}"
SERIAL="${1:-emulator-5554}"; A=("$ADB" -s "$SERIAL"); PKG=com.harumi.autoos
OUT="$HERE/resultados/gpu-$(date +%Y%m%d-%H%M).json"; mkdir -p "$HERE/resultados"
forward(){ local pid; pid=$(timeout 10 "${A[@]}" shell pidof $PKG | tr -d '\r'); "$ADB" forward --remove-all >/dev/null 2>&1; "${A[@]}" forward tcp:9222 localabstract:webview_devtools_remote_$pid >/dev/null; }
ev(){ timeout 40 node "$HERE/cdp-eval.js" -e "$1" 2>/dev/null; }

timeout 60 "${A[@]}" shell am start -n $PKG/.MainActivity >/dev/null; sleep 3
forward
timeout 20 node "$HERE/cdp-navigate.js" diag-gpu.html >/dev/null  # Page.navigate: o app bloqueia location.href (shouldOverrideUrlLoading)
RES=""
for i in $(seq 1 20); do
  sleep 2; forward
  RES=$(ev "typeof window.harumiGpuProbe==='undefined' ? 'AGUARDANDO' : window.harumiGpuProbe")
  case "$RES" in ""|*AGUARDANDO*|ERRO*) RES="";; *) break;; esac
done
[ -n "$RES" ] && { echo "$RES" | tee "$OUT"; echo "Resultado salvo em $OUT"; } || echo "Falha: sonda nao respondeu (o APK tem diag-gpu.html?)"
forward; timeout 20 node "$HERE/cdp-navigate.js" index.html >/dev/null

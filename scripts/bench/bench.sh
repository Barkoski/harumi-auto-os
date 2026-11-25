#!/usr/bin/env bash
# Benchmark da Harumi num Android via adb (LDPlayer ou central). Somente leitura do aparelho: nao instala nem apaga nada.
# Uso: bash scripts/bench/bench.sh [serial-adb]   (padrao: emulator-5554). Resultado em scripts/bench/resultados/.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ADB="${ADB:-$HERE/../../../work/android-toolchain/android-sdk/platform-tools/adb.exe}"
SERIAL="${1:-emulator-5554}"; A=("$ADB" -s "$SERIAL"); PKG=com.harumi.autoos
OUT="$HERE/resultados/bench-$(date +%Y%m%d-%H%M).txt"; mkdir -p "$HERE/resultados"
log(){ echo "$*" | tee -a "$OUT"; }
forward(){ local pid; pid=$(timeout 10 "${A[@]}" shell pidof $PKG | tr -d '\r'); "$ADB" forward --remove-all >/dev/null 2>&1; "${A[@]}" forward tcp:9222 localabstract:webview_devtools_remote_$pid >/dev/null; }
ready(){ for i in $(seq 1 120); do r=$(timeout 10 node "$HERE/cdp-eval.js" -e "!!document.getElementById('assistant-status')&&/^Pronta/.test(document.getElementById('assistant-status').textContent)" 2>/dev/null); [ "$r" = "true" ] && return 0; sleep 0.5; done; return 1; }

log "== Harumi bench $(date '+%d/%m/%Y %H:%M') · aparelho $SERIAL"
log "Aparelho: $(timeout 10 "${A[@]}" shell getprop ro.product.model | tr -d '\r') · Android $(timeout 10 "${A[@]}" shell getprop ro.build.version.release | tr -d '\r') · ABI $(timeout 10 "${A[@]}" shell getprop ro.product.cpu.abi | tr -d '\r') · núcleos $(timeout 10 "${A[@]}" shell nproc | tr -d '\r')"
log "Versão: $(timeout 10 "${A[@]}" shell dumpsys package $PKG | grep -m1 versionName | tr -d '\r ')"

log ""; log "-- Abertura a frio (3x): tela nativa (Android) e interface pronta (WebView + status)"
for n in 1 2 3; do
  timeout 20 "${A[@]}" shell am force-stop $PKG; sleep 2
  t0=$(date +%s%3N); tot=$(timeout 60 "${A[@]}" shell am start -W -n $PKG/.MainActivity | grep TotalTime | tr -dc '0-9'); forward
  ready && t1=$(date +%s%3N) || t1=0
  log "  rodada $n: Android ${tot} ms · interface pronta $(( t1>0 ? t1-t0 : -1 )) ms"
done

log ""; log "-- Abrir app pela Harumi (Chrome) e Configurações de Wi-Fi: tempo medido pelo Android (Displayed)"
for act in "catalog.open chrome com.android.chrome" "connection.wifi - com.android.settings"; do
  set -- $act; timeout 10 "${A[@]}" logcat -c
  t0=$(date +%s%3N); timeout 10 node "$HERE/cdp-eval.js" -e "HarumiNative.dispatch('$1','$2');1" >/dev/null
  for i in $(seq 1 100); do top=$(timeout 10 "${A[@]}" shell dumpsys activity activities | grep -m1 topResumedActivity); echo "$top" | grep -q "$3" && break; sleep 0.1; done; t1=$(date +%s%3N)
  disp=$(timeout 10 "${A[@]}" logcat -d | grep -m1 "Displayed $3" | grep -o '+[0-9a-z]*' | head -1)
  log "  $1 $2: em primeiro plano em ~$((t1-t0)) ms (medido pelo PC, inclui adb) · Android: ${disp:-sem registro}"
  timeout 10 "${A[@]}" shell am start -n $PKG/.MainActivity >/dev/null; sleep 3
done
forward

log ""; log "-- Conversa, IA, voz, Oi Harumi e painéis (pela interface)"
timeout 1500 node "$HERE/cdp-eval.js" "$HERE/page-bench.js" | tee -a "$OUT"

log ""; log "-- Memória do app (com modelos carregados)"
timeout 20 "${A[@]}" shell dumpsys meminfo $PKG | grep -E "TOTAL PSS|TOTAL RSS|Native Heap" | head -3 | tee -a "$OUT"
log ""; log "Resultado salvo em $OUT"

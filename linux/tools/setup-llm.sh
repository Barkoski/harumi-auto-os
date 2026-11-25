#!/bin/sh
# Baixa e compila o llama.cpp e baixa os modelos de teste no Orange Pi (rodar como o usuario orangepi).
# Log em ~/harumi/llm/setup.log; ao terminar grava ~/harumi/llm/SETUP_OK.
# Cuidados depois do reinicio de 16/11: download com limite de velocidade, compilacao com 4 tarefas
# e sync depois de cada etapa (o que estava so na memoria se perdeu na queda).
set -eu
L="$HOME/harumi/llm"
mkdir -p "$L/models"
cd "$L"
rm -f "$L/SETUP_OK"
exec >"$L/setup.log" 2>&1
echo "inicio $(date)"

TAG=v1.0.0
B="$L/llama.cpp/build/bin"
if [ ! -s "$B/llama-server" ] || [ ! -s "$B/llama-bench" ]; then
  if [ ! -f "$L/llama.cpp/CMakeLists.txt" ]; then
    curl -fL --retry 3 --limit-rate 10M -o llama.tar.gz "https://github.com/ggml-org/llama.cpp/archive/refs/tags/$TAG.tar.gz"
    rm -rf llama.cpp && mkdir llama.cpp && tar xzf llama.tar.gz -C llama.cpp --strip-components=1 && rm llama.tar.gz
  fi
  [ -d "$B" ] && find "$B" -maxdepth 1 -type f -size 0 -delete
  find "$L/llama.cpp/build" -name '*.o' -size 0 -delete 2>/dev/null || true
  cmake -S llama.cpp -B llama.cpp/build -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF
  cmake --build llama.cpp/build -j4 --target llama-bench llama-cli llama-server
  sync
fi
ls -la "$B" | grep -v '\.so'

for f in "Qwen3.5-2B-GGUF/Qwen3.5-2B-Q4_0.gguf" "Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_0.gguf"; do
  out="models/$(basename "$f")"
  if [ ! -s "$out" ]; then
    curl -fL --retry 3 --limit-rate 15M -C - -o "$out.part" "https://huggingface.co/unsloth/$(dirname "$f")/resolve/main/$(basename "$f")"
    mv "$out.part" "$out"
    sync
  fi
  ls -la "$out"
done
echo "fim $(date)"
touch "$L/SETUP_OK"
sync

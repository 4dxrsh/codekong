#!/usr/bin/env bash
# Entrypoint for the full CodeKong container: bring up the local Ollama server,
# make sure the model is present, then serve the web app. Live generation in
# the UI talks to this in-container Ollama at http://localhost:11434 (matches
# config.yaml llm.local_host), so no external services are needed.
set -e

echo "[codekong] starting Ollama server..."
ollama serve >/tmp/ollama.log 2>&1 &

# Wait for Ollama to accept requests.
for i in $(seq 1 60); do
  if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[codekong] Ollama is ready."
    break
  fi
  sleep 1
done

# The model is baked in at build time; pull as a fallback if it is missing
# (e.g. if the image was built without the bake step).
if ! ollama list 2>/dev/null | grep -q "qwen2.5-coder:7b"; then
  echo "[codekong] model not found in image, pulling qwen2.5-coder:7b..."
  ollama pull qwen2.5-coder:7b || echo "[codekong] WARNING: model pull failed; live generation will not work."
fi

echo "[codekong] starting web app on http://0.0.0.0:${PORT:-5001}"
exec python -m frontend.app

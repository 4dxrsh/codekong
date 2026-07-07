#!/usr/bin/env bash
# CodeKong Phase 0 bootstrap — run from the repo root.
#   Linux target : WSL2 Ubuntu (see README "Setting up WSL2 from zero")
#   macOS target : Apple Silicon or Intel, needs Homebrew (https://brew.sh)
# Idempotent: safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"

OS="$(uname -s)"

echo "== 0. Environment sanity =="
if [ "$OS" = "Darwin" ]; then
  echo "macOS detected: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -m)"
  echo "RAM: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 )) GB unified memory"
  if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew is required on macOS. Install it first:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
  fi
else
  if uname -r | grep -qi microsoft && [[ "$(pwd)" == /mnt/?/* ]]; then
    echo "ERROR: you are running from the Windows drive mount ($(pwd))."
    echo "This corrupts mutation results (stale-metadata bytecode caching)."
    echo "Copy the project to your Linux home and run it there:"
    echo "    cp -r $(pwd) ~/codekong"
    echo "    cd ~/codekong"
    echo "    rm -rf venv subjects module1_mutation/_scratch"
    echo "    bash setup.sh"
    exit 1
  fi
  if ! uname -r | grep -qi microsoft; then
    echo "WARNING: this does not look like WSL2 (uname -r: $(uname -r))."
    echo "mutmut needs fork(); any real Linux works, but WSL2 is the documented target."
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total --format=csv || true
  else
    echo "nvidia-smi not found. If this laptop has the RTX 3050 Ti, update the"
    echo "NVIDIA driver on the WINDOWS host (WSL2 uses it directly; there is no"
    echo "separate Linux driver). Continuing on CPU is possible but slow."
  fi
fi

echo "== 1. Python venv + dependencies =="
if [ "$OS" = "Darwin" ]; then
  command -v git >/dev/null 2>&1 || brew install git
  # Use a Homebrew Python (Apple's system python3 is often outdated/locked).
  if ! command -v python3.11 >/dev/null 2>&1 && ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    brew install python@3.11
  fi
  PY=$(command -v python3.11 || command -v python3)
else
  sudo apt-get update -y
  sudo apt-get install -y python3-venv python3-pip git curl
  PY=python3
fi
[ -d venv ] || "$PY" -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip freeze > requirements.lock.txt
echo "Exact tested versions frozen to requirements.lock.txt — commit it."

echo "== 2. Ollama (local, free, no API key) =="
if ! command -v ollama >/dev/null 2>&1; then
  if [ "$OS" = "Darwin" ]; then
    brew install ollama
  else
    curl -fsSL https://ollama.com/install.sh | sh
  fi
fi
# Start the server if it isn't running. (macOS alternative: `brew services
# start ollama`, or just launch the Ollama app if you installed the .dmg.)
if ! curl -s http://localhost:11434 >/dev/null 2>&1; then
  nohup ollama serve >/tmp/ollama.log 2>&1 &
  sleep 3
fi

MODEL=$(venv/bin/python -m core.hardware | venv/bin/python -c \
  "import sys,json; print(json.load(sys.stdin)['recommended_model'])")
CONFIG_MODEL=$(venv/bin/python -c \
  "from core.config import load_config; print(load_config()['llm']['model'])")
echo "Hardware probe recommends: $MODEL — config.yaml says: $CONFIG_MODEL (config wins)"
if [ "$MODEL" != "$CONFIG_MODEL" ]; then
  echo "NOTE: if this machine can handle $MODEL, edit llm.model in config.yaml."
fi
ollama pull "$CONFIG_MODEL"
echo "-- verification call (watch the speed: fast = GPU/Metal in use, crawling = CPU"
echo "   or partial offload; the latter is EXPECTED on a 4GB RTX 3050 Ti) --"
ollama run "$CONFIG_MODEL" "write a one-line python function"

echo "== 3. Subject repos (cloned + pinned) =="
mkdir -p subjects
clone_pin () {  # url, path, config_key
  local url=$1 path=$2 key=$3
  if [ ! -d "$path/.git" ]; then
    git clone --depth 50 "$url" "$path"
  fi
  local pinned
  pinned=$(venv/bin/python - "$key" <<'EOF'
import sys, yaml
cfg = yaml.safe_load(open("config.yaml"))
print(cfg["subjects"][sys.argv[1]].get("pin_commit") or "")
EOF
)
  if [ -n "$pinned" ]; then
    git -C "$path" checkout --quiet "$pinned"
    echo "$key pinned to existing $pinned"
  else
    local sha
    sha=$(git -C "$path" rev-parse HEAD)
    venv/bin/python - "$key" "$sha" <<'EOF'
# Comment-preserving pin write: edits only the pin_commit line inside the
# subject's block (yaml.safe_dump would strip every comment in config.yaml).
import re, sys
key, sha = sys.argv[1], sys.argv[2]
text = open("config.yaml", encoding="utf-8").read()
pattern = rf'(^  {re.escape(key)}:\n(?:^    .*\n)*?^    pin_commit: )""'
new, n = re.subn(pattern, rf'\g<1>"{sha}"', text, count=1, flags=re.MULTILINE)
if n != 1:
    sys.exit(f"could not locate pin_commit for {key} in config.yaml")
open("config.yaml", "w", encoding="utf-8").write(new)
print(f"{key} newly pinned to {sha} — COMMIT config.yaml so results stay reproducible")
EOF
  fi
}
clone_pin https://github.com/TheAlgorithms/Python subjects/algorithms_python sorts
clone_pin https://github.com/dbader/schedule      subjects/schedule          schedule

echo "== 4. Smoke check =="
venv/bin/python -m core.hardware
venv/bin/python -c "from core.config import load_config; load_config(); print('config OK')"
echo "Setup complete. Next: venv/bin/python run_pipeline.py --repo sorts --limit 5 --skip-semantic"

"""Probe GPU VRAM / system RAM and recommend an Ollama model tier.

Run standalone:  python -m core.hardware

The recommendation is advisory; config.yaml stays authoritative. On the
project's target laptop (RTX 3050 Ti — the laptop variant ships fixed at 4GB
VRAM regardless of vendor), 4GB is below the ~5-6GB a 7B model needs fully
in VRAM at Q4 with context headroom, so Ollama partially offloads to system
RAM and runs slower than the tier table implies. Expected, not broken.

On Apple Silicon Macs there is no separate VRAM: Ollama uses Metal over
unified memory, so total system RAM is the budget (probed via sysctl).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys


def gpu_vram_mb() -> int | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode != 0:
            return None
        vals = [int(v.strip()) for v in out.stdout.splitlines() if v.strip().isdigit()]
        return max(vals) if vals else None
    except Exception:
        return None


def system_ram_mb() -> int | None:
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                 capture_output=True, text=True, timeout=10)
            return int(out.stdout.strip()) // (1024 * 1024)
        except Exception:
            return None
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            m = re.search(r"MemTotal:\s+(\d+)\s+kB", fh.read())
        return int(m.group(1)) // 1024 if m else None
    except OSError:
        return None


def _is_apple_silicon() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        out = subprocess.run(["uname", "-m"], capture_output=True, text=True,
                             timeout=10)
        return out.stdout.strip() == "arm64"
    except Exception:
        return False


def recommend_model() -> dict:
    vram = gpu_vram_mb()
    ram = system_ram_mb()
    apple = _is_apple_silicon()
    # Apple Silicon: unified memory IS the GPU budget, but the OS and apps
    # need a share — count roughly 2/3 of RAM as usable for the model.
    budget = vram if vram else (int(ram * 2 / 3) if (apple and ram) else ram)
    if budget is None:
        tier, note = "qwen2.5-coder:7b", "Could not probe memory; defaulting to smallest tier."
    elif budget >= 24_000:
        tier, note = "qwen2.5-coder:32b", "24GB+: 32b dense, or qwen3-coder:30b (MoE, fits 24GB)."
    elif budget >= 12_000:
        tier, note = "qwen2.5-coder:14b", "12-16GB: 14b, or deepseek-coder-v2:16b-lite-instruct."
    else:
        tier, note = "qwen2.5-coder:7b", "<=8GB budget: 7b tier."
        if vram is not None and vram < 6_000:
            note += (
                f" GPU has {vram}MB VRAM (< ~5-6GB a Q4 7B needs with context): "
                "expect partial offload to system RAM and slow batch runs. "
                "Normal on a laptop RTX 3050 Ti."
            )
    if apple:
        note += (f" Apple Silicon detected ({ram}MB unified memory): Ollama "
                 "uses Metal acceleration; no NVIDIA driver or nvidia-smi "
                 "involved.")
    fallback_cloud = vram is None and not apple and (ram or 0) < 8_000
    if fallback_cloud:
        note += (
            " No discrete GPU and <8GB free RAM: even 7b may be unusably slow. "
            "Documented exception: set llm.provider=cloud in config.yaml, put "
            "OLLAMA_API_KEY in .env, and split batch runs across multiple "
            "5-hour free-tier sessions."
        )
    return {"gpu_vram_mb": vram, "system_ram_mb": ram,
            "apple_silicon": apple,
            "recommended_model": tier, "cloud_fallback_advised": fallback_cloud,
            "note": note}


if __name__ == "__main__":
    import json
    print(json.dumps(recommend_model(), indent=2))

"""Load config.yaml + .env once, hand out a plain dict.

Nothing model- or provider-specific is hardcoded anywhere else in the
codebase: switching local<->cloud Ollama or changing model size is a
config.yaml edit, never a code change.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is in requirements
    def load_dotenv(*_a, **_k):
        return False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(path: Path | str | None = None) -> dict:
    load_dotenv(PROJECT_ROOT / ".env")
    cfg_path = Path(path) if path else CONFIG_PATH
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["_project_root"] = str(PROJECT_ROOT)
    return cfg


def resolve(cfg: dict, rel: str) -> Path:
    """Resolve a config-relative path against the project root."""
    p = Path(rel)
    return p if p.is_absolute() else Path(cfg["_project_root"]) / p


def ollama_api_key() -> str | None:
    return os.environ.get("OLLAMA_API_KEY") or None

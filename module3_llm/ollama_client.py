"""The ONE place in this codebase that talks to a language model.

The original design used the Anthropic SDK in two places (semantic mutant
generation in mutant_normalizer.py, and the LLM test rewriter). Both now call
into this single client, backed by Ollama.

DELIBERATE SUBSTITUTION / THREAT TO VALIDITY: swapping Claude for an open
local model changes the ceiling on instruction-following and code-generation
quality relative to the original design. The RAG-vs-NO_RAG comparison inside
a run remains internally valid (both conditions use the same model), but
absolute kill-rate / valid-test-rate numbers are NOT comparable to a
Claude-backed run and must not be presented as such. See paper/ notes.

Provider is config, never code:
  llm.provider = "local"  -> http://localhost:11434, free, unlimited, no key
  llm.provider = "cloud"  -> https://ollama.com with OLLAMA_API_KEY (free tier
                             is rate-limited: 5-hour sessions, weekly caps,
                             one concurrent model — documented fallback ONLY
                             for machines that can't run a 7B locally)

Every call is logged to a JSONL file (model, temps, durations, token counts
when Ollama reports them) so token-cost-equivalent metrics for RQ4 can be
computed without a paid API's accounting.

API shape verified against current docs (ollama-python Client.chat with
options={'temperature': ...}; REST POST /api/chat with stream=false).
"""
from __future__ import annotations

import ast
import json
import re
import time
from pathlib import Path

from core.config import ollama_api_key, resolve

try:
    import ollama as _ollama_pkg
except ImportError:
    _ollama_pkg = None

try:
    import requests as _requests
except ImportError:
    _requests = None

_FENCE_RE = re.compile(r"```(?:python|json)?\s*\n?(.*?)```", re.DOTALL)


class OllamaClient:
    def __init__(self, cfg: dict):
        llm = cfg["llm"]
        self.provider = llm["provider"]
        self.model = llm["model"]
        self.timeout = llm.get("request_timeout_seconds", 300)
        self.temp_testgen = llm.get("temperature_testgen", 0.0)
        self.temp_semantic = llm.get("temperature_semantic", 0.7)
        self.log_path = resolve(cfg, llm["call_log"])
        self.calls_made = 0

        if self.provider == "cloud":
            self.host = llm["cloud_host"]
            key = ollama_api_key()
            if not key:
                raise RuntimeError(
                    "llm.provider is 'cloud' but OLLAMA_API_KEY is not set in "
                    ".env. Either set it, or switch provider to 'local'.")
            self.headers = {"Authorization": f"Bearer {key}"}
        else:
            self.host = llm["local_host"]
            self.headers = {}

        self._client = (_ollama_pkg.Client(host=self.host, headers=self.headers)
                        if _ollama_pkg else None)

    # ------------------------------------------------------------- raw call
    def _chat(self, system_prompt: str, user_prompt: str,
              temperature: float) -> tuple[str, dict]:
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]
        options = {"temperature": temperature}
        if self._client is not None:
            resp = self._client.chat(model=self.model, messages=messages,
                                     options=options)
            content = resp["message"]["content"]
            meta = {k: resp.get(k) for k in
                    ("eval_count", "prompt_eval_count", "total_duration")}
        elif _requests is not None:
            r = _requests.post(f"{self.host}/api/chat", timeout=self.timeout,
                               headers=self.headers,
                               json={"model": self.model, "messages": messages,
                                     "options": options, "stream": False})
            r.raise_for_status()
            data = r.json()
            content = data["message"]["content"]
            meta = {k: data.get(k) for k in
                    ("eval_count", "prompt_eval_count", "total_duration")}
        else:
            raise RuntimeError("Neither the 'ollama' package nor 'requests' is "
                               "installed — cannot reach any model.")
        return content, meta

    def _log(self, record: dict) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    def generate(self, system_prompt: str, user_prompt: str,
                 temperature: float | None = None,
                 purpose: str = "generic") -> str:
        temp = self.temp_testgen if temperature is None else temperature
        t0 = time.time()
        content, meta = self._chat(system_prompt, user_prompt, temp)
        self.calls_made += 1
        self._log({"ts": time.time(), "provider": self.provider,
                   "model": self.model, "temperature": temp, "purpose": purpose,
                   "wall_seconds": round(time.time() - t0, 2),
                   "system_prompt": system_prompt, "user_prompt": user_prompt,
                   "response_chars": len(content), **{k: v for k, v in
                                                      meta.items() if v is not None}})
        return content

    # ------------------------------------------- validated, retry-once forms
    @staticmethod
    def _strip_fences(text: str) -> str:
        m = _FENCE_RE.search(text)
        return (m.group(1) if m else text).strip()

    def generate_json(self, system_prompt: str, user_prompt: str,
                      temperature: float | None = None,
                      purpose: str = "json") -> dict | None:
        """generate() whose output must be a JSON object. Retries ONCE with a
        simplified prompt if the first response doesn't parse."""
        temp = self.temp_semantic if temperature is None else temperature
        for attempt, (sp, up) in enumerate([
            (system_prompt, user_prompt),
            (system_prompt + " Output ONLY the raw JSON object. No prose, "
             "no markdown fences.", user_prompt),
        ]):
            raw = self.generate(sp, up, temp, purpose=f"{purpose}:a{attempt}")
            for cand in (raw.strip(), self._strip_fences(raw)):
                try:
                    obj = json.loads(cand)
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    continue
        return None

    def generate_python(self, system_prompt: str, user_prompt: str,
                        temperature: float | None = None,
                        purpose: str = "python") -> str | None:
        """generate() whose output must ast.parse as Python. Retries ONCE with
        a simplified prompt if the first response doesn't."""
        temp = self.temp_testgen if temperature is None else temperature
        for attempt, (sp, up) in enumerate([
            (system_prompt, user_prompt),
            (system_prompt + " Output ONLY runnable Python source code. "
             "No prose, no markdown fences, no explanations.", user_prompt),
        ]):
            raw = self.generate(sp, up, temp, purpose=f"{purpose}:a{attempt}")
            code = self._strip_fences(raw)
            try:
                ast.parse(code)
                return code
            except SyntaxError:
                continue
        return None

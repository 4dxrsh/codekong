"""Build class-specific prompts and call the shared ollama_client to produce
a test rewrite. Used identically by both conditions:

  NO_RAG: context_chunks=None  -> the {context_section} slot is empty
          (closed-book, MuTAP-style: diff + original test only)
  RAG:    context_chunks=[...] -> retrieved repo chunks are injected

Temperature is ALWAYS the configured test-generation temperature (0 by
default) — the determinism requirement from the original design.
"""
from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

_TEMPLATE_BY_CLASS = {
    "syntactic": "prompt_syntactic.txt",
    "sdl": "prompt_sdl.txt",
    "semantic": "prompt_semantic.txt",
    "higher_order": "prompt_hom.txt",
}

SYSTEM_PROMPT = (
    "You are an expert Python test engineer. You write minimal, deterministic "
    "pytest files that kill specific mutants. You output only Python source "
    "code, never explanations."
)


def load_template(mutation_class: str) -> str:
    return (PROMPTS_DIR / _TEMPLATE_BY_CLASS[mutation_class]).read_text(
        encoding="utf-8")


def make_import_hint(mutant: dict, subject_subdir: str) -> str:
    """Best-effort import line for the function under test. The generated test
    runs from the subject repo root, so the module path mirrors the file path.

    For METHODS (qualname like 'FilesArray.get_dict') the importable symbol is
    the CLASS, not the method — `from mod import get_dict` would be a
    guaranteed ImportError and every such test would be INVALID regardless of
    model quality (a real bug we shipped and then measured)."""
    mod = mutant["file"].removesuffix(".py").replace("/", ".")
    parts = mutant["function"].split(".")
    if len(parts) > 1:
        return (f"from {mod} import {parts[0]}  "
                f"# then exercise the method {mutant['function']}()")
    return f"from {mod} import {parts[0]}"


def format_context_section(context_chunks: list[dict] | None) -> str:
    if not context_chunks:
        return ""
    parts = ["\n## Retrieved repository context (RAG)\n"
             "These chunks come from the actual codebase under test — real "
             "function bodies, docstrings, and existing tests. Use them to "
             "match import paths, data conventions, and edge-case behavior.\n"]
    for i, ch in enumerate(context_chunks, 1):
        src = ch.get("metadata", {})
        parts.append(f"### Chunk {i} — {src.get('file', '?')}:"
                     f"{src.get('qualname', '?')} ({src.get('kind', 'code')})\n"
                     f"```python\n{ch['document']}\n```\n")
    return "\n".join(parts)


def build_prompt(mutant: dict, existing_tests: str,
                 context_chunks: list[dict] | None,
                 subject_subdir: str, feedback: str | None = None) -> str:
    template = load_template(mutant["mutation_class"])
    prompt = template.format(
        function=mutant["function"], file=mutant["file"], line=mutant["line"],
        mutation_description=mutant["mutation_description"],
        diff=mutant["diff"], original_code=mutant["original_code"],
        mutated_code=mutant["mutated_code"],
        existing_tests=existing_tests or "(no existing test content available)",
        context_section=format_context_section(context_chunks),
        import_hint=make_import_hint(mutant, subject_subdir),
    )
    if feedback:
        prompt += (
            "\n## Feedback from the previous attempt (validator output)\n"
            f"{feedback}\n"
            "Fix exactly what the feedback describes. Keep everything that "
            "already worked."
        )
    return prompt


def rewrite_test(client, mutant: dict, existing_tests: str,
                 context_chunks: list[dict] | None, subject_subdir: str,
                 feedback: str | None = None) -> str | None:
    """Returns validated-parsing Python test source, or None if the model
    failed twice (ollama_client retries once internally)."""
    user_prompt = build_prompt(mutant, existing_tests, context_chunks,
                               subject_subdir, feedback)
    condition = "RAG" if context_chunks else "NO_RAG"
    # mutant_id in purpose enables per-mutant token attribution from the
    # JSONL call log (RQ4 / UI cost views). metrics_logger's class regex
    # still matches: it captures the third segment and ignores the rest.
    return client.generate_python(
        SYSTEM_PROMPT, user_prompt, temperature=client.temp_testgen,
        purpose=f"testgen:{condition}:{mutant['mutation_class']}:{mutant['mutant_id']}")

"""Lightweight, dependency-free validation for anything a user can upload or
type into CodeKong — chiefly the web UI's /generate form.

This is NOT a sandbox: the uploaded code is never executed here, only parsed.
The goal is to reject the obvious foot-guns before user input reaches the
pipeline — wrong type, oversized, binary/garbage, unsafe or traversing file
names, and abusive free-text — with a clear, user-facing message for each.

    from core.input_security import (safe_filename, validate_source,
                                     clean_description, InputRejected)

Everything is standard library (ast, os, re, unicodedata) so it adds no deps
and is safe to import anywhere (web app, CLI, tests).
"""
from __future__ import annotations

import ast
import os
import re
import unicodedata

# Conservative caps — a single source file under test is small; these exist to
# stop accidental or malicious oversized/garbage input, not to be generous.
MAX_UPLOAD_BYTES = 1_000_000        # 1 MB of Python source is already a lot
MAX_SOURCE_LINES = 20_000
MAX_DESCRIPTION_CHARS = 2_000
ALLOWED_SUFFIXES = (".py",)


class InputRejected(ValueError):
    """User input failed a security/sanity check. The message is safe to show
    to the user (it never echoes file contents)."""


def safe_filename(name: str) -> str:
    """Return a safe basename for an upload, or raise InputRejected.

    Strips any directory component (defeats ``../`` path traversal and absolute
    paths), restricts to a conservative character set, forbids hidden/dotfiles,
    and enforces the allowed extension.
    """
    if not name or not name.strip():
        raise InputRejected("no filename provided")
    # Take the basename after normalising both separators — never trust a path.
    base = os.path.basename(name.replace("\\", "/")).strip()
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    base = base.lstrip(".")             # no leading dots -> no hidden files
    if not base:
        raise InputRejected("filename has no usable characters")
    if not base.lower().endswith(ALLOWED_SUFFIXES):
        raise InputRejected("only .py files are accepted")
    if len(base) > 128:
        base = base[-128:]
    return base


def validate_source(raw: bytes) -> str:
    """Validate raw uploaded bytes as a Python source file and return the text.

    Rejects empty, oversized, binary (null bytes), non-UTF-8, over-long, or
    syntactically invalid input. Parsing (never executing) also guarantees the
    downstream pipeline receives a file it can actually work with.
    """
    if not raw:
        raise InputRejected("the file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise InputRejected(
            f"file too large (> {MAX_UPLOAD_BYTES // 1000} KB)")
    if b"\x00" in raw:
        raise InputRejected("file looks binary (contains null bytes)")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputRejected("file is not valid UTF-8 text")
    if text.count("\n") + 1 > MAX_SOURCE_LINES:
        raise InputRejected(f"file has too many lines (> {MAX_SOURCE_LINES})")
    try:
        ast.parse(text)
    except SyntaxError as exc:
        raise InputRejected(
            f"not valid Python: {exc.msg} (line {exc.lineno})")
    return text


def clean_description(text: str) -> str:
    """Trim and sanitise the free-text description field: cap the length and
    drop control characters (keeping newlines and tabs)."""
    text = (text or "").strip()
    if len(text) > MAX_DESCRIPTION_CHARS:
        text = text[:MAX_DESCRIPTION_CHARS]
    return "".join(ch for ch in text
                   if ch in "\n\t" or unicodedata.category(ch)[0] != "C")

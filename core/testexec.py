"""Apply mutants to a working tree and run pytest with a hard timeout.

Timeout strategy: subprocess.run(..., timeout=N) per the roadmap's run_tests()
spec — simpler to reason about than signal-based alarms, even though WSL2's
real Linux kernel would technically support SIGALRM too. A TimeoutExpired is
treated as the mutant being KILLED (infinite-loop mutants are dead mutants).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestRun:
    passed: bool
    timed_out: bool
    returncode: int | None
    stdout: str
    stderr: str

    def tail(self, n: int = 30) -> str:
        lines = (self.stdout + "\n" + self.stderr).strip().splitlines()
        return "\n".join(lines[-n:])


def run_tests(test_targets: str | Path | list, cwd: str | Path,
              timeout: int = 10, extra_args: list[str] | None = None) -> TestRun:
    targets = ([str(t) for t in test_targets] if isinstance(test_targets, list)
               else [str(test_targets)])
    # -B / PYTHONDONTWRITEBYTECODE: this pipeline rewrites source files in
    # place (mutant apply/restore). A same-size rewrite within one mtime tick
    # makes a stale __pycache__ entry look valid, silently running the OLD
    # code. Never write bytecode caches during test runs.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-B", "-m", "pytest", *targets, "-x", "-q",
           "--no-header", "-p", "no:cacheprovider"] + (extra_args or [])
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                              text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired as exc:
        return TestRun(passed=False, timed_out=True, returncode=None,
                       stdout=(exc.stdout or b"" if isinstance(exc.stdout, bytes) else exc.stdout or ""),
                       stderr="TIMEOUT after %ss" % timeout)
    return TestRun(passed=proc.returncode == 0, timed_out=False,
                   returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


class MutantApplier:
    """Context manager: swap original_code -> mutated_code in a file, always restore.

    Text-level replacement of the exact function source, which the schema
    guarantees we carry for every mutant regardless of its source.
    """

    def __init__(self, repo_root: str | Path, mutant: dict):
        self.file = Path(repo_root) / mutant["file"]
        self.mutant = mutant
        self._backup: str | None = None

    def _drop_bytecode_cache(self):
        """A stale .pyc compiled from the pre-swap source can pass Python's
        (mtime, size) validity check when the mutation preserves file size and
        lands within one mtime tick — the mutant would silently never run.
        Deleting the adjacent __pycache__ makes that impossible."""
        shutil.rmtree(self.file.parent / "__pycache__", ignore_errors=True)

    def __enter__(self):
        src = self.file.read_text(encoding="utf-8")
        orig = self.mutant["original_code"]
        if orig not in src:
            raise RuntimeError(
                f"{self.mutant['mutant_id']}: original_code not found verbatim in "
                f"{self.file} — subject repo drifted from the pinned commit?")
        if src.count(orig) > 1:
            raise RuntimeError(
                f"{self.mutant['mutant_id']}: original_code appears "
                f"{src.count(orig)} times in {self.file}; refusing ambiguous apply")
        self._backup = src
        self.file.write_text(src.replace(orig, self.mutant["mutated_code"], 1),
                             encoding="utf-8")
        self._drop_bytecode_cache()
        return self

    def __exit__(self, *exc):
        if self._backup is not None:
            self.file.write_text(self._backup, encoding="utf-8")
            self._drop_bytecode_cache()
        return False

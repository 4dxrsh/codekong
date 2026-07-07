"""Environment guards.

mutmut requires fork(), which only a real POSIX kernel provides (Linux —
including WSL2 — or macOS). The primary documented target is WSL2 Ubuntu on
the project laptop; macOS is a supported secondary target (mutmut runs
natively there and auto-disables the fork-unsafe setproctitle library on
macOS). This guard fails loudly BEFORE mutmut ever runs on plain Windows,
instead of letting mutmut die with a cryptic fork-related error when someone
launches the pipeline from PowerShell or an old VMware VM out of habit.
"""
from __future__ import annotations

import os
import platform
import sys


class EnvironmentGuardError(RuntimeError):
    pass


def is_wsl2() -> bool:
    try:
        return "microsoft" in platform.uname().release.lower()
    except Exception:
        return False


def assert_fork_capable_linux(require_wsl: bool = False) -> None:
    """Fail loudly if mutmut cannot possibly work here.

    - Windows: hard fail with instructions (no fork()).
    - macOS: allowed with a notice (fork works; Ollama uses Metal on Apple
      Silicon; nvidia-smi/WSL guidance does not apply).
    - Real Linux that is NOT WSL2 (native Ubuntu, CI container): allowed with
      a notice. Set require_wsl=True (or CODEKONG_REQUIRE_WSL=1) to hard-fail
      on anything but WSL2.
    """
    if sys.platform.startswith("win"):
        raise EnvironmentGuardError(
            "CodeKong is running on native Windows. mutmut requires fork() "
            "support, which Windows does not provide. Open a WSL2 Ubuntu "
            "terminal (run `wsl` from PowerShell, or see README section "
            "'Setting up WSL2 from zero') and run the pipeline from there. "
            "Do NOT use the old VMware VM: it cannot reach the RTX 3050 Ti, "
            "and WSL2 can."
        )
    if sys.platform == "darwin":
        print("[guards] Note: running on macOS. fork() works and mutmut "
              "supports this platform natively; the WSL2/nvidia-smi guidance "
              "in the README applies only to the Windows laptop.",
              file=sys.stderr)
        return
    if not sys.platform.startswith("linux"):
        raise EnvironmentGuardError(
            f"Unsupported platform {sys.platform!r}: mutmut needs a POSIX "
            "kernel with fork(). Use WSL2 Ubuntu (or macOS) as described in "
            "the README."
        )
    want_wsl = require_wsl or os.environ.get("CODEKONG_REQUIRE_WSL") == "1"
    if not is_wsl2():
        msg = (
            "Note: running on a Linux kernel that is not WSL2 "
            f"(uname -r: {platform.uname().release}). fork() works here, so "
            "mutmut will run, but the documented target environment is WSL2 "
            "with the RTX 3050 Ti visible via `nvidia-smi`."
        )
        if want_wsl:
            raise EnvironmentGuardError(msg + " CODEKONG_REQUIRE_WSL=1 is set, aborting.")
        print(f"[guards] {msg}", file=sys.stderr)


def assert_not_windows_mount(project_root) -> None:
    """Refuse to run the pipeline from /mnt/<drive>/ inside WSL2.

    The Windows drive mount (drvfs/9p) caches file metadata. This pipeline
    rewrites source files in place during mutant application, and stale
    metadata can make Python's bytecode cache serve PRE-mutation code — the
    mutant silently never executes and every result is garbage. We hit this
    exact failure during development. The project must live on the Linux
    filesystem (e.g. ~/codekong).
    """
    p = str(project_root)
    if is_wsl2() and len(p) > 6 and p.startswith("/mnt/") and p[6] == "/":
        raise EnvironmentGuardError(
            f"CodeKong is running from the Windows drive mount ({p}). This "
            "corrupts mutation results (stale-metadata bytecode caching) and "
            "is refused outright. Copy the project to your Linux home and "
            "run it there:\n"
            f"    cp -r {p} ~/codekong\n"
            "    cd ~/codekong\n"
            "    rm -rf venv subjects module1_mutation/_scratch\n"
            "    bash setup.sh"
        )

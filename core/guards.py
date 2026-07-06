"""Environment guards.

mutmut requires fork(), which only a real or virtual Linux kernel provides.
The target environment is WSL2 Ubuntu on the user's laptop. This guard fails
loudly BEFORE mutmut ever runs, instead of letting mutmut die with a cryptic
fork-related error when someone launches the pipeline from Windows PowerShell
or an old VMware VM out of habit.
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

    - Windows / macOS-without-fork-safety: hard fail with instructions.
    - Real Linux that is NOT WSL2 (e.g. a native Ubuntu box or CI container):
      allowed with a notice, because fork works there too. Set require_wsl=True
      (or CODEKONG_REQUIRE_WSL=1) to hard-fail on anything but WSL2.
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
    if not sys.platform.startswith("linux"):
        raise EnvironmentGuardError(
            f"Unsupported platform {sys.platform!r}: mutmut needs a Linux "
            "kernel with fork(). Use WSL2 Ubuntu as described in the README."
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

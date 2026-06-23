"""Resolve DEVASCENT_HOME for standalone skill scripts.

Skill scripts may run outside the Hermes process (e.g. system Python,
nix env, CI) where ``devascent_constants`` is not importable.  This module
provides the same ``get_devascent_home()`` and ``display_devascent_home()``
contracts as ``devascent_constants`` without requiring it on ``sys.path``.

When ``devascent_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``devascent_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``DEVASCENT_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from devascent_constants import display_devascent_home as display_devascent_home
    from devascent_constants import get_devascent_home as get_devascent_home
except (ModuleNotFoundError, ImportError):

    def get_devascent_home() -> Path:
        """Return the Hermes home directory (default: ~/.devascent).

        Mirrors ``devascent_constants.get_devascent_home()``."""
        val = os.environ.get("DEVASCENT_HOME", "").strip()
        return Path(val) if val else Path.home() / ".hermes"

    def display_devascent_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``devascent_constants.display_devascent_home()``."""
        home = get_devascent_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)

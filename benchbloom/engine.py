"""Orchestration bridge to the C++ `bloomdex` engine.

Locates or falls back gracefully when the compiled binary is unavailable, and
wraps the `sign` / `match` / `self` subcommands with subprocess calls plus
parsing of the tab-separated report files they emit.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class EngineError(RuntimeError):
    """Raised when the C++ engine is missing or exits non-zero."""


def find_engine(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve the bloomdex binary: explicit path, PATH, or local build dirs."""
    if explicit:
        p = Path(explicit)
        return str(p) if p.exists() else None
    on_path = shutil.which("bloomdex")
    if on_path:

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
        return on_path
    here = Path(__file__).resolve().parent.parent
    for cand in (here / "cpp" / "bloomdex", here / "cpp" / "bloomdex.exe",
                 here / "build" / "bloomdex", here / "build" / "bloomdex.exe"):
        if cand.exists():
            return str(cand)
    return None


def _run(engine: str, args: List[str]) -> str:
    proc = subprocess.run([engine, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise EngineError(f"bloomdex {' '.join(args)} failed "
                          f"(code {proc.returncode}): {proc.stderr.strip()}")
    return proc.stderr.strip()


def sign(engine: str, input_path: str, out_path: str, *, k: int = 128,
         ngram: int = 5, min_token: int = 1, seed: int = 0) -> str:
    """Build MinHash signatures for a normalized corpus."""
    return _run(engine, ["sign", "--input", input_path, "--out", out_path,
                         "--k", str(k), "--ngram", str(ngram),
                         "--min-token", str(min_token), "--seed", str(seed)])


def match(engine: str, ref_sig: str, subject_sig: str, out_path: str,
          *, threshold: float = 0.5) -> str:
    """Score candidate overlap between reference and subject signatures."""
    return _run(engine, ["match", "--ref", ref_sig, "--subject", subject_sig,
                         "--out", out_path, "--threshold", str(threshold)])


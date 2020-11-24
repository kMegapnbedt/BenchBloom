"""Leakage metrics for benchbloom (pure standard library).

Provides exact n-gram shingling and Jaccard/containment scoring used by the
Python-only path, plus helpers to summarize a leakage report. The C++ engine
gives an approximate (MinHash) answer at scale; these functions give the exact
answer for small-to-medium corpora and for verifying the estimator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple


def shingles(tokens: Sequence[str], n: int) -> Set[str]:
    """Return the set of n-gram shingles (token n-grams joined by unit sep)."""
    if n <= 0:
        raise ValueError("n must be >= 1")
    if len(tokens) < n:
        return {"\x1f".join(tokens)} if tokens else set()
    return {"\x1f".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard(a: Set[str], b: Set[str]) -> float:
    """Exact Jaccard similarity |A∩B| / |A∪B|."""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def containment(a: Set[str], b: Set[str]) -> float:

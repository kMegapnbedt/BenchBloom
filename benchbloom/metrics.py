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
    """Containment of A in B: |A∩B| / |A|. Sensitive to short-in-long leakage."""
    if not a:
        return 0.0
    return len(a & b) / len(a)


@dataclass
class LeakPair:
    ref_id: str
    subject_id: str
    jaccard: float
    containment: float


def _tokenize(text: str) -> List[str]:
    return text.split()


def build_shingle_index(records, n: int) -> Dict[str, Set[str]]:
    """Map record id -> shingle set for a list of (id, normalized_text)."""
    index: Dict[str, Set[str]] = {}
    for rid, text in records:
        index[rid] = shingles(_tokenize(text), n)
    return index


def cross_leakage(ref_index: Dict[str, Set[str]],
                  subject_index: Dict[str, Set[str]],
                  *, threshold: float = 0.3,
                  use_containment: bool = True) -> List[LeakPair]:
    """Score every ref x subject pair; keep those at or above threshold.

    Uses containment as the trigger metric by default because contamination
    often appears as a short benchmark item embedded in a longer training doc.
    """
    pairs: List[LeakPair] = []
    for ref_id, ref_sh in ref_index.items():
        if not ref_sh:
            continue
        for sub_id, sub_sh in subject_index.items():
            if not sub_sh:
                continue
            jc = jaccard(ref_sh, sub_sh)
            ct = containment(ref_sh, sub_sh)
            trigger = ct if use_containment else jc
            if trigger >= threshold:
                pairs.append(LeakPair(ref_id, sub_id, round(jc, 4), round(ct, 4)))
    pairs.sort(key=lambda p: max(p.jaccard, p.containment), reverse=True)
    return pairs


def summarize(pairs: List[LeakPair], ref_count: int) -> Dict[str, float]:
    """Aggregate a report: contaminated ref items, rates, and peak overlap."""

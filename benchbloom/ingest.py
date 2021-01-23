"""Ingestion and normalization for benchbloom.

Reads JSONL or plain-text corpora into a uniform list of records, then applies
deterministic text normalization so that leakage comparisons are robust to
whitespace, casing, and punctuation noise.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List

_WS_RE = re.compile(r"\s+")
_NONALNUM_RE = re.compile(r"[^0-9a-z ]+")


@dataclass
class Record:
    """A single corpus item after ingestion."""

    rid: str
    text: str
    meta: dict = field(default_factory=dict)


def normalize(text: str, *, strip_punct: bool = True) -> str:
    """Lowercase, NFKC-fold, collapse whitespace; optionally drop punctuation.

    The output is stable and idempotent, which matters for reproducible
    n-gram/Jaccard reports.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    if strip_punct:
        text = _NONALNUM_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


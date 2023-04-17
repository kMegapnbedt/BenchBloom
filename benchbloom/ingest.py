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


def _extract_text(obj: dict, fields: List[str]) -> str:
    """Pull and concatenate the configured text fields from a JSON object."""
    parts: List[str] = []
    for f in fields:
        val = obj.get(f)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, (list, tuple)):
            parts.extend(str(v) for v in val if isinstance(v, (str, int, float)))
    return " ".join(parts)


def read_jsonl(path: Path, fields: List[str], id_field: str | None = None) -> Iterator[Record]:
    """Stream a JSONL file into Records, skipping malformed lines gracefully."""
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # Tolerate the occasional broken line rather than aborting a scan.
                continue
            if not isinstance(obj, dict):
                obj = {"text": str(obj)}
            text = _extract_text(obj, fields) if fields else str(obj.get("text", ""))
            rid = str(obj.get(id_field, f"j{i}")) if id_field else f"j{i}"
            yield Record(rid=rid, text=text, meta={k: obj[k] for k in obj if k not in fields})


def read_text(path: Path) -> Iterator[Record]:
    """Stream a plain-text file: one record per non-empty line."""
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.rstrip("\n")

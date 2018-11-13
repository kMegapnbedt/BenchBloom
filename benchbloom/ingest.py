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

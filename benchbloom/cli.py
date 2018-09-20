"""benchbloom command-line interface (pure standard library).

Subcommands
-----------
normalize   Ingest JSONL/text and emit a normalized, one-record-per-line file.
scan        Exact n-gram/Jaccard leakage report (Python only).
index       Orchestrate the C++ engine: normalize -> sign -> match.
report      Render a saved TSV match report into a human summary.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import __version__, engine, ingest, metrics


def _cmd_normalize(args: argparse.Namespace) -> int:
    records = ingest.load(args.input, fields=args.field, id_field=args.id_field)
    n = ingest.write_normalized(records, args.out, strip_punct=not args.keep_punct)
    print(f"normalized {n} records -> {args.out}")

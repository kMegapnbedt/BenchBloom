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
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    ref = ingest.load(args.ref, fields=args.field, id_field=args.id_field)
    sub = ingest.load(args.subject, fields=args.field, id_field=args.id_field)
    ref_norm = [(r.rid, ingest.normalize(r.text)) for r in ref]
    sub_norm = [(s.rid, ingest.normalize(s.text)) for s in sub]

    ref_idx = metrics.build_shingle_index(ref_norm, args.ngram)
    sub_idx = metrics.build_shingle_index(sub_norm, args.ngram)
    pairs = metrics.cross_leakage(ref_idx, sub_idx, threshold=args.threshold,

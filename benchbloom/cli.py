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
                                  use_containment=not args.jaccard_only)
    summary = metrics.summarize(pairs, len(ref_idx))

    report = {
        "summary": summary,
        "pairs": [vars(p) for p in pairs[: args.top]] if args.top else [vars(p) for p in pairs],
    }
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"scan report -> {args.out}")
    else:
        print(text)
    _print_verdict(summary)
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    eng = engine.find_engine(args.engine)
    if not eng:
        print("error: bloomdex engine not found. Build it with cpp/build.sh or make.",
              file=sys.stderr)
        return 3

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="benchbloom_"))
    workdir.mkdir(parents=True, exist_ok=True)

    ref = ingest.load(args.ref, fields=args.field, id_field=args.id_field)
    sub = ingest.load(args.subject, fields=args.field, id_field=args.id_field)
    ref_norm = workdir / "ref.norm.txt"
    sub_norm = workdir / "subject.norm.txt"
    ingest.write_normalized(ref, ref_norm)
    ingest.write_normalized(sub, sub_norm)

    ref_sig = workdir / "ref.sig"
    sub_sig = workdir / "subject.sig"
    print(engine.sign(eng, str(ref_norm), str(ref_sig), k=args.k, ngram=args.ngram))
    print(engine.sign(eng, str(sub_norm), str(sub_sig), k=args.k, ngram=args.ngram))

    match_out = Path(args.out) if args.out else workdir / "match.tsv"
    print(engine.match(eng, str(ref_sig), str(sub_sig), str(match_out),
                       threshold=args.threshold))
    rows = engine.parse_match_report(match_out)


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

    contaminated = {r.ref_id for r in rows}
    summary = {
        "ref_items": len(ref),
        "flagged_pairs": len(rows),
        "contaminated_ref_items": len(contaminated),
        "contamination_rate": round(len(contaminated) / len(ref), 4) if ref else 0.0,
        "peak_overlap": round(max((r.jaccard for r in rows), default=0.0), 4),
    }
    print(f"match report -> {match_out}")
    _print_verdict(summary)
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    rows = engine.parse_match_report(args.input)
    contaminated = {r.ref_id for r in rows}
    print(f"flagged pairs        : {len(rows)}")
    print(f"contaminated ref ids : {len(contaminated)}")
    if rows:
        top = sorted(rows, key=lambda r: r.jaccard, reverse=True)[: args.top]
        print("top overlaps:")
        for r in top:
            print(f"  {r.ref_id:>10}  <->  {r.subject_id:<10}  jaccard={r.jaccard:.3f}")
    return 0


def _print_verdict(summary: dict) -> None:
    rate = summary.get("contamination_rate", 0.0)
    if rate == 0.0:
        verdict = "CLEAN — no leakage above threshold"
    elif rate < 0.05:
        verdict = "TRACE — isolated overlap, inspect flagged pairs"
    elif rate < 0.25:
        verdict = "ELEVATED — meaningful contamination present"
    else:
        verdict = "HEAVY — benchmark likely compromised"
    print(f"verdict: {verdict} (rate={rate})", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="benchbloom",
                                description="benchmark contamination detector")
    p.add_argument("--version", action="version", version=f"benchbloom {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--field", action="append", help="JSON text field(s) to read")
        sp.add_argument("--id-field", help="JSON field to use as record id")
        sp.add_argument("--ngram", type=int, default=5, help="token n-gram size")

    pn = sub.add_parser("normalize", help="ingest and normalize a corpus")
    pn.add_argument("input")
    pn.add_argument("--out", required=True)
    pn.add_argument("--field", action="append")
    pn.add_argument("--id-field")
    pn.add_argument("--keep-punct", action="store_true")
    pn.set_defaults(func=_cmd_normalize)

    ps = sub.add_parser("scan", help="exact Python n-gram/Jaccard leakage report")
    ps.add_argument("--ref", required=True)
    ps.add_argument("--subject", required=True)
    ps.add_argument("--out")
    ps.add_argument("--threshold", type=float, default=0.3)

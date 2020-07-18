# Roadmap

benchbloom follows a foundation-first plan. The milestones below marked done
are the ones actually implemented and verified in this repository. Everything
under "Planned" is aspirational and not yet built.

## Foundation (verified in this release)

- [x] **M1 — Ingestion & normalization.** JSONL/text loaders with tolerant
  parsing and deterministic NFKC + whitespace/punctuation normalization.
  Implemented in `benchbloom/ingest.py`.
- [x] **M2 — Exact leakage metrics.** Token n-gram shingling with Jaccard and

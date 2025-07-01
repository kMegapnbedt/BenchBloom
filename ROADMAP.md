# Roadmap

benchbloom follows a foundation-first plan. The milestones below marked done
are the ones actually implemented and verified in this repository. Everything
under "Planned" is aspirational and not yet built.

## Foundation (verified in this release)

- [x] **M1 — Ingestion & normalization.** JSONL/text loaders with tolerant
  parsing and deterministic NFKC + whitespace/punctuation normalization.
  Implemented in `benchbloom/ingest.py`.
- [x] **M2 — Exact leakage metrics.** Token n-gram shingling with Jaccard and
  containment scoring and a report summarizer. Implemented in
  `benchbloom/metrics.py`.
- [x] **M3 — C++17 MinHash engine.** `bloomdex` builds min-hash signatures over
  token shingles and scores candidate overlap; compiles cleanly with `g++`
  `-std=c++17`. Implemented in `cpp/bloomdex.cpp`.
- [x] **M4 — Python↔C++ orchestration.** The `index` subcommand normalizes,
  signs, and matches through the engine bridge in `benchbloom/engine.py`.

## Planned (not yet implemented)

- [ ] LSH banding to prune the O(N·M) match loop toward near-linear behavior.
- [ ] Streaming signature format with a compact binary encoding.
- [ ] Multi-field weighting and per-field contamination attribution.
- [ ] HTML report export with highlighted overlapping shingles.
- [ ] Parallel signing across shards / threads in the C++ engine.

Honesty note: performance claims for the C++ engine are qualitative

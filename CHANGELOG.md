# Changelog

All notable changes to benchbloom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims
to adhere to Semantic Versioning.

## [Unreleased]

### Added
- `index` forwards `--seed` and `--min-token` to the signature step,
  matching the knobs `engine.sign` already accepted.

## [0.1.0] - 2026-09-01

### Added
- Pure-stdlib Python orchestrator (`benchbloom`) with `normalize`, `scan`,
  `index`, and `report` subcommands.
- JSONL / text ingestion with tolerant parsing and NFKC-based normalization.
- Exact n-gram shingling with Jaccard and containment leakage metrics.
- C++17 engine `bloomdex` implementing token-shingle MinHash signatures and
  candidate overlap scoring (`sign`, `match`, `self`).
- Direct `g++`/`clang++` build via `Makefile` and `cpp/build.sh` (no CMake).
- Worked examples: reference/subject corpora and an end-to-end walkthrough.
- CI workflow compiling the C++ engine and syntax-checking the Python package.

### Notes
- MinHash overlap is an estimate; use `scan` for exact verification on small
  corpora. Estimator variance narrows as `--k` increases.

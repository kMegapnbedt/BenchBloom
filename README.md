<div align="center">

# 🌸 benchbloom

**A forensic herbarium for benchmark contamination.**

*Press your benchmark between glass, dust it for spores, and read the pollen count where a training corpus brushed against it.*

![pipeline](docs/assets/pipeline.svg)

</div>

---

## Field notes before you begin

Contamination is quiet. A benchmark item does not announce that it has already
been seen during training — it simply germinates, unnoticed, until the day your
model scores suspiciously well and you cannot say why. benchbloom is a small,
patient instrument for finding those germinated seeds. It treats every corpus
like a pressed plant specimen: flatten it, catalogue its parts, and compare the
spore prints of two specimens to see whether one grew from the other.

There are two instruments on this bench, and they are meant to be used
together:

- **`benchbloom`** — a pure-Python-standard-library orchestrator. It is the
  botanist: it collects specimens (JSONL or text), presses and dries them
  (normalization), and can either read the exact venation of every leaf itself
  (n-gram / Jaccard) or hand the specimens to the microscope for a faster,
  approximate reading.
- **`bloomdex`** — a C++17 microscope. It grinds each specimen into token
  shingles, takes a MinHash spore print, and reports where two prints overlap.
  It reads at high throughput and streams so that a specimen larger than memory
  still fits on the slide.

No external libraries. No CMake. No test suite shipped (by design — this release
is a foundation). Just a botanist, a microscope, and a drawer of honest labels.

---

## Why a botanical metaphor, and why it is not just decoration

The metaphor earns its keep because contamination detection genuinely behaves
like comparing biological specimens:

| Botany | benchbloom |
| --- | --- |
| Pressing & drying a specimen | Normalization: NFKC fold, lowercase, collapse whitespace, drop punctuation |
| A leaf's venation pattern | The set of token n-gram *shingles* of a record |
| Two leaves sharing venation | High **Jaccard** / **containment** between shingle sets |
| A spore print on paper | A **MinHash signature**: K min-hashes standing in for the whole set |
| Matching spore prints under glass | Estimated Jaccard = fraction of matching min-positions |
| A short cutting embedded in a larger plant | **Containment**: a benchmark item copied inside a long training doc |

Containment is the metaphor that matters most. Real leakage rarely looks like
two identical documents. It looks like one small benchmark question pressed flat
inside a sprawling web-scraped paragraph. Jaccard punishes that size mismatch;
containment does not. benchbloom triggers on containment by default and reports
Jaccard alongside it, so you can see both the strict and the sensitive reading.

---

## The bench layout

```
benchbloom/
├── benchbloom/                # the botanist (pure stdlib Python)
│   ├── __init__.py
│   ├── __main__.py            # python -m benchbloom
│   ├── cli.py                 # normalize | scan | index | report
│   ├── ingest.py              # JSONL/text loaders + normalization
│   ├── metrics.py             # exact n-gram shingling, Jaccard, containment
│   └── engine.py              # bridge to the C++ microscope
├── cpp/                       # the microscope (C++17, no deps)
│   ├── bloomdex.cpp           # sign | match | self
│   └── build.sh               # direct clang++/g++ build
├── examples/                  # two pressed specimens + a walkthrough
│   ├── benchmark.jsonl
│   ├── training.jsonl
│   └── README.md
├── docs/assets/               # two animated SVG plates
│   ├── pipeline.svg
│   └── lattice.svg
├── .github/workflows/ci.yml   # compile C++, syntax-check Python, smoke test
├── Makefile                   # make  ->  cpp/bloomdex
├── pyproject.toml
├── CHANGELOG.md · ROADMAP.md · LICENSE
```

![lattice](docs/assets/lattice.svg)

---

## Preparing the bench (build the microscope)


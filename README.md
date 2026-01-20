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

The Python botanist needs nothing but a standard Python 3.8+ interpreter. The
C++ microscope must be ground from its single translation unit. Pick either
door — both call the compiler directly, no CMake in sight.

```bash
# Door 1: Makefile
make                    # produces cpp/bloomdex

# Door 2: the build script (auto-detects clang++ or g++)
bash cpp/build.sh

# Door 3: by hand, if you enjoy the sound of it
g++ -std=c++17 -O2 -Wall -Wextra -pedantic cpp/bloomdex.cpp -o cpp/bloomdex
```

On Windows with MinGW the same one-liner works; the resulting binary is
`cpp/bloomdex.exe`, and the Python bridge already knows to look for the `.exe`
suffix.

---

## A first pressing (the exact reading)

You do not need the microscope to get an exact answer on modest specimens. The
botanist can read venation directly:

```bash
python -m benchbloom scan \
  --ref examples/benchmark.jsonl \
  --subject examples/training.jsonl \
  --field text --ngram 4 --threshold 0.3
```

This prints a JSON report to stdout and a one-line **verdict** to stderr. In the
shipped example, benchmark items `b1`, `b2`, and `b4` were quietly transplanted
into the training set, and the scan will flag them with high containment. Items
`b3` (a fact about prime numbers) and `b5` (an invented city) never took root
and stay clean.

The report looks like this:

```json
{
  "summary": {
    "ref_items": 5,
    "flagged_pairs": 3,
    "contaminated_ref_items": 3,
    "contamination_rate": 0.6,
    "peak_overlap": 1.0
  },
  "pairs": [
    { "ref_id": "b1", "subject_id": "t5", "jaccard": 0.72, "containment": 1.0 },
    ...
  ]
}
```

The **verdict** grades the contamination rate on a simple herbarium scale:

- `CLEAN` — nothing germinated above threshold.
- `TRACE` — an isolated seedling; inspect the flagged pairs by hand.
- `ELEVATED` — meaningful contamination; the benchmark is compromised in part.
- `HEAVY` — the specimen is overgrown; treat scores from it with suspicion.

---

## The microscope reading (MinHash at scale)

Exact shingling is O(unique-shingles) in memory and quadratic in specimens. When
the corpus grows past comfort, hand it to the microscope. The `index` subcommand
orchestrates the whole assay: press both specimens, take their spore prints, and
overlay the prints.

```bash
python -m benchbloom index \
  --ref examples/benchmark.jsonl \
  --subject examples/training.jsonl \
  --field text --k 128 --ngram 4 --threshold 0.4 \
  --out match.tsv

python -m benchbloom report match.tsv
```

Under the hood the botanist:

1. Loads and normalizes both corpora, writing one dried record per line.
2. Calls `bloomdex sign` on each to produce a signature file — `K` 64-bit
   min-hashes per record, drawn from `K` universal hash seeds over the record's
   shingle set.
3. Calls `bloomdex match` to compare every reference print against every subject
   print, emitting a TSV of pairs whose *estimated* Jaccard clears the
   threshold.

The estimate is honest but approximate. The variance of a MinHash Jaccard
estimate shrinks roughly with `1/√K`, so `--k 128` gives you a standard error
near 0.09 and `--k 512` roughly halves it. When in doubt, confirm a flagged pair
with the exact `scan`. The microscope finds candidates; the botanist confirms
the diagnosis.

### Reading a spore print by hand

You can drive the microscope directly, without the botanist, if you already have
normalized text (one record per line):

```bash
cpp/bloomdex sign  --input ref.norm.txt --out ref.sig --k 256 --ngram 5
cpp/bloomdex sign  --input sub.norm.txt --out sub.sig --k 256 --ngram 5
cpp/bloomdex match --ref ref.sig --subject sub.sig --out match.tsv --threshold 0.5

# find near-duplicates *within* a single corpus (deduplication)
cpp/bloomdex self  --input sub.sig --out dups.tsv --threshold 0.8
```

A signature line is deliberately plain text so you can inspect it with any tool:

```
r42<TAB>318<TAB>8823...  199...  40..  (K space-separated 64-bit min-hashes)
```

---

## How the spore print is actually taken

For the curious, here is the honest mechanism, no hand-waving:

- **Shingles.** Each normalized record is split into tokens; every window of
  `ngram` consecutive tokens is joined with a unit-separator byte (`0x1f`) to
  form one shingle. The separator prevents `["a","bc"]` and `["ab","c"]` from
  colliding into the same string.
- **Base hash.** Each shingle is hashed with 64-bit FNV-1a into a base value.
- **Permutations.** `K` universal hash functions of the form
  `(a·x + b) mod (2⁶¹−1)` permute that base value. The coefficients `a, b` come
  from a `splitmix64` stream seeded deterministically, so two runs on two
  machines produce identical prints — a property you want in forensics.
- **Min selection.** For each of the `K` functions we keep the minimum permuted
  value across all shingles. That vector of `K` minima is the signature.
- **Estimate.** The estimated Jaccard between two records is simply the fraction
  of the `K` positions where their minima agree — the classic MinHash identity.

Short records (fewer tokens than `ngram`) degrade gracefully: the whole record
becomes a single shingle rather than vanishing from the assay.

---

## Command reference

### `benchbloom normalize`
Press and dry a corpus into one normalized record per line — the format the
microscope consumes.

```bash
python -m benchbloom normalize input.jsonl --out dried.txt --field text --field title
```

### `benchbloom scan`
Exact n-gram / Jaccard / containment report, Python only. Flags on containment
by default; pass `--jaccard-only` to trigger on Jaccard instead. `--top N` keeps
only the N strongest pairs in the JSON body.

### `benchbloom index`
Full orchestration through the C++ engine. `--k` sets signature width, `--ngram`
the shingle size, `--threshold` the estimated-Jaccard cutoff, `--engine` an
explicit path to the binary, and `--workdir` a place to keep intermediates.

### `benchbloom report`
Render a saved `match.tsv` into a human summary with the strongest overlaps
listed first.

### `bloomdex sign | match | self`
The microscope's three lenses: build signatures, compare two signature sets, and
find near-duplicates within one set. Run `bloomdex --help` for the exact flags.

---

## Interpreting results without fooling yourself

A few honest cautions from the field log:

- **Threshold is a dial, not a truth.** A high threshold misses paraphrased
  leakage; a low one drowns you in coincidental n-gram overlap. Sweep it.
- **Containment finds the small-in-large case.** If your benchmark items are
  short and your training docs are long, prefer the default containment trigger.
- **MinHash is a screen, not a verdict.** Treat every flagged pair as a
  candidate and confirm the important ones with the exact `scan`.
- **Normalization changes the answer.** Stripping punctuation merges more items;
  keeping it (`--keep-punct`) is stricter. Pick one and stay consistent across a
  study.
- **This tool detects textual overlap.** Semantic contamination — the same
  question rephrased entirely — is out of scope here and always will be for an
  n-gram instrument. Do not claim more than the spore print shows.

---

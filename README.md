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


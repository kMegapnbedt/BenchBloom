# Examples

Two tiny corpora ship here so you can watch benchbloom flag contamination:

- `benchmark.jsonl` — 5 held-out benchmark items (the "reference").
- `training.jsonl` — 6 training documents (the "subject"). Items `t1`, `t2`,
  and `t5` deliberately paraphrase or copy benchmark items `b2`, `b4`, and `b1`.

## Exact Python scan (no compiler needed)

```bash
python -m benchbloom scan \
  --ref examples/benchmark.jsonl \
  --subject examples/training.jsonl \
  --field text --ngram 4 --threshold 0.3
```

You should see `b1`, `b2`, and `b4` flagged with high containment, and a
`verdict:` line printed to stderr.

## MinHash engine path (requires the C++ build)

```bash
# 1) build the engine
make            # or: bash cpp/build.sh

# 2) orchestrate normalize -> sign -> match through bloomdex
python -m benchbloom index \
  --ref examples/benchmark.jsonl \
  --subject examples/training.jsonl \
  --field text --k 128 --ngram 4 --threshold 0.4 \
  --out match.tsv

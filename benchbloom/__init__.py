"""benchbloom — benchmark contamination detector (Python orchestrator).

Pure standard library. Ingests JSONL/text corpora, normalizes records, and
either computes exact n-gram/Jaccard leakage reports in Python or delegates

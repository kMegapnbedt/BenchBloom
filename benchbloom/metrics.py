"""Leakage metrics for benchbloom (pure standard library).

Provides exact n-gram shingling and Jaccard/containment scoring used by the
Python-only path, plus helpers to summarize a leakage report. The C++ engine
gives an approximate (MinHash) answer at scale; these functions give the exact
answer for small-to-medium corpora and for verifying the estimator.
"""


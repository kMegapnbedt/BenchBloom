"""Leakage metrics for benchbloom (pure standard library).

Provides exact n-gram shingling and Jaccard/containment scoring used by the
Python-only path, plus helpers to summarize a leakage report. The C++ engine

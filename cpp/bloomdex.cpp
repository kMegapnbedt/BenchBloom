// bloomdex.cpp — benchbloom C++17 high-throughput shingle/MinHash index & overlap engine.
//
// The Python orchestrator (`benchbloom`) shells out to this binary to build
// MinHash-like signatures over token shingles and to score candidate overlap
// between a "reference" (benchmark) corpus and a "subject" (training) corpus.
//
// Design notes:
//   * No external libraries. Only the C++17 standard library.
//   * Streaming line-oriented I/O so multi-GB JSONL/text corpora stay bounded.
//   * A signature is K 64-bit min-hashes drawn from H universal hash seeds.
//   * Estimated Jaccard = (matching min-positions) / K.
//

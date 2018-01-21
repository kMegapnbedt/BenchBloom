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
// Subcommands:
//   sign   --input F --out F [--k 128] [--ngram 5] [--min-token 1]
//   match  --ref F --subject F --out F [--threshold 0.5] [--top 0]
//   self   --input F --out F [--threshold 0.8]   (near-duplicate detection)
//
// Signature file format (text, one record per line):
//   <id>\t<token_count>\t<h0> <h1> ... <h_{k-1}>
//
// Exit codes: 0 ok, 2 usage error, 3 I/O error.

#include <algorithm>
#include <array>
#include <cctype>

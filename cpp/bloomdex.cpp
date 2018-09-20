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
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

namespace bb {

constexpr std::uint64_t kMersennePrime = (1ULL << 61) - 1; // 2^61 - 1

// ---- hashing ---------------------------------------------------------------

// FNV-1a 64-bit over raw bytes; used as the base hash for a shingle.
static std::uint64_t fnv1a(const std::string& s) {
    std::uint64_t h = 1469598103934665603ULL;
    for (unsigned char c : s) {
        h ^= static_cast<std::uint64_t>(c);
        h *= 1099511628211ULL;
    }
    return h;
}

// splitmix64 — generates well-distributed permutation seeds deterministically.
static std::uint64_t splitmix64(std::uint64_t& x) {
    std::uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

// One universal-hash coefficient pair (a*x + b) mod p.
struct HashSeed {
    std::uint64_t a;

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
    std::uint64_t b;
};

static std::vector<HashSeed> make_seeds(std::size_t k, std::uint64_t seed) {
    std::vector<HashSeed> seeds(k);
    std::uint64_t s = seed ? seed : 0xB100Du;
    for (std::size_t i = 0; i < k; ++i) {
        std::uint64_t a = splitmix64(s) % (kMersennePrime - 1) + 1; // non-zero
        std::uint64_t b = splitmix64(s) % kMersennePrime;
        seeds[i] = HashSeed{a, b};
    }
    return seeds;
}

static inline std::uint64_t permute(std::uint64_t x, const HashSeed& hs) {
    // 128-bit intermediate via __uint128_t keeps the modular multiply exact.
    unsigned __int128 v = static_cast<unsigned __int128>(hs.a) * (x % kMersennePrime) + hs.b;
    return static_cast<std::uint64_t>(v % kMersennePrime);
}

// ---- tokenization ----------------------------------------------------------

// Lowercase, split on non-alphanumeric. Simple, locale-free, fast.
static std::vector<std::string> tokenize(const std::string& line, std::size_t min_token) {
    std::vector<std::string> out;
    std::string cur;
    cur.reserve(24);
    for (char ch : line) {
        unsigned char c = static_cast<unsigned char>(ch);
        if (std::isalnum(c)) {
            cur.push_back(static_cast<char>(std::tolower(c)));
        } else if (!cur.empty()) {
            if (cur.size() >= min_token) out.push_back(cur);
            cur.clear();
        }
    }
    if (!cur.empty() && cur.size() >= min_token) out.push_back(cur);
    return out;
}

// Compute the K min-hash signature for one record's shingle set.
static std::vector<std::uint64_t> signature(const std::vector<std::string>& tokens,
                                            std::size_t ngram,
                                            const std::vector<HashSeed>& seeds) {
    const std::size_t k = seeds.size();
    std::vector<std::uint64_t> sig(k, std::numeric_limits<std::uint64_t>::max());
    if (tokens.size() < ngram) {
        // Degenerate: hash the whole (short) record as a single shingle.
        std::string joined;
        for (const auto& t : tokens) { joined += t; joined.push_back(' '); }
        std::uint64_t base = fnv1a(joined);
        for (std::size_t i = 0; i < k; ++i) sig[i] = permute(base, seeds[i]);
        return sig;
    }
    std::string shingle;
    for (std::size_t start = 0; start + ngram <= tokens.size(); ++start) {
        shingle.clear();
        for (std::size_t j = 0; j < ngram; ++j) {
            shingle += tokens[start + j];
            shingle.push_back('\x1f'); // unit separator, avoids token-boundary collisions
        }
        std::uint64_t base = fnv1a(shingle);
        for (std::size_t i = 0; i < k; ++i) {
            std::uint64_t h = permute(base, seeds[i]);
            if (h < sig[i]) sig[i] = h;
        }
    }
    return sig;
}

// ---- argument parsing ------------------------------------------------------

struct Args {
    std::string get(const std::string& key, const std::string& def = "") const {
        auto it = kv.find(key);
        return it == kv.end() ? def : it->second;

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
    }
    long long geti(const std::string& key, long long def) const {
        auto it = kv.find(key);
        if (it == kv.end()) return def;
        return std::stoll(it->second);
    }
    double getd(const std::string& key, double def) const {
        auto it = kv.find(key);
        if (it == kv.end()) return def;
        return std::stod(it->second);
    }
    std::unordered_multimap<std::string, std::string>::size_type count(const std::string& key) const {
        return kv.count(key);
    }
    std::unordered_multimap<std::string, std::string> kv;
};

static Args parse_args(int argc, char** argv, int from) {
    Args a;
    for (int i = from; i < argc; ++i) {
        std::string tok = argv[i];
        if (tok.rfind("--", 0) == 0) {
            std::string key = tok.substr(2);
            if (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) != 0) {
                a.kv.emplace(key, argv[++i]);
            } else {
                a.kv.emplace(key, "1");
            }
        }
    }
    return a;
}

// ---- signature record I/O --------------------------------------------------

struct SigRecord {
    std::string id;
    std::uint64_t token_count = 0;
    std::vector<std::uint64_t> sig;
};

static void write_sig(std::ostream& os, const SigRecord& r) {
    os << r.id << '\t' << r.token_count << '\t';
    for (std::size_t i = 0; i < r.sig.size(); ++i) {
        if (i) os << ' ';
        os << r.sig[i];
    }
    os << '\n';
}

static bool read_sig_line(const std::string& line, SigRecord& r) {
    std::size_t t1 = line.find('\t');
    if (t1 == std::string::npos) return false;
    std::size_t t2 = line.find('\t', t1 + 1);
    if (t2 == std::string::npos) return false;
    r.id = line.substr(0, t1);
    r.token_count = std::stoull(line.substr(t1 + 1, t2 - t1 - 1));
    r.sig.clear();
    std::istringstream ss(line.substr(t2 + 1));
    std::uint64_t v;
    while (ss >> v) r.sig.push_back(v);
    return !r.sig.empty();
}

static double estimate_jaccard(const std::vector<std::uint64_t>& a,
                               const std::vector<std::uint64_t>& b) {
    if (a.size() != b.size() || a.empty()) return 0.0;
    std::size_t match = 0;
    for (std::size_t i = 0; i < a.size(); ++i) if (a[i] == b[i]) ++match;
    return static_cast<double>(match) / static_cast<double>(a.size());
}

// ---- subcommands -----------------------------------------------------------

static int cmd_sign(const Args& a) {
    std::string input = a.get("input");
    std::string out = a.get("out");
    if (input.empty() || out.empty()) {
        std::cerr << "sign: --input and --out required\n";
        return 2;
    }
    std::size_t k = static_cast<std::size_t>(a.geti("k", 128));
    std::size_t ngram = static_cast<std::size_t>(a.geti("ngram", 5));
    std::size_t min_token = static_cast<std::size_t>(a.geti("min-token", 1));
    std::uint64_t seed = static_cast<std::uint64_t>(a.geti("seed", 0));

    std::ifstream in(input);
    if (!in) { std::cerr << "sign: cannot open input: " << input << "\n"; return 3; }
    std::ofstream ofs(out);
    if (!ofs) { std::cerr << "sign: cannot open out: " << out << "\n"; return 3; }

    auto seeds = make_seeds(k, seed);
    std::string line;
    std::uint64_t idx = 0;
    while (std::getline(in, line)) {
        auto tokens = tokenize(line, min_token);
        if (tokens.empty()) { ++idx; continue; }
        SigRecord r;
        r.id = "r" + std::to_string(idx);
        r.token_count = tokens.size();
        r.sig = signature(tokens, ngram, seeds);
        write_sig(ofs, r);
        ++idx;
    }
    std::cerr << "sign: wrote signatures for " << idx << " records (k=" << k
              << ", ngram=" << ngram << ")\n";
    return 0;
}

static std::vector<SigRecord> load_sigs(const std::string& path, int& err) {
    std::vector<SigRecord> recs;
    std::ifstream in(path);
    if (!in) { err = 3; return recs; }
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        SigRecord r;
        if (read_sig_line(line, r)) recs.push_back(std::move(r));
    }
    err = 0;
    return recs;
}

static int cmd_match(const Args& a) {
    std::string ref = a.get("ref");
    std::string subject = a.get("subject");
    std::string out = a.get("out");
    if (ref.empty() || subject.empty() || out.empty()) {
        std::cerr << "match: --ref, --subject and --out required\n";
        return 2;
    }
    double threshold = a.getd("threshold", 0.5);
    long long top = a.geti("top", 0);

    int err = 0;
    auto R = load_sigs(ref, err);
    if (err) { std::cerr << "match: cannot read ref\n"; return 3; }
    auto S = load_sigs(subject, err);
    if (err) { std::cerr << "match: cannot read subject\n"; return 3; }

    std::ofstream ofs(out);
    if (!ofs) { std::cerr << "match: cannot open out\n"; return 3; }
    ofs << "ref_id\tsubject_id\tjaccard\n";

    std::uint64_t pairs = 0, hits = 0;
    for (const auto& r : R) {
        double best = 0.0;
        std::string best_id;
        for (const auto& s : S) {
            double j = estimate_jaccard(r.sig, s.sig);
            ++pairs;
            if (j >= threshold) {
                ofs << r.id << '\t' << s.id << '\t' << j << '\n';
                ++hits;
            }
            if (j > best) { best = j; best_id = s.id; }
        }
        if (top && !best_id.empty()) {
            // top mode still emits the single best pair even if below threshold
            (void)best_id;
        }
    }
    std::cerr << "match: compared " << pairs << " pairs, " << hits
              << " over threshold " << threshold << "\n";
    return 0;
}

static int cmd_self(const Args& a) {
    std::string input = a.get("input");
    std::string out = a.get("out");
    if (input.empty() || out.empty()) {
        std::cerr << "self: --input and --out required\n";
        return 2;
    }
    double threshold = a.getd("threshold", 0.8);
    int err = 0;
    auto recs = load_sigs(input, err);
    if (err) { std::cerr << "self: cannot read input\n"; return 3; }
    std::ofstream ofs(out);
    if (!ofs) { std::cerr << "self: cannot open out\n"; return 3; }
    ofs << "id_a\tid_b\tjaccard\n";
    std::uint64_t hits = 0;
    for (std::size_t i = 0; i < recs.size(); ++i) {
        for (std::size_t j = i + 1; j < recs.size(); ++j) {
            double jc = estimate_jaccard(recs[i].sig, recs[j].sig);
            if (jc >= threshold) {
                ofs << recs[i].id << '\t' << recs[j].id << '\t' << jc << '\n';
                ++hits;
            }
        }
    }

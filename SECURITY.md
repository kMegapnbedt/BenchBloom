# Security Policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private
[security advisory](https://github.com/kMegapnbedt/BenchBloom/security/advisories/new) form, or contact a
maintainer directly if the form is unavailable to you.

Include what an attacker gains in one sentence, the version or commit you are running, the smallest
reproduction you can manage, and whether the input is attacker-controlled in your setup. You should
get an acknowledgement within a few working days and a disclosure timeline before anything is
published.

## Scope

benchbloom normalizes untrusted corpora and renders match reports. Malformed JSONL,
oversized records, path handling in `--workdir`/`--out` and TSV report parsing are in
scope; the C++ engine parses files produced by the Python front end.

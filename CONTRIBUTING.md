# Contributing

Thanks for looking. A few things that make a change easy to take:

1. Open an issue first for anything larger than a bug fix, so we agree on the shape.
2. Keep the change focused - one behaviour per pull request.
3. Run the checks before opening the PR:
- `make` (builds `cpp/bloomdex`)
- `python -m benchbloom scan --ref examples/benchmark.jsonl --subject examples/training.jsonl`
4. Add a test for the behaviour you changed.
5. Match the surrounding style; the codebase is deliberately small and flat.
6. Dev tooling is pinned in `requirements-dev.txt`; bump pins deliberately.

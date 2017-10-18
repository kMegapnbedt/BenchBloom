"""Orchestration bridge to the C++ `bloomdex` engine.

Locates or falls back gracefully when the compiled binary is unavailable, and
wraps the `sign` / `match` / `self` subcommands with subprocess calls plus
parsing of the tab-separated report files they emit.
"""

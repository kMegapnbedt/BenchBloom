#!/usr/bin/env bash
# Build the bloomdex C++17 engine with clang++ or g++ (no CMake required).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/bloomdex.cpp"
OUT="$HERE/bloomdex"


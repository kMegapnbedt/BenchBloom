#!/usr/bin/env bash
# Build the bloomdex C++17 engine with clang++ or g++ (no CMake required).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/bloomdex.cpp"
OUT="$HERE/bloomdex"

CXX="${CXX:-}"
if [ -z "$CXX" ]; then
    if command -v clang++ >/dev/null 2>&1; then CXX=clang++
    elif command -v g++ >/dev/null 2>&1; then CXX=g++
    else echo "error: no clang++ or g++ found on PATH" >&2; exit 1
    fi
fi

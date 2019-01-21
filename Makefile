# benchbloom / bloomdex — direct compiler build, no CMake.
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -pedantic
SRC      := cpp/bloomdex.cpp
BIN      := cpp/bloomdex


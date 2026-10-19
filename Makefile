# benchbloom / bloomdex — direct compiler build, no CMake.
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -pedantic
SRC      := cpp/bloomdex.cpp
BIN      := cpp/bloomdex

.PHONY: all clean check

all: $(BIN)

$(BIN): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(BIN)

check: all
	python -m compileall -q benchbloom
	python -m benchbloom scan --ref examples/benchmark.jsonl \
		--subject examples/training.jsonl > /dev/null

clean:
	rm -f $(BIN) $(BIN).exe

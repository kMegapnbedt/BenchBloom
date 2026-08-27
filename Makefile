# benchbloom / bloomdex — direct compiler build, no CMake.
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -pedantic
SRC      := cpp/bloomdex.cpp
BIN      := cpp/bloomdex

.PHONY: all clean

all: $(BIN)

$(BIN): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(BIN)

clean:
	rm -f $(BIN) $(BIN).exe

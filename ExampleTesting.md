API Simulator - complex C++ codebase for testing memory-checkers

Build (simple):
  g++ -std=c++17 -pthread src/*.cpp -O0 -g -o api_simulator

Run:
  ./api_simulator

What it does:
  - Simulates 1000 "API calls" concurrently using a thread pool and futures.
  - Produces intentional memory issues (leaks, double frees, shared_ptr cycles, small use-after-free) to test a simplified valgrind-like checker.

Notes:
  - This is purely local and simulates endpoints; there is no real network activity.
  - Compile with debug symbols (-g) and no optimizations (-O0) if you want valgrind/simple_checker to detect issues more reliably.


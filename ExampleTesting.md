# API Simulator - complex C++ codebase for testing memory-checkers

Build (simple):
```bash
g++ -std=c++17 -pthread src/*.cpp -O0 -g -o api_simulator
```

Run:
```bash
./api_simulator
```

## What it does:
- Simulates 1000 "API calls" concurrently using a thread pool and futures.
- Produces intentional memory issues (leaks, double frees, shared_ptr cycles, small use-after-free) to test a simplified valgrind-like checker.

## Notes:
- This is purely local and simulates endpoints; there is no real network activity.
- Compile with debug symbols (-g) and no optimizations (-O0) if you want valgrind/simple_checker to detect issues more reliably.

---

**Note:** This is part of the Simple_Checker project and is used to test the memory analysis capabilities with a complex, multi-threaded C++ application.

#pragma once
#include <string>
#include <memory>
#include <functional>
#include <chrono>
#include <random>

struct HttpResponse {
    int status;
    std::string body;
    // intentionally hold a raw buffer pointer for simulation
    char* raw_payload = nullptr;
    size_t raw_size = 0;
};

class HttpSimulator {
public:
    HttpSimulator();
    ~HttpSimulator();

    // simulate an API call to `endpoint` with payload size `payload_size`
    // `danger_level` controls whether call will attempt problematic behavior
    HttpResponse call(const std::string& endpoint, size_t payload_size, int danger_level = 0);

    // helpers for intentional leak/double-free etc.
    void intentionally_leak_raw_buffer(size_t size);
    void cause_double_delete();
    void create_shared_cycle();

private:
    std::mt19937_64 rng_;
    std::uniform_int_distribution<int> status_dist_;
    // keep a vector that will hold leaked pointers sometimes
    std::vector<char*> leak_store_;
    // holder to create a shared_ptr cycle
    std::shared_ptr<int> cycle_holder_a_;
    std::shared_ptr<int> cycle_holder_b_;
};


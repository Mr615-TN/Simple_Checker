#include "http_simulator.h"
#include <thread>
#include <sstream>
#include <cstring>
#include <iostream>
#include <memory>

HttpSimulator::HttpSimulator()
: rng_(std::random_device{}()), status_dist_(200, 599) {
}

HttpSimulator::~HttpSimulator() {
    // intentionally *not* freeing leak_store_ contents so destructor reveals leaks
    // but we will free some occasionally in calls to vary behaviour
    // cleanup a little to avoid catastrophic OS-level leaks in long-running runs
    for (auto p : leak_store_) {
        // intentionally comment out to keep leaks for testing
        // delete[] p;
        (void)p;
    }
}

void HttpSimulator::intentionally_leak_raw_buffer(size_t size) {
    char* p = new char[size];
    // scribble some data
    memset(p, 0xAB, size);
    leak_store_.push_back(p); // kept forever to leak
}

void HttpSimulator::cause_double_delete() {
    // allocate a small buffer and delete it twice (undefined behavior)
    char* p = new char[32];
    memset(p, 0xCD, 32);
    delete[] p;
    // OOPS: double delete
    delete[] p;
}

void HttpSimulator::create_shared_cycle() {
    // create two shared_ptrs that reference each other -> leak via cycle
    struct Node {
        std::shared_ptr<Node> other;
        int val;
    };
    auto a = std::make_shared<Node>();
    auto b = std::make_shared<Node>();
    a->val = 1; b->val = 2;
    a->other = b;
    b->other = a;
    // intentionally store one in members so it persists beyond scope
    cycle_holder_a_ = std::reinterpret_pointer_cast<int>(a);
    cycle_holder_b_ = std::reinterpret_pointer_cast<int>(b);
    // reinterpret cast is intentionally sketchy to simulate misuse
}

HttpResponse HttpSimulator::call(const std::string& endpoint, size_t payload_size, int danger_level) {
    // simulate variable latency
    std::uniform_int_distribution<int> delay_ms(5, 200);
    int d = delay_ms(rng_);
    std::this_thread::sleep_for(std::chrono::milliseconds(d));

    HttpResponse resp;
    resp.status = status_dist_(rng_);
    // craft body
    std::ostringstream ss;
    ss << "{ \"endpoint\":\"" << endpoint << "\", \"size\":" << payload_size << ", \"sim_delay_ms\":" << d << " }";
    std::string body = ss.str();
    resp.body = body;

    // allocate raw payload buffer to mimic library-managed buffer
    resp.raw_size = body.size() + 1;
    resp.raw_payload = new char[resp.raw_size];
    memcpy(resp.raw_payload, body.c_str(), resp.raw_size);

    // introduce controlled problematic behaviors depending on danger_level
    if (danger_level == 1) {
        // leak a raw buffer
        intentionally_leak_raw_buffer(payload_size > 0 ? payload_size : 64);
    } else if (danger_level == 2) {
        // double delete
        cause_double_delete();
    } else if (danger_level == 3) {
        // create shared_ptr cycle -> leak for leak detectors that don't break cycles
        create_shared_cycle();
    } else if (danger_level == 4) {
        // small use-after-free: free payload immediately and return pointer to freed memory
        delete[] resp.raw_payload;
        // store dangling pointer in resp (dangerous)
        resp.raw_payload = reinterpret_cast<char*>(0x1); // obviously invalid pointer to provoke detectors
    }

    return resp;
}


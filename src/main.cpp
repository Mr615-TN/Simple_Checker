#include <iostream>
#include <vector>
#include <atomic>
#include <chrono>
#include <sstream>
#include <memory>
#include <random>
#include <cstring>

#include "thread_pool.h"
#include "http_simulator.h"
#include "leaky_cache.h"

int main(int argc, char** argv) {
    const size_t NUM_CALLS = 1000;
    const size_t THREADS = 16;
    const size_t MAX_PAYLOAD = 8 * 1024; // up to 8 KB
    ThreadPool pool(THREADS);
    HttpSimulator sim;
    LeakyCache cache;

    std::atomic<size_t> completed{0};
    std::vector<std::future<void>> futures;
    futures.reserve(NUM_CALLS);

    std::mt19937_64 rng((unsigned)std::chrono::high_resolution_clock::now().time_since_epoch().count());
    std::uniform_int_distribution<int> danger_dist(0, 10);
    std::uniform_int_distribution<size_t> size_dist(16, MAX_PAYLOAD);

    std::cout << "Simulating " << NUM_CALLS << " API calls across " << THREADS << " worker threads...\n";

    for (size_t i = 0; i < NUM_CALLS; ++i) {
        std::string endpoint = "/api/resource/" + std::to_string(i % 50);

        // pick payload and danger level
        size_t payload_size = size_dist(rng);
        int dd = danger_dist(rng);
        int danger_level = 0;
        if (dd == 1) danger_level = 1; // leak raw
        else if (dd == 2) danger_level = 2; // double delete
        else if (dd == 3) danger_level = 3; // shared_ptr cycle
        else if (dd == 4) danger_level = 4; // use-after-free style

        // submit task
        futures.emplace_back(pool.submit([&, endpoint, payload_size, danger_level, i]() {
            try {
                // lazy create a payload stored in cache
                auto payload = std::make_shared<std::string>(payload_size, 'x');
                cache.put(endpoint + ":" + std::to_string(i), payload);

                // occasionally retain forever to leak
                if ((i % 97) == 0) cache.retain_forever(payload);

                // call simulated API
                HttpResponse r = sim.call(endpoint, payload_size, danger_level);

                // process response: copy body into a new allocation then free (normal behavior)
                char* proc_buf = new char[r.raw_size + 8];
                if (r.raw_payload && r.raw_size > 0) {
                    // risk of use-after-free if r.raw_payload invalid – calculate carefully
                    // protect with try/catch to avoid crash (though UB may still crash)
                    try {
                        memcpy(proc_buf, r.raw_payload, std::min(r.raw_size, r.raw_size + 0));
                    } catch (...) {
                        // ignore
                    }
                }
                // free proc_buf normally
                delete[] proc_buf;

                // free r.raw_payload unless it was intentionally left dangling
                if (danger_level != 4 && r.raw_payload) delete[] r.raw_payload;
                // else if danger_level==4: the simulator already deleted it or replaced it with invalid pointer

                // small chance to trigger cache purge
                if ((i % 13) == 0) cache.maybe_purge();

            } catch (const std::exception& ex) {
                std::cerr << "task exception: " << ex.what() << "\n";
            } catch (...) {
                std::cerr << "task unknown exception\n";
            }
            ++completed;
            if (completed % 100 == 0) {
                std::cout << "[progress] completed " << completed << " calls\n";
            }
        }));
    }

    // wait for all tasks to finish
    for (auto &f : futures) {
        try {
            f.get();
        } catch (...) {
            // swallow
        }
    }

    std::cout << "All tasks submitted: completed = " << completed.load() << "\n";

    // create a short-lived shared_ptr cycle in main to leave a leak for detectors
    {
        struct Node { std::shared_ptr<Node> other; int v; };
        auto a = std::make_shared<Node>(); auto b = std::make_shared<Node>();
        a->v = 10; b->v = 20;
        a->other = b; b->other = a;
        // intentionally not breaking cycle
    }

    std::cout << "Exiting main; destructors will run. Intentionally some memory will remain leaked for testing.\n";
    return 0;
}


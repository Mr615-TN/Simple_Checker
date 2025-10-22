#include "leaky_cache.h"
#include <iostream>

LeakyCache::~LeakyCache() {
    // intentionally leave store_ as-is to keep objects alive across destructor to simulate leak
    // but print sizes so you see memory retention
    std::unique_lock<std::mutex> lk(m_);
    std::cerr << "[LeakyCache] destructor: store size = " << store_.size()
              << ", retained = " << retained_.size() << "\n";
}

void LeakyCache::put(const std::string& key, std::shared_ptr<std::string> payload) {
    std::unique_lock<std::mutex> lk(m_);
    store_[key] = payload;
}

void LeakyCache::maybe_purge() {
    std::unique_lock<std::mutex> lk(m_);
    // purge small fraction to create intermittent frees
    if (store_.empty()) return;
    auto it = store_.begin();
    for (int i = 0; i < 3 && it != store_.end(); ++i) {
        it = store_.erase(it);
    }
}

void LeakyCache::retain_forever(std::shared_ptr<std::string> p) {
    std::unique_lock<std::mutex> lk(m_);
    retained_.push_back(p); // intentionally never cleared
}


#pragma once
#include <string>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <vector>
// A "cache" that intentionally holds onto objects (leaks) unless explicitly cleared.
// Also demonstrates a place where shared_ptr cycles can hide leaks.

class LeakyCache {
public:
    LeakyCache() = default;
    ~LeakyCache();

    // store payload indexed by a key
    void put(const std::string& key, std::shared_ptr<std::string> payload);

    // occasionally purge small number
    void maybe_purge();

    // intentionally never purge to create retained memory
    void retain_forever(std::shared_ptr<std::string> p);

private:
    std::unordered_map<std::string, std::shared_ptr<std::string>> store_;
    std::vector<std::shared_ptr<std::string>> retained_;
    std::mutex m_;
};


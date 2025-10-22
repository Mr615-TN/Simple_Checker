#pragma once
#include <vector>
#include <thread>
#include <queue>
#include <functional>
#include <future>
#include <mutex>
#include <condition_variable>
#include <atomic>

class ThreadPool {
public:
    ThreadPool(size_t n = std::thread::hardware_concurrency()) : stop_(false) {
        for (size_t i = 0; i < n; ++i) workers_.emplace_back([this]{ this->worker(); });
    }
    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lk(m_);
            stop_ = true;
        }
        cv_.notify_all();
        for (auto &t : workers_) if (t.joinable()) t.join();
    }

    template<typename F, typename... Args>
    auto submit(F&& f, Args&&... args) -> std::future<typename std::result_of<F(Args...)>::type> {
        using R = typename std::result_of<F(Args...)>::type;
        auto task = std::make_shared<std::packaged_task<R()>>(std::bind(std::forward<F>(f), std::forward<Args>(args)...));
        std::future<R> fut = task->get_future();
        {
            std::unique_lock<std::mutex> lk(m_);
            queue_.push([task](){ (*task)(); });
        }
        cv_.notify_one();
        return fut;
    }

private:
    void worker() {
        while (true) {
            std::function<void()> job;
            {
                std::unique_lock<std::mutex> lk(m_);
                cv_.wait(lk, [this]{ return stop_ || !queue_.empty(); });
                if (stop_ && queue_.empty()) return;
                job = std::move(queue_.front());
                queue_.pop();
            }
            try {
                job();
            } catch (...) {
                // swallow
            }
        }
    }

    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> queue_;
    std::mutex m_;
    std::condition_variable cv_;
    bool stop_;
};


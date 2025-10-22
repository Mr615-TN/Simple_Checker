cmake_minimum_required(VERSION 3.8)
project(api_simulator)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(SRC
    src/main.cpp
    src/http_simulator.cpp
    src/leaky_cache.cpp
)
add_executable(api_simulator ${SRC})


cmake_minimum_required(VERSION 3.14)
project(cli_football_matches CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Using FetchContent to download dependencies
include(FetchContent)

# 1. cpr (C++ Requests)
FetchContent_Declare(
    cpr
    GIT_REPOSITORY https://github.com/libcpr/cpr.git
    GIT_TAG        1.10.5
)
set(CPR_USE_SYSTEM_CURL OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(cpr)

# 2. nlohmann/json
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.3
)
FetchContent_MakeAvailable(nlohmann_json)

# Add executable
add_executable(clifc src/main.cpp)

# Link libraries
target_link_libraries(clifc PRIVATE cpr::cpr nlohmann_json::nlohmann_json)

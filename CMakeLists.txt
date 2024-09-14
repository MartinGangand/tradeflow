cmake_minimum_required(VERSION 3.10)

project(tradeflow VERSION 0.0.14)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

if (MSVC)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wshadow -Wpedantic)
endif()

add_subdirectory(lib/cpp/tradeflow)

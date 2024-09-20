cmake_minimum_required(VERSION 3.10)

project(tradeflow)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

set(MY_PROJECT_SOURCE_DIR ${PROJECT_SOURCE_DIR} CACHE PATH "Source directory of the project")

if (MSVC)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wshadow -Wpedantic)
endif()

add_subdirectory(lib/cpp/tradeflow)

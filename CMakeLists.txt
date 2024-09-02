# Specify the minimum version of CMake required
cmake_minimum_required(VERSION 3.10)

# Set the project name and version
project(tradeflow VERSION 0.0.12.1 LANGUAGES CXX)

# Set the C++ standard to be used
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add the source file
add_library(tradeflow SHARED lib/cpp/tradeflow/simulation.cppp)

# Specify the output directory for the shared library
set_target_properties(tradeflow PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/tradeflow
        RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_SOURCE_DIR}/tradeflow
)

set_target_properties(tradeflow PROPERTIES PREFIX "")

# Set the appropriate compiler flags
if(MSVC)
    # Windows specific flags
    target_compile_options(tradeflow PRIVATE /Wall)
else()
    # Unix (Linux, macOS) specific flags
    target_compile_options(tradeflow PRIVATE -Wall -Wextra -fPIC)
endif()

set_target_properties(tradeflow PROPERTIES
        OUTPUT_NAME "libtradeflow"
)

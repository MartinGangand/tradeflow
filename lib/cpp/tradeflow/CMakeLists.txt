# Specify the minimum version of CMake required
cmake_minimum_required(VERSION 3.10)

# Set the project name and version
project(tradeflow VERSION 0.0.12.1 LANGUAGES CXX)

# Set the C++ standard to be used
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
if(WIN32)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
endif()

# Add the source file
add_library(tradeflow SHARED simulation.cpp)

# Specify the output directory for the shared library (${CMAKE_SOURCE_DIR}/../../../tradeflow)
set_target_properties(tradeflow PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY_DEBUG "${RUNTIME_OUTPUT_DIRECTORY_DEBUG}"
        PREFIX ""
        OUTPUT_NAME "libtradeflow"
)

message("111111111___CMAKE: ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")
message("22222222: ${RUNTIME_OUTPUT_DIRECTORY_DEBUG}")
message("=====LIBRARY_OUTPUT_DIRECTORY=====: ${CMAKE_BUILD_TYPE} => ${CMAKE_RUNTIME_OUTPUT_DIRECTORY} ..... ${CMAKE_LIBRARY_OUTPUT_DIRECTORY} ..... ${LIBRARY_OUTPUT_DIRECTORY}")

# Set the appropriate compiler flags
if(MSVC)
    # Windows specific flags
    target_compile_options(tradeflow PRIVATE /Wall)
else()
    # Unix (Linux, macOS) specific flags
    target_compile_options(tradeflow PRIVATE -Wall -Wextra -fPIC)
endif()

set(OUTPUT_DIRECTORY_TRADEFLOW "${MY_PROJECT_SOURCE_DIR}/tradeflow" CACHE PATH "Output directory for the tradeflow shared library")

add_library(libtradeflow SHARED simulation.cpp)

target_include_directories(libtradeflow PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

set_target_properties(libtradeflow PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${OUTPUT_DIRECTORY_TRADEFLOW}"
        RUNTIME_OUTPUT_DIRECTORY_DEBUG "${OUTPUT_DIRECTORY_TRADEFLOW}"
        RUNTIME_OUTPUT_DIRECTORY_RELEASE "${OUTPUT_DIRECTORY_TRADEFLOW}"
        PREFIX ""
)

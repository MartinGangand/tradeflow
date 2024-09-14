set(OutputDirectory "${PROJECT_SOURCE_DIR}/tradeflow")

add_library(libtradeflow SHARED simulation.cpp)

target_include_directories(libtradeflow PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

set_target_properties(libtradeflow PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${OutputDirectory}"
        RUNTIME_OUTPUT_DIRECTORY_DEBUG "${OutputDirectory}"
        PREFIX ""
)

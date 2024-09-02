#pragma once

#if defined(_MSC_VER)
    #define EXPORT __declspec(dllexport) // Microsoft
#elif defined(__GNUC__)
    #define EXPORT __attribute__((visibility("default"))) // GCC
#else
    #define EXPORT // Most compilers export all the symbols by default.
    #pragma warning Unknown dynamic link import/export semantics.
#endif

extern "C" {
    EXPORT void simulate(int size, const double* inverted_params_ptr, double constant_parameter, int nb_params, int* last_signs_ptr, int seed, int* res);
}

#pragma once

#if defined(_MSC_VER)
    #define EXPORT __declspec(dllexport)
#elif defined(__GNUC__)
    #define EXPORT __attribute__((visibility("default")))
#else
    #define EXPORT
    #pragma warning Unknown dynamic link export semantics.
#endif

extern "C" {
    EXPORT void simulate(int size, const double* inverted_params_ptr, double constant_parameter, int nb_params, int* last_signs_ptr, int seed, int* res);
}

#pragma once

extern "C" {
    void simulate(int size, const double* inverted_params_ptr, double constant_parameter, int nb_params, int* last_signs_ptr, int seed, int* res);
}

#include <algorithm>
#include <numeric>
#include <random>

using namespace std;

vector<double> generate_uniforms(const int size, const int seed) {
    mt19937 gen(seed);
    uniform_real_distribution unif(0.0, 1.0);
    vector<double> uniforms;
    uniforms.reserve(size);
    for (int i = 0; i < size; i++) {
        uniforms.push_back(unif(gen));
    }
    return uniforms;
}

template <typename T>
void rotate_left_by_1(vector<T>& vect, const T new_el) {
    rotate(vect.begin(), vect.begin() + 1, vect.end());
    vect.at(vect.size() - 1) = new_el;
}

vector<int> simulate(const int size, const int seed, const vector<double>& inverted_params, const double constant_parameter, vector<int>& last_signs) {
    const size_t nb_params = inverted_params.size();
    const vector<double> uniforms = generate_uniforms(size, seed);
    vector<int> simulation;
    simulation.reserve(size);
    int next_sign;
    for (int i = 0; i < size; i++) {
        const double next_sign_expected_value = inner_product(last_signs.begin(), last_signs.end(),
                                                              inverted_params.begin(), constant_parameter);
        if (const double next_sign_buy_proba = 0.5 * (1 + next_sign_expected_value);uniforms.at(i) < next_sign_buy_proba) {
            next_sign = 1;
        } else {
            next_sign = -1;
        }
        simulation.push_back(next_sign);
        rotate_left_by_1(last_signs, next_sign);
        last_signs[nb_params - 1] = next_sign;
    }
    return simulation;
}

#if defined(_MSC_VER)
#define EXPORT __declspec(dllexport) // Microsoft
#elif defined(__GNUC__)
#define EXPORT __attribute__((visibility("default"))) // GCC
#else
#define EXPORT // Most compilers export all the symbols by default. We hope for the best here.
#pragma warning Unknown dynamic link import/export semantics.
#endif

extern "C" {
    EXPORT void my_simulate(const int size, const int seed, const double* inverted_params, const double constant_parameter, const int nb_params, int* last_signs, int* res) {
        auto last_signs_vec = vector(last_signs, last_signs + nb_params);
        const auto inverted_params_vect = vector(inverted_params, inverted_params + nb_params);
        vector<int> simulation = simulate(size, seed, inverted_params_vect, constant_parameter, last_signs_vec);
        copy(simulation.begin(), simulation.end(), res);
    }
}
#include "simulation.h"

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
void rotate_left_by_1(vector<T>& vect, const T new_far_right_value) {
    rotate(vect.begin(), vect.begin() + 1, vect.end());
    vect.at(vect.size() - 1) = new_far_right_value;
}

void simulate(const int size, const double* inverted_params_ptr, const double constant_parameter, const int nb_params, int* last_signs_ptr, const int seed, int* res) {
    vector<int> last_signs = vector(last_signs_ptr, last_signs_ptr + nb_params);
    const vector<double> inverted_params = vector(inverted_params_ptr, inverted_params_ptr + nb_params);

    const vector<double> uniforms = generate_uniforms(size, seed);
    vector<int> simulation;
    simulation.reserve(size);
    int next_sign;
    for (int i = 0; i < size; i++) {
        const double next_sign_expected_value = inner_product(last_signs.begin(), last_signs.end(),
                                                              inverted_params.begin(), constant_parameter);
        if (const double next_sign_buy_proba = 0.5 * (1 + next_sign_expected_value); uniforms.at(i) < next_sign_buy_proba) {
            next_sign = 1;
        } else {
            next_sign = -1;
        }
        simulation.push_back(next_sign);
        rotate_left_by_1(last_signs, next_sign);
    }

    copy(simulation.begin(), simulation.end(), res);
}

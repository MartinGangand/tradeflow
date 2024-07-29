#include <iostream>
#include <list>
#include <numeric>
// #include <__random/random_device.h>
#include <random>

using namespace std;

vector<double> generate_uniforms(const int size, const int seed) {
    // random_device rd; gen(rd());
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
void print_vector(const vector<T>& vect) {
    if (!vect.empty()) {
        cout << "[ ";
        for (const auto v : vect) {
            cout << v << " ";
        }
        cout << "]" << endl;
    } else {
        cout << "EMPTY ARRAY" << endl;
    }
}

template <typename T>
void rotate_left_by_1(vector<T>& vect, const T new_el) {
    rotate(vect.begin(), vect.begin() + 1, vect.end());
    vect.at(vect.size() - 1) = new_el;
}

vector<int> simulate_from_unifs(const vector<double>& uniforms, const vector<double>& inverted_params, const double constant_parameter, vector<int>& last_signs, const int nb_params, const int size) {
    vector<int> simulation;
    simulation.reserve(size);
    int next_sign;
    for (int i = 0; i < size; i++) {
        const double next_sign_expected_value = inner_product(last_signs.begin(), last_signs.end(), inverted_params.begin(), constant_parameter);
        const double next_sign_buy_proba = 0.5 * (1 + next_sign_expected_value);
        if (uniforms.at(i) < next_sign_buy_proba) {
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

vector<int> simulate(const int size, const int seed, const vector<double>& inverted_params, const double constant_parameter, vector<int>& last_signs, const int nb_params) {
    const vector<double> uniforms = generate_uniforms(size, seed);
    return simulate_from_unifs(uniforms, inverted_params, constant_parameter, last_signs, nb_params, size);
}


extern "C" {
    void my_simulate_from_unifs(const double* uniforms, const double* inverted_params, const double constant_parameter, int* last_signs, const int nb_params, const int size, int* res) {
        const vector<double> uniforms_vect(uniforms, uniforms + size);
        vector<int> last_signs_vect(last_signs, last_signs + nb_params);
        const vector<double> inverted_params_vect(inverted_params, inverted_params + nb_params);
        vector<int> simulation = simulate_from_unifs(uniforms_vect, inverted_params_vect, constant_parameter, last_signs_vect, nb_params, size);
        copy(simulation.begin(), simulation.end(), res);
    }

    void my_simulate(const int size, const int seed, const double* inverted_params, const double constant_parameter, int* last_signs, const int nb_params, int* res) {
        vector<int> last_signs_vect(last_signs, last_signs + nb_params);
        const vector<double> inverted_params_vect(inverted_params, inverted_params + nb_params);
        vector<int> simulation = simulate(size, seed, inverted_params_vect, constant_parameter, last_signs_vect, nb_params);
        copy(simulation.begin(), simulation.end(), res);
    }
}

void run_simulate() {
    constexpr int size = 50;
    const vector<double> inverted_params = {0.07896963, 0.12228963, 0.10762269, 0.0832857, 0.15625334, 0.2079367};
    vector<int> last_signs = {-1, 1, 1, -1, -1, -1};

    constexpr double uniforms[] = {0.417022004702574, 0.7203244934421581, 0.00011437481734488664, 0.30233257263183977, 0.14675589081711304, 0.0923385947687978, 0.1862602113776709, 0.34556072704304774, 0.39676747423066994, 0.538816734003357, 0.4191945144032948, 0.6852195003967595, 0.20445224973151743, 0.8781174363909454, 0.027387593197926163, 0.6704675101784022, 0.41730480236712697, 0.5586898284457517, 0.14038693859523377, 0.1981014890848788, 0.8007445686755367, 0.9682615757193975, 0.31342417815924284, 0.6923226156693141, 0.8763891522960383, 0.8946066635038473, 0.08504421136977791, 0.03905478323288236, 0.1698304195645689, 0.8781425034294131, 0.0983468338330501, 0.42110762500505217, 0.9578895301505019, 0.5331652849730171, 0.6918771139504734, 0.31551563100606295, 0.6865009276815837, 0.8346256718973729, 0.018288277344191806, 0.7501443149449675, 0.9888610889064947, 0.7481656543798394, 0.2804439920644052, 0.7892793284514885, 0.10322600657764203, 0.44789352617590517, 0.9085955030930956, 0.2936141483736795, 0.28777533858634874, 0.13002857211827767};
    const vector<int> simulation1 = simulate_from_unifs(vector<double>(uniforms, uniforms + 50), inverted_params, 0, last_signs, 6, 50);
    print_vector(simulation1);
    cout << "Sell idx: [";
    for (int i = 0; i < size; i++) {
        if (simulation1.at(i) == -1) {
            cout << i << " ";
        }
    }
    cout << "]" << endl;

    // python: 0 1 21 24 25 29 32 34 36 37 39 40 41 42 43 45 46 47 48
    // c++:    0 1 21 24 25 29 32 34 36 37 39 40 41 42 43 45 46 47 48

    const vector<double> unifs = generate_uniforms(10, 1);
    print_vector(unifs);

    const vector<int> simulation2 = simulate(size, 1, inverted_params, 0, last_signs, 6);
    print_vector(simulation2);
}

int main() {
    run_simulate();
    // run_simulate_p();
    return 0;
}

#include <iostream>

using namespace std;

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

void run_simulate() {
    constexpr int size = 50;
    const vector inverted_params = {0.07896963, 0.12228963, 0.10762269, 0.0832857, 0.15625334, 0.2079367};
    vector last_signs = {-1, 1, 1, -1, -1, -1};

    const vector<int> simulation2 = simulate(size, 1, inverted_params, 0, last_signs, 6);
    print_vector(simulation2);
}

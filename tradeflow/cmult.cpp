using namespace std;

double expected_value_to_proba(double expected_value) {
    return 0.5 * (1 + expected_value);
}

extern "C" {
    double my_expected_value_to_proba(double expected_value) {
        return expected_value_to_proba(expected_value);
    } 
}

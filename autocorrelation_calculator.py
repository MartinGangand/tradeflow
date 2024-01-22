import numpy as np

def autocorrelation_convolution(x, nb_lags=None, mode="full"):
    result = np.correlate(x, x, mode=mode)
    if (nb_lags is not None):
        return result[result.size // 2:][:nb_lags + 1] / float(result.max())
    else:
        return result[result.size // 2:] / float(result.max())
    
def autocorrelation_lag_k_convolution(x, k):
    assert(k < len(x))

    autocorrelation_lag_k_coeff = 0
    for i in range(len(x) - k):
        autocorrelation_lag_k_coeff += (x[i] * x[i + k])
    return autocorrelation_lag_k_coeff

def autocorrelation_convolution_perso(x, nb_lags=None):
    assert(nb_lags is None or nb_lags < len(x))
    autocorrelation_coeffs = []
    range_upper_bound = (nb_lags + 1) if nb_lags is not None else len(x)
    for k in range(range_upper_bound):
        current_autocorrelation_coeff = autocorrelation_lag_k_convolution(x, k)
        autocorrelation_coeffs.append(current_autocorrelation_coeff)
    
    autocorrelation_coeffs = np.array(autocorrelation_coeffs)
    return np.array(autocorrelation_coeffs) / float(autocorrelation_coeffs.max())

def nornalized_autocorrelation(signs, nb_lags=None):
    if (nb_lags is None):
        autocorrelation_coeffs = autocorrelation_convolution(signs)
    else:
        autocorrelation_coeffs = autocorrelation_convolution_perso(signs, nb_lags)
    
    first_idx_negative = len(autocorrelation_coeffs)
    for i, coeff in enumerate(autocorrelation_coeffs):
        if (coeff < 0):
            first_idx_negative = i
            break
    autocorrelation_coeffs = autocorrelation_coeffs[:first_idx_negative]
    print(f"First negative index: {first_idx_negative}")

    autocorrelation_coeffs = autocorrelation_coeffs[1:]
    nornalized_autocorrelation_coeffs = autocorrelation_coeffs / np.sum(autocorrelation_coeffs)
    nornalized_autocorrelation_coeffs[-1] = 1 - np.sum(nornalized_autocorrelation_coeffs[:-1])

    assert(coeff >= 0 for coeff in nornalized_autocorrelation_coeffs)
    assert(np.sum(nornalized_autocorrelation_coeffs) >= 0.999 and np.sum(nornalized_autocorrelation_coeffs) <= 1.001)
    return nornalized_autocorrelation_coeffs

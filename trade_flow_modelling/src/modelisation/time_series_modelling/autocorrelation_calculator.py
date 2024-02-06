import numpy as np

print("AUTOCORRELATION")

def autocorrelation_np(x, nb_lags=None):
    result = np.correlate(x, x, mode="full")
    if (nb_lags is not None):
        return result[result.size // 2:][:nb_lags + 1] / float(result.max())
    else:
        return result[result.size // 2:] / float(result.max())

def autocorrelation_convolution_perso(x, nb_lags=None):
    assert(nb_lags is None or nb_lags < len(x))
    autocorrelation_coeffs = []
    range_upper_bound = (nb_lags + 1) if nb_lags is not None else len(x)
    for k in range(range_upper_bound):
        current_autocorrelation_coeff = autocorrelation_lag_k_convolution(x, k)
        autocorrelation_coeffs.append(current_autocorrelation_coeff)
    
    autocorrelation_coeffs = np.array(autocorrelation_coeffs)
    return np.array(autocorrelation_coeffs) / float(autocorrelation_coeffs.max())

def autocorrelation_lag_k_convolution(x, k):
    assert(k < len(x))
    autocorrelation_lag_k_coeff = 0
    for i in range(len(x) - k):
        autocorrelation_lag_k_coeff += (x[i] * x[i + k])
    return autocorrelation_lag_k_coeff

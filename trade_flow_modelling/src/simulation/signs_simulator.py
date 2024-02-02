from statsmodels.tsa.ar_model import AutoReg
import numpy as np

from trade_flow_modelling.src.modelling import time_series
import utils

def simulate_signs(training_signs, nb_signs_to_simulate, nb_lags=None, verbose=False):
    # start_select_order = time.time()
    nb_lags = nb_lags if (nb_lags is not None) else time_series.select_appropriate_nb_lags(training_signs)
    # end_select_order = time.time()
    # time_select_order = np.round(end_select_order - start_select_order, settings.PRECISION)

    is_stationary = time_series.is_time_series_stationary(training_signs, max_lag=nb_lags)
    utils.check_condition(is_stationary, Exception("The time series must be stationary in order to simulate signs"))

    # start_model_fit = time.time()
    ar_model = AutoReg(training_signs, lags=nb_lags, trend="c").fit()
    # end_model_fit = time.time()
    # time_model_fit = np.round(end_model_fit - start_model_fit, settings.PRECISION)

    # start_sign_simulation = time.time()
    simulated_signs = simulate_n_signs_from_fitted_params(nb_signs_to_simulate, ar_model.params, training_signs)
    # end_sign_simulation = time.time()
    # time_sign_simulation = np.round(end_sign_simulation - start_sign_simulation, settings.PRECISION)

    # if (verbose):
    #     print(f"Time: (1) selection of number of lags: {time_select_order} s => (2) model fit: {time_model_fit} s => sign simulation: {time_sign_simulation} s")
    #     print(f"Number of lags to use => {nb_lags}")

    return simulated_signs, nb_lags

def simulate_n_signs_from_fitted_params(n, fitted_params, training_signs):
    all_signs = training_signs.copy()
    for _ in range(n):
        expected_value = fitted_params[0]
        for i in range(1, len(fitted_params)):
            expected_value += (fitted_params[i] * all_signs[-i])
        proba_to_buy = expected_value_to_proba_to_buy(expected_value)
        next_sign = simulate_sign(proba_to_buy)
        all_signs.append(next_sign)

    simulated_signs = all_signs[len(training_signs):]
    assert(len(simulated_signs) == n)
    return simulated_signs

def expected_value_to_proba_to_buy(expected_value):
    proba_to_buy = (1 + expected_value) / 2
    return capped_proba(proba_to_buy)

def capped_proba(proba):
    capped_proba = None
    if (proba > 1):
        capped_proba = 1
    elif (proba < 0):
        capped_proba = 0
    else:
        capped_proba = proba

    assert(is_proba_valid(capped_proba))
    return capped_proba

def is_proba_valid(proba):
    return proba >= 0 and proba <= 1

def simulate_sign(proba_to_buy):
    return 1 if np.random.uniform() <= proba_to_buy else -1

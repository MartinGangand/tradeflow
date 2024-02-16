import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error

from ..autocorrelation import autocorrelation_calculator
from trade_flow_modelling.src import settings

# Metric 1: absolute percentage difference of buy percentage
def metric_signs(training_signs, simulated_signs, verbose=False):
    training_buy_pct = buy_percentage(training_signs)
    simulated_buy_pct = buy_percentage(simulated_signs)
    if (training_buy_pct == 0):
        abs_pct_diff = 1 if simulated_buy_pct != 0 else 0
    else:
        abs_pct_diff = np.abs(simulated_buy_pct - training_buy_pct) / training_buy_pct
    
    if (verbose):
        print(f"METRIC 1: Buy pct training: {np.round(100 * training_buy_pct, settings.PRECISION)} % | Buy pct simulated: {np.round(100 * simulated_buy_pct, settings.PRECISION)} % => Diff: {np.round(100 * abs_pct_diff, settings.PRECISION)} %")
    
    return np.round(abs_pct_diff, settings.PRECISION)

def buy_percentage(signs):
    return np.sum([1 for sign in signs if sign == 1]) / len(signs)

# Metric 2: std of buy percentage per portion
def metric_std_buy_pct_per_portion(training_signs, simulated_signs, nb_trades_per_portion, verbose=False, plot=False):
    training_buy_percentages = buy_percentage_per_portion(training_signs, nb_trades_per_portion)
    simulated_buy_percentages = buy_percentage_per_portion(simulated_signs, nb_trades_per_portion)
    

    training_std = np.std(training_buy_percentages)
    simulated_std = np.std(simulated_buy_percentages)

    abs_pct_diff = np.abs(simulated_std - training_std) / training_std

    if (verbose):
        print(f"METRIC 2: Std training: {np.round(training_std, settings.PRECISION)} | Std simulated: {np.round(simulated_std, settings.PRECISION)} => Diff: {np.round(100 * abs_pct_diff, settings.PRECISION)} %")
    
    if (plot):
        plt.plot(training_buy_percentages, "black", label="Buy percentages training")
        plt.plot(simulated_buy_percentages, "orange", label="Buy percentages simulated")
        plt.xlabel("Portion")
        plt.ylabel("Buy percentage")
        plt.title("Buy percentage per portion for training and simulated signs")
        plt.legend()
        plt.show()
    
    return np.round(abs_pct_diff, settings.PRECISION)

def buy_percentage_per_portion(signs, nb_trades_per_portion):
    idx_start = 0
    idx_up = nb_trades_per_portion

    buy_percentages = []
    while (idx_start < len(signs)):
        if (idx_up > len(signs)):
            break
        current_portion_signs = signs[idx_start:idx_up]
        nb_buy = np.sum([1 if i == 1 else 0 for i in current_portion_signs])
        nb_sell = np.sum([1 if i == -1 else 0 for i in current_portion_signs])
        current_buy_percentage = nb_buy / (nb_buy + nb_sell)
        idx_start = idx_up
        idx_up += nb_trades_per_portion
        buy_percentages.append(np.round(current_buy_percentage, 2))

    return buy_percentages

# Metric 3: MAE of autocorrelation functions
def metric_mae_autocorrelation(training_signs, simulated_signs, nb_lags=None, verbose=False, plot=False):
    autocorrelation_true = compute_autocorrelation(training_signs, nb_lags)
    autocorrelation_pred = compute_autocorrelation(simulated_signs, nb_lags)
    mae = mean_absolute_error(autocorrelation_true, autocorrelation_pred) * len(autocorrelation_true)

    nb_lags = len(autocorrelation_pred)

    if (verbose):
        print(f"METRIC 3: {mae} ({nb_lags} lags)")

    if (plot):
        fig, axe = plt.subplots(1, 2, figsize=(18, 4))
        axe[0].plot(autocorrelation_true, "black", linestyle="dashed", label=f"True autocorrelation function (training signs)")
        axe[0].plot(autocorrelation_pred, "blue", label=f"Pred autocorrelation function (simulated signs)")
        axe[0].set_title("Autocorrelation plot for training and simulated signs (linear scale)")
        axe[0].set_ylabel("Lags")
        axe[0].set_xlim(-5, nb_lags)
        axe[0].set_ylim(min(np.nanmin(autocorrelation_true), np.nanmin(autocorrelation_pred)) - 0.1, max(np.nanmax(autocorrelation_true), np.nanmax(autocorrelation_pred)) + 0.1)
        axe[0].grid()
        
        axe[1].plot(autocorrelation_true, "black", linestyle="dashed", label=f"True autocorrelation function (training signs)")
        axe[1].plot(autocorrelation_pred, "blue", label=f"Pred autocorrelation function (simulated signs)")
        axe[1].set_title("Autocorrelation plot for training and simulated signs (log scale)")
        axe[1].set_ylabel("Lags")
        axe[1].set_yscale("log")
        axe[1].set_xlim(-5, nb_lags)
        axe[1].set_ylim(max(0, min(np.nanmin(autocorrelation_true), np.nanmin(autocorrelation_pred)) - 0.1), max(np.nanmax(autocorrelation_true), np.nanmax(autocorrelation_pred)) + 0.1)
        axe[1].grid()
        plt.show()

    return np.round(mae, settings.PRECISION)

def metric_mae_autocorrelation_V2(autocorrelation_true, training_signs, simulated_signs, nb_lags=None, verbose=False, plot=False):
    autocorrelation_pred = compute_autocorrelation(simulated_signs, nb_lags)
    mae = mean_absolute_error(autocorrelation_true, autocorrelation_pred) # * len(autocorrelation_true)

    nb_lags = len(autocorrelation_pred)

    if (verbose):
        print(f"METRIC 3: {mae} ({nb_lags} lags)")

    if (plot):
        fig, axe = plt.subplots(1, 2, figsize=(18, 4))
        axe[0].plot(autocorrelation_true, "black", linestyle="dashed", label=f"True autocorrelation function (training signs)")
        axe[0].plot(autocorrelation_pred, "blue", label=f"Pred autocorrelation function (simulated signs)")
        axe[0].set_title("Autocorrelation plot for training and simulated signs (linear scale)")
        axe[0].set_ylabel("Lags")
        axe[0].set_xlim(-5, nb_lags)
        axe[0].set_ylim(min(np.nanmin(autocorrelation_true), np.nanmin(autocorrelation_pred)) - 0.1, max(np.nanmax(autocorrelation_true), np.nanmax(autocorrelation_pred)) + 0.1)
        axe[0].grid()
        
        axe[1].plot(autocorrelation_true, "black", linestyle="dashed", label=f"True autocorrelation function (training signs)")
        axe[1].plot(autocorrelation_pred, "blue", label=f"Pred autocorrelation function (simulated signs)")
        axe[1].set_title("Autocorrelation plot for training and simulated signs (log scale)")
        axe[1].set_ylabel("Lags")
        axe[1].set_yscale("log")
        axe[1].set_xlim(-5, nb_lags)
        axe[1].set_ylim(max(0, min(np.nanmin(autocorrelation_true), np.nanmin(autocorrelation_pred)) - 0.1), max(np.nanmax(autocorrelation_true), np.nanmax(autocorrelation_pred)) + 0.1)
        axe[1].grid()
        plt.show()
        
    return np.round(mae, settings.PRECISION)

def compute_autocorrelation(signs, nb_lags=None):
    autocorrelation = None
    if (nb_lags is None):
        autocorrelation = autocorrelation_calculator.autocorrelation_convolution(signs)
    else:
        autocorrelation = autocorrelation_calculator.autocorrelation_convolution_perso(signs, nb_lags)
    return autocorrelation
import matplotlib.pyplot as plt
import numpy as np

from .AutocorrelationCalculator import calculate_autocorrelation

def plot_autocorrelation(time_series, nb_lags_max=None, best_nb_lags=None, best_nb_lags_method_labels=None, label="Autocorrelation function", log_scale=True):
    fig, axe = plt.subplots(1, 1, figsize=(8, 4))
    autocorrelation = calculate_autocorrelation(time_series, nb_lags_max)

    axe.plot(autocorrelation, "orange", label=label)
 
    y_1 = [l ** (-0.5) for l in range(1, len(autocorrelation) + 1)]
    y_2 = [l ** (-1.9) for l in range(1, len(autocorrelation) + 1)]

    axe.plot(y_1, "grey", linestyle="dashed", label="x^(-0.5)")
    axe.plot(y_2, "brown", linestyle="dashed", label="x^(-1.9)")

    if (log_scale):
        axe.set_yscale("log")

    if (best_nb_lags is not None):
        assert (len(best_nb_lags) == len(best_nb_lags_method_labels))
        for nb_lags, method_label in zip(best_nb_lags, best_nb_lags_method_labels):
            axe.axvline(x=nb_lags, label=f"Best nb_lags {method_label}: {nb_lags}", linestyle='--')

    axe.set_title(f"Autocorrelation plot | {'log' if log_scale else 'linear'} scale")
    axe.set_xlabel("Lag")
    axe.set_ylabel("Autocorrelation")
    axe.set_xlim(-5, nb_lags_max)
    axe.set_ylim(max(0.001, np.nanmin(autocorrelation) - 0.1), np.nanmax(autocorrelation) + 0.1)
    axe.grid(True)
    axe.legend()
    plt.show()

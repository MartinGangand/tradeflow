from typing import List
from numbers import Number
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import pacf

from ....statistics.autocorrelation.src.autocorrelation import calculate_autocorrelation

def plot_autocorrelation(time_series: List[Number], nb_lags: int | None, log_scale: bool = True) -> None:
    autocorrelation = calculate_autocorrelation(time_series=time_series, nb_lags=nb_lags)
    plot_corr(corr_values=autocorrelation, title="Partial autocorrelation function", log_scale=log_scale)
    
def plot_partial_autocorrelation(time_series: List[Number], nb_lags: int | None, log_scale: bool = True) -> None:
    partial_autocorrelation = pacf(x=time_series, nlags=nb_lags, method="burg", alpha=None)
    plot_corr(corr_values=partial_autocorrelation, title="Partial autocorrelation function", log_scale=log_scale)
    
def plot_corr(corr_values: List[Number], title: str, log_scale: bool = True) -> None:
    y_scale =  f"{'log' if log_scale else 'linear'}"
    fig, axe = plt.subplots(1, 1, figsize=(8, 4))
    axe.plot(corr_values, "purple")
    axe.set_title(f"{title} ({y_scale} scale)")
    axe.set_xlabel("Lag")
    axe.set_xlim(-1, len(corr_values) - 1)
    axe.set_ylim(max(0.0001, np.nanmin(corr_values) - 0.1), np.nanmax(corr_values) + 0.1)
    axe.grid(True)
    plt.show()
    
def plot_corr_training_vs_simulated(corr_values_training: List[Number], corr_values_simulated: List[Number], order: int, title: str, log_scale: bool = True) -> None:
    y_scale =  f"{'log' if log_scale else 'linear'}"
    fig, axe = plt.subplots(1, 1, figsize=(8, 4))
    axe.plot(corr_values_training, "green", linestyle="dashed", label=f"Training")
    axe.plot(corr_values_simulated, "purple", label=f"Simulated")
    axe.set_yscale(y_scale)
    axe.set_title(f"{title} ({y_scale} scale)")
    axe.set_xlabel("Lag")
    axe.set_xlim(-1, len(corr_values_simulated) - 1)
    axe.set_ylim(max(0.0001, min(np.nanmin(corr_values_training), np.nanmin(corr_values_simulated))), max(np.nanmax(corr_values_training), np.nanmax(corr_values_simulated)) + 0.1)
    axe.axvline(x=order, color='grey', label="Order of the model", linestyle='--')
    axe.grid()
    axe.legend()
    plt.show()
    
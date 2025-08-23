"""
This example illustrates the usage of the `tradeflow` package for modeling and simulating trade sign sequences using an Autoregressive (AR) model.

It includes loading trade sign data, fitting an AR model, simulating new trade sign sequences, and generating a statistical summary and plots of the ACF and PACF comparing the original and simulated data.
"""

from pathlib import Path
import numpy as np

import tradeflow

DATA_FOLDER = Path(__file__).parent.joinpath("data")
DATA_FILE = DATA_FOLDER.joinpath("trade_signs_ethusdt_20250817.txt")


def main():
    # Load sample data and run a basic usage verification for the `tradeflow` package
    signs = np.loadtxt(DATA_FILE, dtype="int8")

    # Construct and fit AR model with method "yule_walker" (can also be "burg", "cmle_without_cst", "cmle_with_cst", "mle_without_cst", "mle_with_cst")
    ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")
    ar_model = ar_model.fit(method="yule_walker", significance_level=0.05, check_stationarity=True, check_residuals_not_autocorrelated=True)

    print(f"Model order: {ar_model.order}")
    print(f"Fitted parameters: {ar_model.parameters}")

    # Simulate an autocorrelated sign sequence from the fitted AR model
    # OR
    # Simulate new sign sequence
    simulated_signs = ar_model.simulate(size=1_000_000, seed=1)

    # Generate summary and ACF/PACF plots comparing the original and simulated time series of signs.
    summary_df, fig = ar_model.simulation_summary(plot_acf=True, plot_pacf=True, log_scale=True)
    print(f"Simulation summary:\n{summary_df}")

    """
    Example of statistical summary over the time series counting the number of consecutive signs in a row:
    
    |                             |      Training |   Simulation |
    |-----------------------------|---------------|--------------|
    | size                        |       2844829 |      1000000 |
    | pct_buy (%)                 |         49.97 |        48.69 |
    | mean_nb_consecutive_values  |         25.53 |        25.21 |
    | std_nb_consecutive_values   |         58.21 |        58.34 |
    | Q50.0_nb_consecutive_values |             2 |            3 |
    | Q75.0_nb_consecutive_values |            16 |           12 |
    | Q95.0_nb_consecutive_values |        139.25 |          146 |
    | Q99.0_nb_consecutive_values |           277 |       286.38 |
    | Q99.9_nb_consecutive_values |        511.26 |       475.03 |
    """


if __name__ == "__main__":
    main()

from pathlib import Path

import numpy as np

import tradeflow

DATA_FOLDER = Path(__file__).parent.joinpath("data")


# Load the sample data and run a basic usage verification for the `tradeflow` package
signs = np.loadtxt(DATA_FOLDER.joinpath("trade_signs_ethusdt_20250817.txt"), dtype="int8", delimiter=None)

# Construct the AR model using the trade signs data
ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")

# Fit the AR model with specified parameters with a method chosen between "yule_walker", "burg", "cmle_without_cst", "cmle_with_cst", "mle_without_cst", "mle_with_cst"
ar_model = ar_model.fit(method="yule_walker", significance_level=0.05, check_stationarity=True, check_residuals_not_autocorrelated=True)

# Simulate an autocorrelated sign sequence from the fitted AR model
ar_model.simulate(size=1_000_000, seed=1)

summary_df, fig = ar_model.simulation_summary(plot_acf=True, plot_pacf=True, log_scale=True)

i = 0

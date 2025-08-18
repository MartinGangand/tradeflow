from pathlib import Path

import numpy as np

import tradeflow

DATA_FOLDER = Path(__file__).parent.joinpath("data")


signs = np.loadtxt(DATA_FOLDER.joinpath("trade_signs_ethusdt_20250817.txt"), dtype="int8", delimiter=",")

ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")
ar_model = ar_model.fit(method="yule_walker", significance_level=0.05, check_stationarity=True,
                        check_residuals_not_autocorrelated=True)
ar_model.simulate(size=1_000_000, seed=1)
ar_model.simulation_summary(plot_acf=True, plot_pacf=True, log_scale=True)

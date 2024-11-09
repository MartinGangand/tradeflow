from pathlib import Path

import numpy as np
import pandas as pd

CURRENT_DIRECTORY = Path(__file__).parent.absolute()


class Namespace:

    def __init__(self):
        self.acf = None
        self.pacf = None

        self.percentiles = None
        self.stats_df = None


class ResultsTimeSeries:
    """
    Results are from statsmodels.
    """

    @staticmethod
    def correlation():
        obj = Namespace()
        obj.acf = np.loadtxt(fname=CURRENT_DIRECTORY.joinpath("acf.csv"), dtype=float, delimiter=",")
        obj.pacf = np.loadtxt(fname=CURRENT_DIRECTORY.joinpath("pacf.csv"), dtype=float, delimiter=",")
        return obj

    @staticmethod
    def simulation_summary(column_name: str) -> Namespace:
        obj = Namespace()
        obj.percentiles = (50.0, 75.0, 95.0, 99.0, 99.9)
        index = ["size", "pct_buy (%)", "mean_nb_consecutive_values", "std_nb_consecutive_values",
                 "Q50.0_nb_consecutive_values", "Q75.0_nb_consecutive_values", "Q95.0_nb_consecutive_values",
                 "Q99.0_nb_consecutive_values", "Q99.9_nb_consecutive_values"]
        statistics = [1000.0, 64.0, 3.7037037037037037, 7.845332723462921, 2.0, 3.0, 13.0, 35.13000000000005, 78.00600000000134]
        obj.stats_df = pd.DataFrame(data=statistics, columns=[column_name], index=index)

        return obj

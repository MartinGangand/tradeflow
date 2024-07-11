import os

import numpy as np
import pandas as pd

current_directory = os.path.abspath(os.path.dirname(__file__))


class Namespace:
    pass


class ResultsTimeSeries:
    """
    Results are from statsmodels.
    """

    @staticmethod
    def correlation():
        obj = Namespace()
        obj.acf = np.loadtxt(fname=os.path.join(current_directory, 'acf.csv'), dtype=float, delimiter=",")
        obj.pacf = np.loadtxt(fname=os.path.join(current_directory, 'pacf.csv'), dtype=float, delimiter=",")
        return obj

    @staticmethod
    def signs_statistics(column_name: str) -> Namespace:
        obj = Namespace()
        obj.percentiles = (50.0, 75.0, 95.0, 99.0, 99.9)
        index = ["size", "pct_buy (%)", "mean_nb_consecutive_values", "std_nb_consecutive_values",
                 "Q50.0_nb_consecutive_values", "Q75.0_nb_consecutive_values", "Q95.0_nb_consecutive_values",
                 "Q99.0_nb_consecutive_values", "Q99.9_nb_consecutive_values"]
        statistics = [1000.0, 64.0, 3.7037037037037037, 7.845332723462921, 2.0, 3.0, 13.0, 35.13000000000005, 78.00600000000134]
        obj.stats_df = pd.DataFrame(data=statistics, columns=[column_name], index=index)

        return obj

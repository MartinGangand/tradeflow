from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from numpy.testing import assert_equal, assert_almost_equal
from pandas.testing import assert_frame_equal

from tradeflow.datasets import signs
from tradeflow.exceptions import IllegalNbLagsException, IllegalValueException
from tradeflow.tests.results.results_time_series import ResultsTimeSeries
from tradeflow.time_series import TimeSeries

signs_data = signs.load()


@pytest.fixture
def time_series_signs():
    TimeSeries.__abstractmethods__ = set()
    time_series = TimeSeries(signs=signs_data)
    time_series._order = 6
    return time_series


@pytest.fixture
def time_series_signs_non_stationary():
    TimeSeries.__abstractmethods__ = set()
    time_series = TimeSeries(signs=[-1] * 500 + [1] * 500)
    time_series._order = 1
    return time_series


class TestCalculateAcf:

    @pytest.mark.parametrize("nb_lags", [-1, 0, 1000, 1500])
    def test_calculate_acf_should_raise_exception(self, time_series_signs, nb_lags):
        expected_exception_message = f"Can only calculate the autocorrelation function with a number of lags positive and lower than the time series length (requested number of lags {nb_lags} should be < 1000)."
        with pytest.raises(IllegalNbLagsException) as ex:
            time_series_signs.calculate_acf(nb_lags=nb_lags)

        assert str(ex.value) == expected_exception_message

    @pytest.mark.parametrize("nb_lags", [1, 200, 999])
    def test_calculate_acf(self, time_series_signs, nb_lags):
        actual_acf = time_series_signs.calculate_acf(nb_lags=nb_lags)
        assert len(actual_acf) == nb_lags + 1

        expected_acf = ResultsTimeSeries.correlation().acf[:nb_lags + 1]
        assert_almost_equal(actual=actual_acf, desired=expected_acf, decimal=10)


class TestCalculatePacf:

    @pytest.mark.parametrize("nb_lags", [-1, 0, 500, 750])
    def test_calculate_pacf_should_raise_exception_when_invalid_nb_lags(self, time_series_signs, nb_lags):
        expected_exception_message = f"Can only calculate the partial autocorrelation function with a number of lags positive and lower than 50% of the time series length (requested number of lags {nb_lags} should be < 500)."
        with pytest.raises(IllegalNbLagsException) as ex:
            time_series_signs.calculate_pacf(nb_lags=nb_lags, alpha=0.05)

        assert str(ex.value) == expected_exception_message

    @pytest.mark.parametrize("alpha", [-0.05, 1.05])
    def test_calculate_pacf_should_raise_exception_when_invalid_alpha(self, time_series_signs, alpha):
        expected_exception_message = f"Alpha {alpha} is invalid, it must be in the interval [0, 1]"
        with pytest.raises(IllegalValueException) as ex:
            time_series_signs.calculate_pacf(nb_lags=25, alpha=alpha)

        assert str(ex.value) == expected_exception_message

    @pytest.mark.parametrize("nb_lags,alpha", [(1, 0.05), (200, None), (499, 0.05)])
    def test_calculate_pacf(self, time_series_signs, nb_lags, alpha):
        actual_pacf = time_series_signs.calculate_pacf(nb_lags=nb_lags, alpha=alpha)
        actual_pacf = actual_pacf[0] if alpha is not None else actual_pacf
        assert len(actual_pacf) == nb_lags + 1

        expected_pacf = ResultsTimeSeries.correlation().pacf[:nb_lags + 1]
        assert_almost_equal(actual=actual_pacf, desired=expected_pacf, decimal=10)


class TestTimeSeriesStationarity:

    @pytest.mark.parametrize("regression", ["c", "ct", "ctt", "n"])
    def test_time_series_should_be_stationary(self, time_series_signs, regression):
        assert time_series_signs._is_time_series_stationary(significance_level=0.05, regression=regression)

    @pytest.mark.parametrize("regression", ["c", "ct", "ctt", "n"])
    def test_time_series_should_be_non_stationary(self, time_series_signs_non_stationary, regression):
        assert not time_series_signs_non_stationary._is_time_series_stationary(significance_level=0.05, regression=regression)


class TestSimulationSummary:

    def test_simulation_summary(self, time_series_signs):
        time_series_signs._simulation = time_series_signs._signs
        time_series_signs._order = 6

        actual_simulation_summary_df = time_series_signs.simulation_summary(plot=False, log_scale=False, percentiles=(50.0, 75.0, 95.0, 99.0, 99.9))

        expected_training_stats_df = ResultsTimeSeries.signs_statistics(column_name="Training").stats_df
        expected_simulation_stats_df = ResultsTimeSeries.signs_statistics(column_name="Simulation").stats_df
        expected_simulation_summary_df = pd.concat([expected_training_stats_df, expected_simulation_stats_df],
                                                   axis=1).round(decimals=2)

        assert_frame_equal(left=actual_simulation_summary_df, right=expected_simulation_summary_df, check_dtype=True,
                           check_index_type=True, check_names=True, check_exact=True, obj="stats")

    def test_compute_signs_statistics(self):
        results_signs_stats = ResultsTimeSeries.signs_statistics(column_name="Test signs")
        actual_stats_df = TimeSeries._compute_signs_statistics(signs=signs_data, column_name="Test signs",
                                                               percentiles=results_signs_stats.percentiles)

        expected_stats_df = results_signs_stats.stats_df
        assert_frame_equal(left=actual_stats_df, right=expected_stats_df, check_dtype=True, check_index_type=True,
                           check_names=True,
                           check_exact=True, obj="stats")

    @pytest.mark.parametrize("signs,expected_series", [
        ([1., 1., -1., -1., -1., 1., 1.], [2, 3, 2]),
        ([-1., 1., -1., 1., 1.], [1, 1, 1, 2]),
        ([1., -1., 1., -1.], [1, 1, 1, 1]),
        ([-1., 1., -1., -1., -1., -1., 1., 1., 1., 1., 1., -1.], [1, 1, 4, 5, 1]),
        ([1., 2., 2., 3., 3., 3., 4., 4., 4., 4.], [1, 2, 3, 4])
    ])
    def test_compute_series_nb_consecutive_values(self, signs, expected_series):
        actual_series = TimeSeries._compute_series_nb_consecutive_signs(signs=signs)
        assert_equal(actual=actual_series, desired=expected_series)

    @pytest.mark.parametrize("signs,expected_buy_pct", [
        ([1., -1., 1., 1., -1.], 100 * 3 / 5),
        ([1., 1., 1., 1., 1.], 100.0),
        ([-1., -1., -1., -1., -1.], 0.0),
        ([-1., -1., -1., -1., 1.], 100 * 1 / 5)
    ])
    def test_percentage_buy(self, signs, expected_buy_pct):
        assert TimeSeries._percentage_buy(signs=signs) == expected_buy_pct


class TestPlot:

    @staticmethod
    def check_axe_values_training_vs_simulation(axe: Axes, training_values: np.ndarray, simulation_values: np.ndarray,
                                                order: int, title: str, y_scale: str, x_lim: Tuple[float, float],
                                                y_lim: Tuple[float, float] | None = None):
        assert_almost_equal(actual=axe.lines[0].get_xydata()[:, 1], desired=training_values, decimal=10)
        assert axe.lines[0].get_label() == "Training"

        assert_almost_equal(actual=axe.lines[1].get_xydata()[:, 1], desired=simulation_values, decimal=10)
        assert axe.lines[1].get_label() == "Simulation"

        assert np.all([x == order for x in axe.lines[2].get_xydata()[:, 0]])
        assert axe.get_title() == title
        assert axe.get_xlabel() == "Lag"

        assert axe.get_xscale() == "linear"
        assert axe.get_yscale() == y_scale

        assert axe.get_xlim() == x_lim
        if y_lim is not None:
            assert axe.get_ylim() == y_lim

    @pytest.mark.parametrize("log_scale", [True, False])
    def test_build_fig_corr_training_vs_simulation(self, time_series_signs, log_scale):
        order = time_series_signs._order
        time_series_signs._simulation = time_series_signs._signs
        y_scale = "log" if log_scale else "linear"

        fig = time_series_signs._build_fig_corr_training_vs_simulation(log_scale=log_scale)

        acf_axe = fig.get_axes()[0]
        expected_acf = ResultsTimeSeries.correlation().acf[:2 * order + 1]
        expected_acf_title = f"ACF plot for training and simulated time series ({y_scale} scale)"
        self.check_axe_values_training_vs_simulation(axe=acf_axe, training_values=expected_acf,
                                                     simulation_values=expected_acf,
                                                     order=order, title=expected_acf_title, y_scale=y_scale,
                                                     x_lim=(-1.0, 2 * order))

        pacf_axe = fig.get_axes()[1]
        expected_pacf = ResultsTimeSeries.correlation().pacf[:2 * order + 1]
        expected_pacf_title = f"PACF plot for training and simulated time series ({y_scale} scale)"
        self.check_axe_values_training_vs_simulation(axe=pacf_axe, training_values=expected_pacf,
                                                     simulation_values=expected_pacf, order=order,
                                                     title=expected_pacf_title,
                                                     y_scale=y_scale, x_lim=(-1.0, 2 * order))

    @pytest.mark.parametrize("log_scale", [True, False])
    def test_fill_axe_training_vs_simulation(self, log_scale):
        training_values = np.array([1, 2, 3, 2, 2.5])
        simulation_values = np.array([1.3, 2.1, 2.9, 2.2, 2.4])
        order = 2

        TimeSeries.__abstractmethods__ = set()
        time_series = TimeSeries(signs=training_values)
        time_series._simulation = simulation_values
        time_series._order = order

        title = "Test plot training vs simulation"

        fig, axe = plt.subplots(1, 1, figsize=(8, 4))
        time_series._fill_axe_training_vs_simulation(axe=axe, training=training_values,
                                                     simulation=simulation_values,
                                                     order=order, title=title, log_scale=log_scale)

        y_scale = "log" if log_scale else "linear"
        expected_title = f"{title} ({y_scale} scale)"
        self.check_axe_values_training_vs_simulation(axe=axe, training_values=training_values,
                                                     simulation_values=simulation_values, order=order,
                                                     title=expected_title,
                                                     y_scale=y_scale,
                                                     x_lim=(-1.0, 4.0), y_lim=(1.0, 3.1))

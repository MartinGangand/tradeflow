from typing import Tuple, Optional, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from numpy.testing import assert_equal, assert_almost_equal
from pandas.testing import assert_frame_equal

from tradeflow.datasets import trade_signs_sample
from tradeflow.exceptions import IllegalNbLagsException, IllegalValueException
from tradeflow.tests.results.results_time_series import ResultsTimeSeries
from tradeflow.time_series import TimeSeries


@pytest.fixture(scope="class")
def signs():
    return trade_signs_sample.load()


@pytest.fixture
def time_series_signs(signs):
    TimeSeries.__abstractmethods__ = set()
    time_series = TimeSeries(signs=signs)
    time_series._order = 6
    return time_series


def generate_white_noise(size: int, sigma: float, seed: Optional[int] = None) -> np.ndarray:
    np.random.seed(seed)
    return np.random.normal(loc=0, scale=sigma, size=size)


def generate_autoregressive(size: int, parameters: List[float], sigma: float, seed: Optional[int] = None) -> np.ndarray:
    order = len(parameters)
    adjusted_size = size + order
    inverted_parameters = parameters[::-1]

    epsilon = generate_white_noise(size=adjusted_size, sigma=sigma, seed=seed)
    simulation = [epsilon[0]]
    for i in range(1, adjusted_size):
        nb_el_to_consider = min(order, i)
        visible_inverted_parameters = inverted_parameters[-nb_el_to_consider:]
        visible_series = simulation[-nb_el_to_consider:]

        simulation.append(epsilon[i] + np.dot(visible_inverted_parameters, visible_series))

    return np.asarray(simulation[order:])


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


class TestIsTimeSeriesStationary:

    @pytest.mark.parametrize("nb_lags", [6, None])
    @pytest.mark.parametrize("regression", ["c", "ct", "n"])
    def test_time_series_should_be_stationary(self, signs, nb_lags, regression):
        assert TimeSeries.is_time_series_stationary(time_series=signs, nb_lags=nb_lags, significance_level=0.05, regression=regression)

    @pytest.mark.parametrize("regression", ["c", "ct", "ctt", "n"])
    def test_time_series_should_be_non_stationary(self, regression):
        non_stationary_time_series = [-1] * 500 + [1] * 500
        assert not TimeSeries.is_time_series_stationary(time_series=non_stationary_time_series, nb_lags=1, significance_level=0.05, regression=regression)


class TestBreuschGodfreyTest:
    """
    Results are from statsmodels (function acorr_breusch_godfrey).
    """
    
    SIZE = 100_000

    def test_breusch_godfrey_test_with_autocorrelated_resid(self):
        autocorrelated_resid = generate_autoregressive(size=self.SIZE, parameters=[0.13, 0.04, 0.01], sigma=1, seed=1)
        actual_lagrange_multiplier, actual_p_value = TimeSeries.breusch_godfrey_test(resid=autocorrelated_resid, nb_lags=10)

        assert_almost_equal(actual=actual_lagrange_multiplier, desired=1934.4000726500221, decimal=8)
        assert actual_p_value == 0  # Can reject the null hypothesis of no autocorrelation

    def test_breusch_godfrey_test_with_no_autocorrelated_resid(self):
        white_noise_resid = generate_white_noise(size=self.SIZE, sigma=1, seed=1)
        actual_lagrange_multiplier, actual_p_value = TimeSeries.breusch_godfrey_test(resid=white_noise_resid, nb_lags=10)

        assert_almost_equal(actual=actual_lagrange_multiplier, desired=7.658271690957896, decimal=9)
        assert_almost_equal(actual=actual_p_value, desired=0.6621766710678502, decimal=10)  # Can't reject the null hypothesis of no autocorrelation

    def test_breusch_godfrey_test_should_raise_exception_when_residuals_are_not_1d_array(self):
        with pytest.raises(ValueError) as ex:
            TimeSeries.breusch_godfrey_test(resid=np.asarray([[0.38, 0.25], [0.34, 0.31]]), nb_lags=10)

        assert str(ex.value) == "Residuals must be a 1d array."


class TestSimulationSummary:

    def test_simulation_summary(self, time_series_signs):
        time_series_signs._simulation = time_series_signs._signs
        time_series_signs._order = 6

        actual_simulation_summary_df = time_series_signs.simulation_summary(plot=False, log_scale=False, percentiles=(50.0, 75.0, 95.0, 99.0, 99.9))

        expected_training_stats_df = ResultsTimeSeries.simulation_summary(column_name="Training").stats_df
        expected_simulation_stats_df = ResultsTimeSeries.simulation_summary(column_name="Simulation").stats_df
        expected_simulation_summary_df = pd.concat([expected_training_stats_df, expected_simulation_stats_df],
                                                   axis=1).round(decimals=2)

        assert_frame_equal(left=actual_simulation_summary_df, right=expected_simulation_summary_df, check_dtype=True,
                           check_index_type=True, check_names=True, check_exact=True, obj="stats")

    def test_compute_signs_statistics(self):
        results_signs_stats = ResultsTimeSeries.simulation_summary(column_name="Test signs")
        actual_stats_df = TimeSeries._compute_signs_statistics(signs=trade_signs_sample.load(), column_name="Test signs",
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

    @pytest.mark.parametrize("signs,expected_buy_proportion", [
        ([1., -1., 1., 1., -1.], 3 / 5),
        ([1., 1., 1., 1., 1.], 1.0),
        ([-1., -1., -1., -1., -1.], 0.0),
        ([-1., -1., -1., -1., 1.], 1 / 5)
    ])
    def test_proportion_buy(self, signs, expected_buy_proportion):
        assert TimeSeries.proportion_buy(signs=signs) == expected_buy_proportion


class TestPlot:

    @staticmethod
    def check_axe_values(axe: Axes, expected_functions: List[np.ndarray], expected_labels: List[str], expected_title: str, expected_log_scale: bool,
                         expected_x_lim: Tuple[float, float], expected_y_lim: Optional[Tuple[float, float]], expected_order: Optional[int]):
        for i in range(len(expected_functions)):
            assert_almost_equal(actual=axe.lines[i].get_xydata()[:, 1], desired=expected_functions[i], decimal=10)
            assert axe.lines[i].get_label() == expected_labels[i]

        assert axe.get_title() == expected_title
        assert axe.get_xlabel() == "Lag"

        assert axe.get_xscale() == "linear"
        assert axe.get_yscale() == f"{'log' if expected_log_scale else 'linear'}"

        assert axe.get_xlim() == expected_x_lim
        if expected_y_lim is not None:
            assert axe.get_ylim() == expected_y_lim

        if expected_order is not None:
            idx_order = len(expected_functions)
            assert np.all([x == expected_order for x in axe.lines[idx_order].get_xydata()[:, 0]])

    @pytest.mark.parametrize("log_scale", [True, False])
    def test_build_fig_corr_training_vs_simulation(self, time_series_signs, log_scale):
        order = time_series_signs._order
        time_series_signs._simulation = time_series_signs._signs
        y_scale = "log" if log_scale else "linear"

        fig = time_series_signs._build_fig_corr_training_vs_simulation(log_scale=log_scale)

        acf_axe = fig.get_axes()[0]
        expected_acf = ResultsTimeSeries.correlation().acf[:2 * order + 1]
        expected_acf_title = f"ACF function for training and simulated time series ({y_scale} scale)"
        self.check_axe_values(axe=acf_axe, expected_functions=[expected_acf, expected_acf], expected_labels=["Training", "Simulation"],
                              expected_title=expected_acf_title, expected_log_scale=log_scale, expected_x_lim=(-1.0, 2 * order), expected_y_lim=None, expected_order=order)

        pacf_axe = fig.get_axes()[1]
        expected_pacf = ResultsTimeSeries.correlation().pacf[:2 * order + 1]
        expected_pacf_title = f"PACF function for training and simulated time series ({y_scale} scale)"
        self.check_axe_values(axe=pacf_axe, expected_functions=[expected_pacf, expected_pacf], expected_labels=["Training", "Simulation"],
                              expected_title=expected_pacf_title, expected_log_scale=log_scale, expected_x_lim=(-1.0, 2 * order), expected_y_lim=None, expected_order=order)

    @pytest.mark.parametrize("log_scale", [True, False])
    def test_fill_axe(self, log_scale):
        training_values = np.array([1, 2, 3, 2, 2.5])
        simulation_values = np.array([1.3, 2.1, 2.9, 2.2, 2.4])
        order = 2

        TimeSeries.__abstractmethods__ = set()
        time_series = TimeSeries(signs=training_values)
        time_series._simulation = simulation_values
        time_series._order = order

        title = "Test plot training vs simulation"

        fig, axe = plt.subplots(1, 1, figsize=(8, 4))
        time_series._fill_axe(axe=axe, functions=[training_values, simulation_values], colors=["green", "purple"], linestyles=["dashed", "solid"], labels=["Training", "Simulation"], title=title, xlabel="Lag", log_scale=log_scale, order=order)

        expected_title = f"{title} ({'log' if log_scale else 'linear'} scale)"
        self.check_axe_values(axe=axe, expected_functions=[training_values, simulation_values], expected_labels=["Training", "Simulation"],
                              expected_title=expected_title, expected_log_scale=log_scale, expected_x_lim=(-1.0, 4.0), expected_y_lim=(1.0, 3.1), expected_order=order)

    @pytest.mark.parametrize("log_scale", [True, False])
    def test_plot_acf_and_pacf(self, time_series_signs, log_scale):
        nb_lags = 10
        y_scale = "log" if log_scale else "linear"

        fig = time_series_signs.plot_acf_and_pacf(nb_lags=10, log_scale=log_scale)

        expected_acf = ResultsTimeSeries.correlation().acf[:nb_lags + 1]
        self.check_axe_values(axe=fig.get_axes()[0], expected_functions=[expected_acf], expected_labels=["Time series of size 1000"],
                              expected_title=f"ACF function ({y_scale} scale)", expected_log_scale=log_scale, expected_x_lim=(-1.0, nb_lags), expected_y_lim=None, expected_order=None)

        expected_pacf = ResultsTimeSeries.correlation().pacf[:nb_lags + 1]
        self.check_axe_values(axe=fig.get_axes()[1], expected_functions=[expected_pacf], expected_labels=["Time series of size 1000"],
                              expected_title=f"PACF function ({y_scale} scale)", expected_log_scale=log_scale, expected_x_lim=(-1.0, nb_lags), expected_y_lim=None, expected_order=None)

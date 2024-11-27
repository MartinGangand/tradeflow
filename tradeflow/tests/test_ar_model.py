import pytest
from numpy.testing import assert_equal, assert_almost_equal, assert_allclose

from tradeflow.ar_model import AR
from tradeflow.datasets import trade_signs_sample, trade_signs_btcusdt_20240720
from tradeflow.exceptions import IllegalNbLagsException, EnumValueException, \
    IllegalValueException, ModelNotFittedException, NonStationaryTimeSeriesException
from tradeflow.tests.results.results_ar_model import ResultsAR


@pytest.fixture
def signs_sample():
    return trade_signs_sample.load()


@pytest.fixture
def signs_btcusdt():
    return trade_signs_btcusdt_20240720.load()


@pytest.fixture
def ar_model_with_max_order_6(signs_sample):
    ar_model = AR(signs=signs_sample, max_order=6, order_selection_method=None, information_criterion=None)
    return ar_model


@pytest.fixture
def ar_model_non_stationary_with_max_order_1():
    ar_model = AR(signs=[-1] * 500 + [1] * 500, max_order=1, order_selection_method=None, information_criterion=None)
    return ar_model


class TestInit:

    @pytest.mark.parametrize("max_order", [500, 1000])
    def test_init_max_order_should_raise_exception_when_invalid_max_order(self, signs_sample, max_order):
        with pytest.raises(IllegalNbLagsException) as ex:
            AR(signs=signs_sample, max_order=max_order, order_selection_method=None, information_criterion=None)

        assert str(ex.value) == f"{max_order} is not valid for 'max_order', it must be positive and lower than 50% of the time series length (< 500)."

    def test_init_should_raise_exception_when_invalid_order_selection_method(self, signs_sample):
        with pytest.raises(EnumValueException) as ex:
            AR(signs=signs_sample, max_order=6, order_selection_method="invalid_order_selection_method", information_criterion="aic")

        assert str(ex.value) == "The value 'invalid_order_selection_method' for order_selection_method is not valid, it must be among ['information_criterion', 'pacf'] or None if it is valid."

    @pytest.mark.parametrize("order_selection_method,information_criterion", [
        ("information_criterion", "invalid_ic"),
        ("information_criterion", None)
    ])
    def test_init_should_raise_exception_when_invalid_information_criterion(self, signs_sample, order_selection_method, information_criterion):
        expected_exception_message = f"The value '{information_criterion}' for information_criterion is not valid, it must be among ['aic', 'bic', 'hqic'] or None if it is valid."
        with pytest.raises(EnumValueException) as ex:
            AR(signs=signs_sample, max_order=6, order_selection_method=order_selection_method, information_criterion=information_criterion)

        assert str(ex.value) == expected_exception_message


class TestResid:

    def test_resid(self):
        ar = AR(signs=[1, 1, 1, -1, 1, 1, -1, 1, 1, 1], max_order=3)
        ar._order = 3
        ar._parameters = [0.009, 0.43, 0.21, 0.20]

        actual_resid = ar.resid()
        assert_almost_equal(actual=actual_resid, desired=[-1.849, 1.011, 0.571, -1.449, 1.011, 0.571, 0.551], decimal=10)


class TestInitMaxOrder:

    @pytest.mark.parametrize("max_order,expected_max_order", [
        (25, 25),
        (None, 22)  # Schwert (1989)
    ])
    def test_init_max_order(self, ar_model_with_max_order_6, max_order, expected_max_order):
        assert ar_model_with_max_order_6._init_max_order(max_order=max_order) == expected_max_order

    @pytest.mark.parametrize("max_order", [0, 500, 1000])
    def test_init_max_order_should_raise_exception_when_invalid_max_order(self, ar_model_with_max_order_6, max_order):
        expected_exception_message = f"{max_order} is not valid for 'max_order', it must be positive and lower than 50% of the time series length (< 500)."
        with pytest.raises(IllegalNbLagsException) as ex:
            ar_model_with_max_order_6._init_max_order(max_order=max_order)

        assert str(ex.value) == expected_exception_message


class TestFit:

    @pytest.mark.parametrize("method", ["yule_walker", "ols_with_cst"])
    def test_fit(self, ar_model_with_max_order_6, method):
        ar_model_with_max_order_6.fit(method=method)

        expected_parameters_results = ResultsAR.parameters_order_6(method=method)
        assert_almost_equal(actual=ar_model_with_max_order_6._constant_parameter, desired=expected_parameters_results.constant_parameter, decimal=10)
        assert_almost_equal(actual=ar_model_with_max_order_6._parameters, desired=expected_parameters_results.parameters, decimal=10)

    @pytest.mark.parametrize("method", ["invalid_method", None])
    def test_fit_should_raise_exception_when_invalid_method(self, ar_model_with_max_order_6, method):
        expected_exception_message = f"The value '{method}' for method is not valid, it must be among ['yule_walker', 'ols_with_cst'] or None if it is valid."
        with pytest.raises(EnumValueException) as ex:
            ar_model_with_max_order_6.fit(method=method)

        assert str(ex.value) == expected_exception_message

    @pytest.mark.parametrize("method", ["yule_walker", "ols_with_cst"])
    def test_fit_should_raise_exception_when_time_series_non_stationary(self, ar_model_non_stationary_with_max_order_1, method):
        with pytest.raises(NonStationaryTimeSeriesException) as ex:
            ar_model_non_stationary_with_max_order_1.fit(method="yule_walker")

        assert str(ex.value) == "The time series must be stationary in order to be fitted."


class TestSelectOrder:

    @pytest.mark.parametrize("max_order,order_selection_method,information_criterion,expected_order", [
        (25, "information_criterion", "aic", 6), (4, "information_criterion", "aic", 4),
        (50, "information_criterion", "bic", 5), (3, "information_criterion", "bic", 3),
        (25, "information_criterion", "hqic", 6), (2, "information_criterion", "hqic", 2),
        (499, "pacf", "hqic", 6), (1, "pacf", "hqic", 1)
    ])
    def test_select_order_with_selection_method(self, signs_sample, max_order, order_selection_method, information_criterion, expected_order):
        ar_model = AR(signs=signs_sample, max_order=max_order, order_selection_method=order_selection_method, information_criterion=information_criterion)
        assert ar_model._max_order == max_order

        ar_model._select_order()
        assert ar_model._order == expected_order

    @pytest.mark.parametrize("max_order,information_criterion,expected_order", [
        (25, None, 25),
        (25, "aic", 25),
        (None, None, 22),  # Schwert (1989)
        (None, "aic", 22)  # Schwert (1989)
    ])
    def test_select_order_without_selection_method(self, signs_sample, max_order, information_criterion, expected_order):
        ar_model = AR(signs=signs_sample, max_order=max_order, order_selection_method=None, information_criterion=information_criterion)
        ar_model._select_order()
        assert ar_model._order == expected_order == ar_model._max_order


class TestSimulate:

    @pytest.mark.parametrize("method", ["yule_walker", "ols_with_cst"])
    @pytest.mark.parametrize("size", [50, 1000])
    def test_simulate(self, ar_model_with_max_order_6, method, size):
        actual_simulation = ar_model_with_max_order_6.fit(method=method).simulate(size=size, seed=1)

        expected_signs = ResultsAR.simulated_signs(fit_method=method)
        assert len(actual_simulation) == size
        assert_equal(actual=actual_simulation, desired=expected_signs.simulation[:size])

    @pytest.mark.parametrize("size", [-50, 0])
    def test_simulate_should_raise_exception_when_invalid_size(self, ar_model_with_max_order_6, size):
        with pytest.raises(IllegalValueException) as ex:
            ar_model_with_max_order_6.fit("yule_walker").simulate(size=size)

        assert str(ex.value) == f"The size '{size}' for the time series to be simulated is not valid, it must be greater than 0."

    def test_simulate_should_raise_exception_when_model_not_fitted(self, ar_model_with_max_order_6):
        with pytest.raises(ModelNotFittedException) as ex:
            ar_model_with_max_order_6.simulate(size=50)

        assert str(ex.value) == "The model has not yet been fitted. Fit the model first by calling 'fit()'."


class TestSimulationSummary:

    @pytest.mark.parametrize("fit_method", ["ols_with_cst", "yule_walker"])
    def test_simulation_summary(self, signs_btcusdt, fit_method):
        size_simulation = 2_000_000
        ar_model = AR(signs=signs_btcusdt, max_order=None, order_selection_method="pacf", information_criterion=None)
        actual_simulation = ar_model.fit(method=fit_method).simulate(size=size_simulation, seed=1)
        summary_df = ar_model.simulation_summary(plot=False, percentiles=(50.0, 75.0, 95.0, 99.0))

        res_training_signs_stats = ResultsAR.simulation_summary_training_signs(fit_method=fit_method)

        assert ar_model._order == 52
        assert_almost_equal(actual=ar_model._constant_parameter, desired=res_training_signs_stats.constant_parameter, decimal=10)
        assert_almost_equal(actual=ar_model._parameters, desired=res_training_signs_stats.parameters, decimal=10)

        # Checks that training signs statistics did not change
        assert len(signs_btcusdt) == res_training_signs_stats.size
        assert summary_df.loc["pct_buy (%)"]["Training"] == res_training_signs_stats.pct_buy
        assert summary_df.loc["mean_nb_consecutive_values"]["Training"] == res_training_signs_stats.mean_nb_consecutive_values
        assert summary_df.loc["std_nb_consecutive_values"]["Training"] == res_training_signs_stats.std_nb_consecutive_values
        assert summary_df.loc["Q50.0_nb_consecutive_values"]["Training"] == res_training_signs_stats.Q50_nb_consecutive_values
        assert summary_df.loc["Q75.0_nb_consecutive_values"]["Training"] == res_training_signs_stats.Q75_nb_consecutive_values
        assert summary_df.loc["Q95.0_nb_consecutive_values"]["Training"] == res_training_signs_stats.Q95_nb_consecutive_values
        assert summary_df.loc["Q99.0_nb_consecutive_values"]["Training"] == res_training_signs_stats.Q99_nb_consecutive_values

        # Checks that simulated signs are close to training signs statistics
        assert len(actual_simulation) == size_simulation
        expected_pct_buy = summary_df.loc["pct_buy (%)"]["Training"] if fit_method == "ols_with_cst" else 50.0  # If the fit method is yule_walker there is no constant parameter, so we expect 50% of buy
        assert_allclose(actual=summary_df.loc["pct_buy (%)"]["Simulation"], desired=expected_pct_buy, rtol=0, atol=1.0, equal_nan=False)
        assert_allclose(actual=summary_df.loc["mean_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["mean_nb_consecutive_values"]["Training"], rtol=0, atol=0.25, equal_nan=False)
        assert_allclose(actual=summary_df.loc["std_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["std_nb_consecutive_values"]["Training"], rtol=0, atol=15, equal_nan=False)

        assert_allclose(actual=summary_df.loc["Q50.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q50.0_nb_consecutive_values"]["Training"], rtol=0, atol=1, equal_nan=False)
        assert_allclose(actual=summary_df.loc["Q75.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q75.0_nb_consecutive_values"]["Training"], rtol=0, atol=2, equal_nan=False)
        assert_allclose(actual=summary_df.loc["Q95.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q95.0_nb_consecutive_values"]["Training"], rtol=0, atol=3, equal_nan=False)
        assert_allclose(actual=summary_df.loc["Q99.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q99.0_nb_consecutive_values"]["Training"], rtol=0, atol=6, equal_nan=False)

import pytest
from numpy.testing import assert_equal, assert_almost_equal

from tradeflow.ar_model import AR
from tradeflow.datasets import signs
from tradeflow.exceptions import IllegalNbLagsException, EnumValueException, \
    IllegalValueException, ModelNotFittedException, NonStationaryTimeSeriesException
from tradeflow.tests.results.results_ar_model import ResultsAR

signs_data = signs.load()


@pytest.fixture
def ar_model_with_max_order_6():
    ar_model = AR(signs=signs_data, max_order=6, order_selection_method=None, information_criterion=None)
    return ar_model


@pytest.fixture
def ar_model_non_stationary_with_max_order_1():
    ar_model = AR(signs=[-1] * 500 + [1] * 500, max_order=1, order_selection_method=None, information_criterion=None)
    return ar_model


class TestInit:

    @pytest.mark.parametrize("max_order", [500, 1000])
    def test_init_max_order_should_raise_exception_when_invalid_max_order(self, max_order):
        with pytest.raises(IllegalNbLagsException) as ex:
            AR(signs=signs_data, max_order=max_order, order_selection_method=None, information_criterion=None)

        assert str(ex.value) == f"{max_order} is not valid for 'max_order', it must be positive and lower than 50% of the time series length (< 500)."

    def test_init_should_raise_exception_when_invalid_order_selection_method(self):
        with pytest.raises(EnumValueException) as ex:
            AR(signs=signs_data, max_order=6, order_selection_method="invalid_order_selection_method", information_criterion="aic")

        assert str(ex.value) == "The value 'invalid_order_selection_method' for order_selection_method is not valid, it must be among ['information_criterion', 'pacf'] or None if it is valid."

    @pytest.mark.parametrize("order_selection_method,information_criterion", [
        ("information_criterion", "invalid_ic"),
        ("information_criterion", None)
    ])
    def test_init_should_raise_exception_when_invalid_information_criterion(self, order_selection_method, information_criterion):
        expected_exception_message = f"The value '{information_criterion}' for information_criterion is not valid, it must be among ['aic', 'bic', 'hqic'] or None if it is valid."
        with pytest.raises(EnumValueException) as ex:
            AR(signs=signs_data, max_order=6, order_selection_method=order_selection_method, information_criterion=information_criterion)

        assert str(ex.value) == expected_exception_message


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

        assert str(ex.value) == "The time series must be stationary to be fitted."


class TestSelectOrder:

    @pytest.mark.parametrize("max_order,order_selection_method,information_criterion,expected_order", [
        (25, "information_criterion", "aic", 6), (4, "information_criterion", "aic", 4),
        (50, "information_criterion", "bic", 5), (3, "information_criterion", "bic", 3),
        (25, "information_criterion", "hqic", 6), (2, "information_criterion", "hqic", 2),
        (499, "pacf", "hqic", 6), (1, "pacf", "hqic", 1)
    ])
    def test_select_order_with_selection_method(self, max_order, order_selection_method, information_criterion, expected_order):
        ar_model = AR(signs=signs_data, max_order=max_order, order_selection_method=order_selection_method, information_criterion=information_criterion)
        assert ar_model._max_order == max_order

        ar_model._select_order()
        assert ar_model._order == expected_order

    @pytest.mark.parametrize("max_order,information_criterion,expected_order", [
        (25, None, 25),
        (25, "aic", 25),
        (None, None, 22),  # Schwert (1989)
        (None, "aic", 22)  # Schwert (1989)
    ])
    def test_select_order_without_selection_method(self, max_order, information_criterion, expected_order):
        ar_model = AR(signs=signs_data, max_order=max_order, order_selection_method=None, information_criterion=information_criterion)
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

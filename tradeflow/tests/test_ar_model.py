import numpy as np
import pytest
from numpy.testing import assert_almost_equal, assert_allclose, assert_array_almost_equal, \
    assert_array_equal

from tradeflow.ar_model import AR
from tradeflow.common.exceptions import EnumValueException
from tradeflow.common.general_utils import get_enum_values
from tradeflow.common.shared_libraries_registry import Singleton
from tradeflow.datasets import trade_signs_sample, trade_signs_btcusdt_20240720
from tradeflow.enums import FitMethodAR
from tradeflow.exceptions import IllegalNbLagsException, IllegalValueException, ModelNotFittedException, \
    NonStationaryTimeSeriesException, AutocorrelatedResidualsException
from tradeflow.tests.test_time_series import generate_autoregressive, generate_white_noise

SIGNIFICANCE_LEVEL = 0.05


@pytest.fixture
def signs_sample():
    return trade_signs_sample.load()


@pytest.fixture
def signs_btcusdt():
    return trade_signs_btcusdt_20240720.load()


@pytest.fixture
def ar_model_with_max_order_6(signs_sample):
    ar_model = AR(signs=signs_sample, max_order=6, order_selection_method=None)
    return ar_model


@pytest.fixture
def ar_model_non_stationary_with_max_order_1():
    ar_model = AR(signs=[-1] * 500 + [1] * 500, max_order=1, order_selection_method=None)
    return ar_model


class TestInit:

    @pytest.mark.parametrize("max_order", [500, 1000])
    def test_init_max_order_should_raise_exception_when_invalid_max_order(self, signs_sample, max_order):
        with pytest.raises(IllegalNbLagsException) as ex:
            AR(signs=signs_sample, max_order=max_order, order_selection_method=None)

        assert str(ex.value) == f"{max_order} is not valid for 'max_order', it must be positive and lower than 50% of the time series length (< 500)."

    def test_init_should_raise_exception_when_invalid_order_selection_method(self, signs_sample):
        with pytest.raises(EnumValueException) as ex:
            AR(signs=signs_sample, max_order=6, order_selection_method="invalid_order_selection_method")

        assert str(ex.value) == "The value 'invalid_order_selection_method' for order_selection_method is not valid, it must be among ['pacf'] or None if it is valid."


class TestResid:

    def test_resid(self):
        ar = AR(signs=[1, 1, 1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1, 1, 1, -1, -1, 1, 1, -1, 1, 1, 1, 1, -1, 1], max_order=3)
        ar._order = 3
        ar._constant_parameter = 0.009
        ar._parameters = [0.43, 0.21, 0.20]

        actual_resid = ar.resid(seed=1)
        assert_almost_equal(actual=actual_resid, desired=[-2, 2, 0, -2, 0, 0, 0, -2, -2, 0, 2, 2, -2, 0, 0, 2, -2, 2, 0, 0, 0, 0, 0], decimal=10)

    def test_resid_should_raise_exception_when_parameters_not_set(self):
        ar = AR(signs=[1, 1, 1, -1, 1, 1, -1, 1, 1, 1], max_order=3)
        ar._order = None
        ar._constant_parameter = 0
        ar._parameters = None

        with pytest.raises(ModelNotFittedException) as ex:
            ar.resid(seed=None)

        assert str(ex.value) == "The model does not have its parameters set. Fit the model first by calling 'fit()'."


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

    @pytest.mark.parametrize("method", [FitMethodAR.YULE_WALKER, FitMethodAR.BURG, FitMethodAR.OLS_WITH_CST])
    def test_fit(self, ar_model_with_max_order_6, method, num_regression):
        ar_model_with_max_order_6.fit(method=method.value, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        # Results are from statsmodels.
        num_regression.check(
            {
                "parameters": ar_model_with_max_order_6._parameters,
                "constant_parameter": [ar_model_with_max_order_6._constant_parameter]
            },
            default_tolerance=dict(atol=1e-10, rtol=0)
        )

    @pytest.mark.parametrize("method,start_parameters", [
        (FitMethodAR.MLE_WITHOUT_CST, [0.20793670441358317, 0.15625334330632215, 0.08328570101676176, 0.10762268507210443, 0.12228963258158163, 0.07896963026086244]),
        (FitMethodAR.MLE_WITH_CST, [0.06400645100573688, 0.20915180295744143, 0.15836060267986332, 0.0834257462768199, 0.10653755478818641, 0.12165411140031882, 0.07969039271249247])
    ])
    def test_fit_with_mle_method(self, mocker, ar_model_with_max_order_6, method, start_parameters, num_regression):
        mocker.patch.object(ar_model_with_max_order_6, "_compute_start_parameters", return_value=start_parameters)

        ar_model_with_max_order_6.fit(method=method.value, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        # Results are from statsmodels.
        num_regression.check(
            {
                "parameters": ar_model_with_max_order_6._parameters,
                "constant_parameter": [ar_model_with_max_order_6._constant_parameter]
            },
            default_tolerance=dict(atol=1e-7, rtol=0)
        )

    @pytest.mark.parametrize("method", [FitMethodAR.MLE_WITHOUT_CST, FitMethodAR.MLE_WITH_CST])
    def test_fit_with_mle_should_raise_exception_when_did_not_converge(self, mocker, ar_model_with_max_order_6, method):
        mocker.patch("scipy.optimize.fmin_l_bfgs_b", return_value=(None, None, {"warnflag": 1}))

        with pytest.raises(Exception) as ex:
            ar_model_with_max_order_6.fit(method=method.value, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        assert str(ex.value) == "lbfgs method did not succeed to find optimal parameters, you may try to use another method."

    @pytest.mark.parametrize("method", ["invalid_method", None])
    def test_fit_should_raise_exception_when_invalid_method(self, ar_model_with_max_order_6, method):
        expected_exception_message = f"The value '{method}' for method is not valid, it must be among {get_enum_values(enum_obj=FitMethodAR)} or None if it is valid."
        with pytest.raises(EnumValueException) as ex:
            ar_model_with_max_order_6.fit(method=method, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        assert str(ex.value) == expected_exception_message

    def test_fit_should_raise_exception_when_time_series_non_stationary(self, ar_model_non_stationary_with_max_order_1):
        with pytest.raises(NonStationaryTimeSeriesException) as ex:
            ar_model_non_stationary_with_max_order_1.fit(method=FitMethodAR.YULE_WALKER.value, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        assert str(ex.value) == "The time series must be stationary in order to be fitted."

    def test_fit_should_raise_exception_when_residuals_are_autocorrelated_and_check_residuals_is_true(self, mocker, ar_model_with_max_order_6):
        autocorrelated_resid = generate_autoregressive(size=10_000, parameters=[0.04, 0.01], sigma=1, seed=1)
        mocker.patch.object(ar_model_with_max_order_6, "resid", return_value=autocorrelated_resid)
        spy_breusch_godfrey_test = mocker.spy(ar_model_with_max_order_6, "breusch_godfrey_test")

        with pytest.raises(AutocorrelatedResidualsException) as ex:
            ar_model_with_max_order_6.fit(method="yule_walker", significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        assert str(ex.value) == "The residuals of the model seems to be autocorrelated (p value of the null hypothesis of no autocorrelation is 0.0129), you may try to increase the number of lags, or you can set 'check_residuals' to False to disable this check."
        spy_breusch_godfrey_test.assert_called_once_with(autocorrelated_resid)
        actual_lagrange_multiplier, actual_p_value = spy_breusch_godfrey_test.spy_return
        assert_almost_equal(actual=actual_lagrange_multiplier, desired=22.46997749885238, decimal=11)  # Results are from statsmodels (function acorr_breusch_godfrey).
        assert_almost_equal(actual=actual_p_value, desired=0.012881423129239181, decimal=13)

    def test_fit_should_not_raise_exception_when_residuals_are_not_autocorrelated_and_check_residuals_is_true(self, mocker, ar_model_with_max_order_6):
        white_noise_resid = generate_white_noise(size=10_000, sigma=1, seed=1)
        mocker.patch.object(ar_model_with_max_order_6, "resid", return_value=white_noise_resid)
        spy_breusch_godfrey_test = mocker.spy(ar_model_with_max_order_6, "breusch_godfrey_test")

        ar_model_with_max_order_6.fit(method="yule_walker", significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

        spy_breusch_godfrey_test.assert_called_once_with(white_noise_resid)
        actual_lagrange_multiplier, actual_p_value = spy_breusch_godfrey_test.spy_return
        assert_almost_equal(actual=actual_lagrange_multiplier, desired=10.584578876704498, decimal=10)  # Results are from statsmodels (function acorr_breusch_godfrey).
        assert_almost_equal(actual=actual_p_value, desired=0.39078478482620826, decimal=11)

    def test_fit_should_not_raise_exception_when_residuals_are_autocorrelated_and_check_residuals_is_false(self, mocker, ar_model_with_max_order_6):
        autocorrelated_resid = generate_autoregressive(size=10_000, parameters=[0.04, 0.01], sigma=1, seed=1)
        mock_resid = mocker.patch.object(ar_model_with_max_order_6, "resid", return_value=autocorrelated_resid)
        spy_breusch_godfrey_test = mocker.spy(ar_model_with_max_order_6, "breusch_godfrey_test")

        ar_model_with_max_order_6.fit(method="yule_walker", significance_level=SIGNIFICANCE_LEVEL, check_residuals=False)

        mock_resid.assert_not_called()
        spy_breusch_godfrey_test.assert_not_called()


class TestGetModelXY:

    def test_get_model_x_y_without_cst_parameter(self):
        ar_model = AR(signs=[1, 2, 3, 4, 5, 6, 7, 8], max_order=3, order_selection_method=None)
        ar_model._order = 3
        actual_x, actual_y = ar_model._get_model_x_y(has_cst_parameter=False)

        expected_x = np.asarray([[3., 2., 1.],
                                 [4., 3., 2.],
                                 [5., 4., 3.],
                                 [6., 5., 4.],
                                 [7., 6., 5.]])
        expected_y = np.asarray([[4.],
                                 [5.],
                                 [6.],
                                 [7.],
                                 [8.]])
        assert_array_equal(actual_x, expected_x, strict=True)
        assert_array_equal(actual_y, expected_y, strict=True)

    def test_get_model_x_y_with_cst_parameter(self):
        ar_model = AR(signs=[1, 2, 3, 4, 5, 6, 7, 8], max_order=3, order_selection_method=None)
        ar_model._order = 3
        actual_x, actual_y = ar_model._get_model_x_y(has_cst_parameter=True)

        expected_x = np.asarray([[1., 3., 2., 1.],
                                 [1., 4., 3., 2.],
                                 [1., 5., 4., 3.],
                                 [1., 6., 5., 4.],
                                 [1., 7., 6., 5.]])
        expected_y = np.asarray([[4.],
                                 [5.],
                                 [6.],
                                 [7.],
                                 [8.]])
        assert_array_equal(actual_x, expected_x, strict=True)
        assert_array_equal(actual_y, expected_y, strict=True)


class TestLogLikelihood:

    PARAMETERS_WITHOUT_CST = np.asarray([0.20793670441358317, 0.15625334330632215, 0.08328570101676176, 0.10762268507210443, 0.12228963258158163, 0.07896963026086244])
    PARAMETERS_WITH_CST = np.r_[0.06400645100573688, PARAMETERS_WITHOUT_CST]

    def _set_model_order_start_idx_x_y(self, ar_model: AR, order: int, has_cst_parameter: bool) -> None:
        ar_model._order = order
        ar_model._x, ar_model._y = ar_model._get_model_x_y(has_cst_parameter=has_cst_parameter)
        ar_model._start_idx_parameters = 1 if has_cst_parameter else 0
        ar_model._first_order_signs = ar_model._signs[:order].reshape((order, 1))

    @pytest.mark.parametrize("has_cst_parameter,parameters,expected_log_likelihood", [
        (False, PARAMETERS_WITHOUT_CST, -1213.402414644196),
        (True, PARAMETERS_WITH_CST, -1209.9266539115727)
    ])
    def test_log_likelihood(self, ar_model_with_max_order_6, has_cst_parameter, parameters, expected_log_likelihood):
        self._set_model_order_start_idx_x_y(ar_model=ar_model_with_max_order_6, order=6,  has_cst_parameter=has_cst_parameter)

        actual_loglikelihood = ar_model_with_max_order_6._log_likelihood(parameters=parameters)
        assert actual_loglikelihood == expected_log_likelihood

    @pytest.mark.parametrize("has_cst_parameter,parameters", [
        (False, PARAMETERS_WITHOUT_CST),
        (True, PARAMETERS_WITH_CST)
    ])
    def test_calculate_vp_inv(self, ar_model_with_max_order_6, has_cst_parameter, parameters):
        self._set_model_order_start_idx_x_y(ar_model=ar_model_with_max_order_6, order=6, has_cst_parameter=has_cst_parameter)

        actual_vp_inv = ar_model_with_max_order_6._calculate_vp_inv(parameters=parameters)

        # Results are from statsmodels.
        expected_vp_inv = np.asarray([[0.9937637974964627, -0.21759387148328738, -0.16475226695414746, -0.08986274203207217, -0.11996195382002829, -0.13871031724678454],
                                      [-0.21759387148328738, 1.0220467163019062, -0.19826420483747748, -0.15761909053658626, -0.08659219952061172, -0.1199619538200283],
                                      [-0.16475226695414746, -0.19826420483747748, 1.0348791812541802, -0.1942139663755341, -0.15761909053658626, -0.08986274203207217],
                                      [-0.08986274203207217, -0.15761909053658626, -0.1942139663755341, 1.0348791812541804, -0.19826420483747748, -0.16475226695414746],
                                      [-0.11996195382002829, -0.08659219952061172, -0.15761909053658626, -0.19826420483747748, 1.0220467163019065, -0.2175938714832874],
                                      [-0.13871031724678454, -0.1199619538200283, -0.08986274203207217, -0.16475226695414746, -0.2175938714832874, 0.9937637974964627]])
        assert_array_almost_equal(actual_vp_inv, expected_vp_inv, decimal=15)


class TestSelectOrder:

    @pytest.mark.parametrize("max_order,order_selection_method,expected_order", [
        (499, "pacf", 6),
        (1, "pacf", 1)
    ])
    def test_select_order_with_selection_method(self, signs_sample, max_order, order_selection_method, expected_order):
        ar_model = AR(signs=signs_sample, max_order=max_order, order_selection_method=order_selection_method)
        assert ar_model._max_order == max_order

        ar_model._select_order()
        assert ar_model._order == expected_order

    @pytest.mark.parametrize("max_order,expected_order", [
        (25, 25),
        (25, 25),
        (None, 22),  # Schwert (1989)
        (None, 22)  # Schwert (1989)
    ])
    def test_select_order_without_selection_method(self, signs_sample, max_order, expected_order):
        ar_model = AR(signs=signs_sample, max_order=max_order, order_selection_method=None)
        ar_model._select_order()
        assert ar_model._order == expected_order == ar_model._max_order


class TestSimulate:

    @pytest.fixture(scope="function", autouse=True)
    def reset_singleton(self):
        yield
        Singleton._instances.clear()

    @pytest.fixture
    def fitted_model(self, ar_model_with_max_order_6):
        return ar_model_with_max_order_6.fit(method=FitMethodAR.YULE_WALKER.value, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)

    def test_simulate(self, fitted_model, num_regression):
        actual_simulation = fitted_model.simulate(size=1000, seed=1)
        assert len(actual_simulation) == 1000

        # Results are from statsmodels.
        num_regression.check({"simulated_signs": actual_simulation}, default_tolerance=dict(atol=0, rtol=0))

    def test_simulate_with_no_seed(self, mocker, fitted_model, num_regression):
        mocker.patch("numpy.random.randint", return_value=1)

        actual_simulation = fitted_model.simulate(size=1000, seed=None)
        assert len(actual_simulation) == 1000

        # Results are from statsmodels.
        num_regression.check({"simulated_signs": actual_simulation}, basename="test_simulate", default_tolerance=dict(atol=0, rtol=0))

    @pytest.mark.parametrize("size", [-50, 0])
    def test_simulate_should_raise_exception_when_invalid_size(self, fitted_model, size):
        with pytest.raises(IllegalValueException) as ex:
            fitted_model.simulate(size=size, seed=1)

        assert str(ex.value) == f"The size '{size}' for the time series to be simulated is not valid, it must be greater than 0."

    def test_simulate_should_raise_exception_when_model_not_fitted(self, ar_model_with_max_order_6):
        with pytest.raises(ModelNotFittedException) as ex:
            ar_model_with_max_order_6.simulate(size=50, seed=1)

        assert str(ex.value) == "The model has not yet been fitted. Fit the model first by calling 'fit()'."


class TestSimulationSummary:

    # Expected training signs statistics
    EXPECTED_ORDER = 52
    EXPECTED_SIZE = 995093
    EXPECTED_PCT_BUY = 42.32
    EXPECTED_MEAN_NB_CONSECUTIVE_VALUES = 7.64
    EXPECTED_STD_NB_CONSECUTIVE_VALUES = 32.34
    EXPECTED_Q50_NB_CONSECUTIVE_VALUES = 2
    EXPECTED_Q75_NB_CONSECUTIVE_VALUES = 4
    EXPECTED_Q95_NB_CONSECUTIVE_VALUES = 34
    EXPECTED_Q99_NB_CONSECUTIVE_VALUES = 95

    @pytest.fixture(scope="function", autouse=True)
    def reset_singleton(self):
        yield
        Singleton._instances.clear()

    @pytest.mark.parametrize("fit_method", [FitMethodAR.YULE_WALKER, FitMethodAR.BURG, FitMethodAR.OLS_WITH_CST, FitMethodAR.MLE_WITHOUT_CST, FitMethodAR.MLE_WITH_CST])
    def test_simulation_summary(self, signs_btcusdt, fit_method):
        simulation_size = 2_000_000
        ar_model = AR(signs=signs_btcusdt, max_order=None, order_selection_method="pacf")
        ar_model = ar_model.fit(method=fit_method.value, significance_level=SIGNIFICANCE_LEVEL, check_residuals=True)
        actual_simulation = ar_model.simulate(size=simulation_size, seed=1)

        summary_df = ar_model.simulation_summary(plot=False, percentiles=(50.0, 75.0, 95.0, 99.0))
        assert ar_model._order == self.EXPECTED_ORDER

        # Checks that training signs statistics did not change
        assert len(signs_btcusdt) == self.EXPECTED_SIZE
        assert summary_df.loc["pct_buy (%)"]["Training"] == self.EXPECTED_PCT_BUY
        assert summary_df.loc["mean_nb_consecutive_values"]["Training"] == self.EXPECTED_MEAN_NB_CONSECUTIVE_VALUES
        assert summary_df.loc["std_nb_consecutive_values"]["Training"] == self.EXPECTED_STD_NB_CONSECUTIVE_VALUES
        assert summary_df.loc["Q50.0_nb_consecutive_values"]["Training"] == self.EXPECTED_Q50_NB_CONSECUTIVE_VALUES
        assert summary_df.loc["Q75.0_nb_consecutive_values"]["Training"] == self.EXPECTED_Q75_NB_CONSECUTIVE_VALUES
        assert summary_df.loc["Q95.0_nb_consecutive_values"]["Training"] == self.EXPECTED_Q95_NB_CONSECUTIVE_VALUES
        assert summary_df.loc["Q99.0_nb_consecutive_values"]["Training"] == self.EXPECTED_Q99_NB_CONSECUTIVE_VALUES

        # Checks that simulated signs are close to training signs statistics
        assert len(actual_simulation) == simulation_size
        expected_pct_buy = summary_df.loc["pct_buy (%)"]["Training"] if fit_method.has_cst_parameter else 50.0  # If the fit method does not include a constant parameter, we expect 50% of buy
        assert_allclose(actual=summary_df.loc["pct_buy (%)"]["Simulation"], desired=expected_pct_buy, rtol=0, atol=1.0, equal_nan=False)
        assert_allclose(actual=summary_df.loc["mean_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["mean_nb_consecutive_values"]["Training"], rtol=0, atol=0.25, equal_nan=False)
        assert_allclose(actual=summary_df.loc["std_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["std_nb_consecutive_values"]["Training"], rtol=0, atol=15, equal_nan=False)

        assert_allclose(actual=summary_df.loc["Q50.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q50.0_nb_consecutive_values"]["Training"], rtol=0, atol=1, equal_nan=False)
        assert_allclose(actual=summary_df.loc["Q75.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q75.0_nb_consecutive_values"]["Training"], rtol=0, atol=2, equal_nan=False)
        assert_allclose(actual=summary_df.loc["Q95.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q95.0_nb_consecutive_values"]["Training"], rtol=0, atol=3, equal_nan=False)
        assert_allclose(actual=summary_df.loc["Q99.0_nb_consecutive_values"]["Simulation"], desired=summary_df.loc["Q99.0_nb_consecutive_values"]["Training"], rtol=0, atol=6, equal_nan=False)

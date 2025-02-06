import pytest

from tradeflow.enums import FitMethodAR


@pytest.mark.parametrize("method, expected_name, expected_has_cst_parameter", [
    (FitMethodAR.YULE_WALKER, "yule_walker", False),
    (FitMethodAR.BURG, "burg", False),
    (FitMethodAR.OLS_WITH_CST, "ols_with_cst", True),
    (FitMethodAR.MLE_WITHOUT_CST, "mle_without_cst", False),
    (FitMethodAR.MLE_WITH_CST, "mle_with_cst", True)
])
def test_ar_fit_method(method, expected_name, expected_has_cst_parameter):
    assert method.value == expected_name
    assert method.has_cst_parameter == expected_has_cst_parameter

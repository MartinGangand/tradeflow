import pytest

from tradeflow.enums import FitMethodAR


@pytest.mark.parametrize("fit_ar_method, expected_name, expected_has_cst_parameter", [
    (FitMethodAR.YULE_WALKER, "yule_walker", False),
    (FitMethodAR.BURG, "burg", False),
    (FitMethodAR.CMLE_WITHOUT_CST, "cmle_without_cst", False),
    (FitMethodAR.CMLE_WITH_CST, "cmle_with_cst", True),
    (FitMethodAR.MLE_WITHOUT_CST, "mle_without_cst", False),
    (FitMethodAR.MLE_WITH_CST, "mle_with_cst", True)
])
def test_fit_method_ar_properties(fit_ar_method, expected_name, expected_has_cst_parameter):
    assert fit_ar_method.value == expected_name
    assert fit_ar_method.has_cst_parameter == expected_has_cst_parameter

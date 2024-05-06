from typing import List
from numbers import Number
import numpy as np

from ....utils.src.general_utils import check_condition
from ....exceptions.src.custom_exceptions import IllegalValueException

def ar_simulate(time_series: List[Number], parameters: List[Number], constant_parameter: float, size: int, seed: int | None) -> List[int]:
    order = len(parameters)
    check_condition(len(time_series) >= order, IllegalValueException(f"The size of the given time series ({len(time_series)}) must be greater or equal to the number of parameters ({order})."))
    check_condition(size > 0, IllegalValueException(f"The size '{size}' for the time series to be simulated is not valid, it must be greater than 0."))
    
    if (seed is not None):
        np.random.seed(seed=seed)

    previous_signs = time_series[-order:]
    for _ in range(size):
        next_sign_expected_value = compute_next_sign_expected_value(last_order_signs=previous_signs[-order:], parameters=parameters, constant_parameter=constant_parameter)
        next_sign_buy_proba = compute_next_sign_buy_proba(expected_value=next_sign_expected_value)
        next_sign = simulate_next_sign(buy_proba=next_sign_buy_proba)
        previous_signs.append(next_sign)

    simulated_signs = previous_signs[order:]
    assert(len(simulated_signs) == size)
    
    return simulated_signs

def compute_next_sign_expected_value(last_order_signs: List[int], parameters: List[Number], constant_parameter: float) -> float:
    assert(len(last_order_signs) == len(parameters))

    expected_value = constant_parameter
    for k in range(len(parameters)):
        expected_value += parameters[k] * last_order_signs[-k-1]
    return expected_value

def compute_next_sign_buy_proba(expected_value: float) -> float:
    buy_proba = 0.5 * (1 + expected_value)
    capped_proba = min(1, max(0, buy_proba))
    return capped_proba


def simulate_next_sign(buy_proba: float) -> int:
    return 1 if np.random.uniform() <= buy_proba else -1

from statsmodels.tsa.ar_model import ar_select_order
import statsmodels.tsa.stattools as stattools
from statsmodels.tools.typing import ArrayLike1D
from typing import Literal

def select_appropriate_nb_lags(time_series: ArrayLike1D):
    mod = ar_select_order(time_series, maxlag=100, ic="aic", trend="c")
    return len(mod.ar_lags)

def is_time_series_stationary(
    time_series: ArrayLike1D,
    significance_level : float = 0.05,
    max_lag: int | None = None,
    regression: Literal["c", "ct", "ctt", "n"] = "c",
    autolag: Literal["AIC", "BIC", "t-stat"] | None = None,
    verbose: bool = False
):
    df_test = stattools.adfuller(time_series, maxlag=max_lag, regression=regression, autolag=autolag)
    p_value = df_test[1]

    if (verbose):
       print(f"Test Statistic: {df_test[0]}")
       print(f"p-value: {df_test[1]}")
       print(f"#Lags Used: {df_test[2]}")
       print(f"Number of Observations Used: {df_test[3]}")

       for key, value in df_test[4].items():
           print(f"Critical Value ({key}): {value}")

    return p_value <= significance_level

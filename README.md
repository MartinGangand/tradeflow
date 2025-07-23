<h1 align="center">
<img src="https://raw.githubusercontent.com/MartinGangand/tradeflow/main/doc/_static/tradeflow_logo.svg" width="650" alt="Tradeflow Logo" />
</h1>

<p align="center">
  <a href="https://pypi.org/project/tradeflow/"><img alt="PyPI Latest Release" src="https://img.shields.io/pypi/v/tradeflow" /></a>
  <a href="https://pypi.org/project/tradeflow/"><img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/tradeflow.svg" /></a>
  <a href="https://github.com/MartinGangand/tradeflow/actions/workflows/ci.yml?query=branch%3Amain"><img alt="CI" src="https://github.com/MartinGangand/tradeflow/actions/workflows/ci.yml/badge.svg?branch=main" /></a>
  <a href="https://codecov.io/github/MartinGangand/tradeflow"><img alt="Coverage" src="https://codecov.io/github/MartinGangand/tradeflow/graph/badge.svg?token=T5Z95K8KRM" /></a>
</p>

As stated in the book _Trades, Quotes and Prices: Financial Markets Under the Microscope_ by Bouchaud et al. [[1, Chapter 10]](#1):

> *"The signs of arriving market orders have long-range autocorrelations."*

**tradeflow** is a Python package for fitting and simulating autocorrelated time series of signs.

## Features
* **Fit autoregressive (AR) models** to time series of signs:
  - Automatic model order selection using the Partial Autocorrelation Function (PACF)
  - Parameter estimation methods: Yule-Walker equations, Maximum Likelihood Estimation, and Burg's method
* **Simulate autocorrelated sign sequences** from fitted models
* **Summarize simulations** by comparing original and simulated time series:
  - Plot the Autocorrelation Function (ACF) and the Partial Autocorrelation Function (PACF)
  - Compute the proportion of buy signs ($+1$)
  - Compute descriptive statistics on consecutive sign runs (mean, standard deviation, percentiles)
* **Perform statistical tests**:
  - Augmented Dickey-Fuller (ADF) test for time series stationarity
  - Breusch-Godfrey test for residual autocorrelation

## Usage
Fit an autoregressive model to a time series of signs (e.g., `[1, 1, -1, -1, 1, -1, 1, 1, 1, 1, ...]`):

```python
from tradeflow import AR

ar_model = AR(signs=signs, max_order=50, order_selection_method='pacf')
ar_model.fit(method="yule_walker", check_stationarity=True, check_residuals=True)
```
<br>

Simulate an autocorrelated time series of signs from the fitted AR model:

```python
ar_model.simulate(size=10_000)
# [1, -1, 1, 1, 1, 1, -1, -1, 1, 1, ...]
```
<br>

Compare the ACF and PACF of the original and simulated time series:

```python
ar_model.simulation_summary(plot=True)
```

<img src="https://raw.githubusercontent.com/MartinGangand/tradeflow/main/doc/_static/simulation_summary.png" width="950" alt="Simulation summary" />

## Installation
tradeflow can be installed with pip:

```bash
pip install tradeflow
```

## Documentation
Read the full documentation [here](https://martingangand.github.io/tradeflow/).

## Background
This package is inspired by the book _Trades, Quotes and Prices: Financial Markets Under the Microscope_ by Bouchaud et al. [[1, Chapters 10 and 13]](#1).

The book discusses the highly persistent nature of the sequence of binary variables $\epsilon_t$ that describe the direction of market orders.
That is, buy orders ($\epsilon_t = +1$) tend to follow other buy orders, and sell orders ($\epsilon_t = -1$) tend to follow other sell orders, often for very long periods.

We assume that the time series of signs $\epsilon_t$ is well modelled by a **discrete autoregressive process** of order $p > 0$. In this framework, the best predictor of the next market order sign (just before it occurs) is a linear combination of the past signs:

```math
\hat{\epsilon}_t = \sum_{k=1}^{p} \mathbb{K}(k) \epsilon_{t-k}
```

Here, $\mathbb{K}(k)$ can be inferred from the sign autocorrelation function using the Yule-Walker equations.
$p$ determines how many past signs are used ($\forall \ell > p, \mathbb{K}(\ell) \approx 0$).

As a result, the probability that the next sign is $\epsilon_t$ is:

```math
\mathbb{P}_{t-1}(\epsilon_t) = \frac{1 + \epsilon_t \hat{\epsilon}_t}{2}
```

## References
<a id="1">[1]</a> 
Bouchaud J-P, Bonart J, Donier J, Gould M. _Trades, Quotes and Prices: Financial Markets Under the Microscope_. Cambridge University Press; 2018.

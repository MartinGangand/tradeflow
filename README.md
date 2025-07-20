<h1 align="center">
<img src="https://raw.githubusercontent.com/MartinGangand/tradeflow/improve-package-documentation/doc/_static/tradeflow_logo.svg" width="650" alt="Tradeflow Logo" />
</h1>

<p align="center">
  <a href="https://pypi.org/project/tradeflow/"><img alt="PyPI Latest Release" src="https://img.shields.io/pypi/v/tradeflow" /></a>
  <a href="https://pypi.org/project/tradeflow/"><img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/tradeflow.svg" /></a>
  <a href="https://github.com/MartinGangand/tradeflow/actions/workflows/ci.yml?query=branch%3Amain"><img alt="CI" src="https://github.com/MartinGangand/tradeflow/actions/workflows/ci.yml/badge.svg?branch=main" /></a>
  <a href="https://codecov.io/github/MartinGangand/tradeflow"><img alt="Coverage" src="https://codecov.io/github/MartinGangand/tradeflow/graph/badge.svg?token=T5Z95K8KRM" /></a>
</p>

tradeflow is a Python package that allows you to generate autocorrelated time series of signs.


## Features
* Fit autoregressive (AR) models to binary sign time series (parameter estimation methods include Yule-Walker, maximum likelihood, and Burg)
  - Automatic order selection using the Partial Autocorrelation Function (PACF).
  - Parameter estimation methods: Yule-Walker equations, Maximum Likelihood Estimation, Burg's method
* Simulation of autocorrelated sign sequences from fitted models
* Statistical summary (on consecutive sign runs) and visualization of original and simulated series
* Simulation summary:
  - ACF and PACF of original and simulated series
  - Statistics on consecutive sign runs
* Statistical tests:
  - Time series stationarity: Augmented Dickey-Fuller test (ADF)
  - Residual autocorrelation: Breusch-Godfrey test
* Plot autocorrelation (ACF) and partial autocorrelation (PACF) functions


## Usage
Fit an autoregressive model with a time series of signs (e.g, [1, 1, -1, -1, 1, -1, 1, 1, 1, 1, ...]).

```python
from tradeflow import AR

ar_model = AR(signs=signs, max_order=50, order_selection_method='pacf')
ar_model.fit(method="yule_walker", significance_level=.05, check_stationarity=True, check_residuals=True)  # Fit autoregressive model
```

Simulate an autocorrelated time series of signs:
```python
signs_simulation = ar_model.simulate(size=10_000)  # Simulate autocorrelated time series of signs
print(signs_simulation[:10])
# [-1, -1, 1, 1, 1, 1, 1, -1, 1, 1]
```

Compare the main statistics (count, percentage of buy signs) of the original signs and the simulated ones.
It also computes the mean and percentiles of the series counting the number of consecutive signs.
```python
ar_model.simulation_summary(percentiles=[50, 95, 99])
```

<img src="https://raw.githubusercontent.com/MartinGangand/tradeflow/improve-package-documentation/doc/_static/simulation_summary.png" width="600" alt="Simulation summary" />


## Installation
tradeflow can be installed with pip:

```bash
pip install tradeflow
```


## Background
The signs of arriving market orders have long-range autocorrelations(WHERE).

This package is inspired by the book "Trades, Quotes and Prices: Financial Markets Under the Microscope" by Bouchaud et al. [[1, Chapter 10 and 13]](#1), which discusses the highly persistent nature of the sequence of binary variables $\epsilon_t$ that describe the direction of market orders.
That is, buy orders ($\epsilon_t = +1$) tend to follow other buy orders, and sell orders ($\epsilon_t = -1$) tend to follow other sell orders, often for very long periods.

Empirical studies show that the autocorrelation function of market-order signs decays extremely slowly with the number of lags.

Assuming that time series of signs $\epsilon_t$ is well modelled by a discrete autoregressive process, the best predictor of the next sign, just before it happens, is a linear combination of the past signs:

$$\hat{\epsilon_t} = \sum_{k=1}^{p} \mathbb{K}(k) \epsilon_{t-k}$$

where $\mathbb{K}(k)$ can be inferred from the sign autocorrelation function using the Yule–Walker equation and ${p}>0$ is the order of the model (number of lags to include in the model), $\forall \ell > p, \mathbb{K}(\ell) = 0$.

Thus, the probability that the next sign is $\epsilon_t$ is then given by

$$\mathbb{P}_{t-1}(\epsilon_t) = \frac{1+\epsilon_t \hat{\epsilon_t}}{2}$$


## References
<a id="1">[1]</a> 
Bouchaud J-P, Bonart J, Donier J, Gould M. Trades, Quotes and Prices: Financial Markets Under the Microscope. Cambridge University Press; 2018.


## Documentation

Read the full documentation [here](https://martingangand.github.io/tradeflow/).

# tradeflow

[![Supported Versions](https://img.shields.io/pypi/pyversions/tradeflow.svg)](https://pypi.org/project/tradeflow/)
[![PyPI Version](https://img.shields.io/pypi/v/tradeflow)](https://pypi.org/project/tradeflow/)
[![CI](https://github.com/MartinGangand/tradeflow/actions/workflows/ci.yml/badge.svg)](https://github.com/MartinGangand/tradeflow/actions)
[![codecov](https://codecov.io/github/MartinGangand/tradeflow/graph/badge.svg?token=T5Z95K8KRM)](https://codecov.io/github/MartinGangand/tradeflow)

**tradeflow** is a library that lets you generate autocorrelated time series of signs.

## Installation
tradeflow is available on PyPI:

```bash
pip install tradeflow
```

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

OR

```python
>>> signs_simulation = ar_model.simulate(size=10_000)  # Simulate autocorrelated time series of signs
>>> print(signs_simulation[:10])
[-1, -1, 1, 1, 1, 1, 1, -1, 1, 1]
```

Compare the main statistics (count, percentage of buy signs) of the original signs and the simulated ones.
It also computes the mean and percentiles of the series counting the number of consecutive signs.
```python
ar_model.simulation_summary(percentiles=[50, 95, 99])
```
|                            |   Training |   Simulation |
|:---------------------------|-----------:|-------------:|
| size                       |  995093    |     10000    |
| pct_buy (%)                |      42.32 |        52.57 |
| mean_nb_consecutive_values |       7.64 |         7.66 |
| std_nb_consecutive_values  |      32.34 |        18.47 |
| Q50_nb_consecutive_values  |       2    |         2    |
| Q95_nb_consecutive_values  |      34    |        34    |
| Q99_nb_consecutive_values  |      95    |        99    |

![Simulation summary](doc/images/simulation_summary.png)

## Background
Autocorrelated time series are sequences where each value is statistically dependent on previous values.
`tradeflow` provides tools to fit autoregressive (AR) models to binary sign data, enabling realistic simulation and analysis of autocorrelated processes.

## Features
- Fit AR models to binary sign time series
- Automatic order selection using PACF
- Simulation of autocorrelated sign sequences
- Statistical summary and visualization tools
- Stationarity and residual checks

## Test image
|    | animal_1   | animal_2   |
|---:|:-----------|:-----------|
|  0 | elk        | dog        |
|  1 | pig        | quetzal    |
<picture align="center">
  <source media="(prefers-color-scheme: dark)" srcset="https://pandas.pydata.org/static/img/pandas_white.svg">
  <img alt="Pandas Logo" src="doc/images/simulation_summary.png">
</picture>

![Simulation summary](doc/images/simulation_summary.png)

<h1 align="center">
    <img src="doc/images/simulation_summary.png" width="300">
</h1><br>

## Documentation

Read the full documentation [here](https://martingangand.github.io/tradeflow/).

## License

Copyright (c) 2024 Martin Gangand

Distributed under the terms of the
[MIT](https://github.com/MartinGangand/tradeflow/blob/main/LICENSE) license.

# tradeflow : generate autocorrelated time series of signs

`tradeflow` lets you generate autocorrelated time series of signs.

## Installation

```
pip install tradeflow
```

## How to use
You can create an autoregressive model from a training time series of signs `time_series_signs`:

```
>>> import tradeflow
>>>
>>> ar_model = tradeflow.AR(signs=time_series_signs, max_order=50, order_selection_method='pacf', information_criterion=None)
```

To fit the model parameters, you have to call the `fit` function:

```
>>> ar_model.fit(method='yule_walker')
```

You can then easily simulate an autocorrelated time series of signs by calling the `simulate` function:
```
>>> simulated_signs = ar_model.simulate(size=15, seed=1)
>>> print(simulated_signs)
```

## Documentation

Read the full documentation [here](https://martingangand.github.io/tradeflow/).

## License

Copyright (c) 2024 Martin Gangand

Distributed under the terms of the
[MIT](https://github.com/MartinGangand/tradeflow/blob/main/LICENSE) license.

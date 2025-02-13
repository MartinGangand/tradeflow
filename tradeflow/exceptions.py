class IllegalNbLagsException(Exception):
    """Raised when the number of lags for a given time series is not valid"""
    pass


class IllegalValueException(Exception):
    """Raised when a value is not in a valid state"""
    pass


class ModelNotFittedException(Exception):
    """Raised when the model need the parameters, but it has not been fitted"""
    pass


class ModelNotSimulatedException(Exception):
    """Raised when the model need the simulated time series, but it has not been simulated"""
    pass


class NonStationaryTimeSeriesException(Exception):
    """Raised when the time series is not stationary"""
    pass


class AutocorrelatedResidualsException(Exception):
    """Raised when the residuals are autocorrelated, based on the result of a hypothesis test"""
    pass


class NoConvergenceException(Exception):
    """Raised when the method used to estimate model parameters failed to converge"""
    pass

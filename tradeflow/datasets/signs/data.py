from statsmodels.datasets import utils as du


def load():
    """
    Load trade signs data and returns a numpy ndarray.

    Returns
    -------
    Dataset
    """
    return load_pandas()


def load_pandas():
    """
    Load trade signs data and returns a numpy.ndarray.

    Returns
    -------
    Dataset
    """
    return _get_data().values


def _get_data():
    data = du.load_csv(__file__, 'signs.csv')
    data = data.iloc[:, 1]
    return data.astype(float)

import importlib.metadata
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import toml

ROOT_REPOSITORY = Path(__file__).parent.parent

package_data = toml.load(ROOT_REPOSITORY.joinpath("pyproject.toml"))["project"]
PACKAGE_NAME = package_data["name"]
VERSION = package_data["version"]


def test_end_to_end():
    # Remove tradeflow from the module search path (TODO: check that package not already installed by pip?)
    sys.path[:] = [path for path in sys.path if PACKAGE_NAME not in path]

    with pytest.raises(ModuleNotFoundError) as ex:
        import tradeflow
    assert str(ex.value) == "No module named 'tradeflow'"

    subprocess.check_call([sys.executable, "-m", "pip", "install", PACKAGE_NAME])
    installed_version = importlib.metadata.version(PACKAGE_NAME)
    assert installed_version == VERSION

    import tradeflow
    from tradeflow.common.logger_utils import get_logger
    DATA_FOLDER = Path(__file__).parent.joinpath("data")
    logger = get_logger(__file__)

    max_order = 100
    order_selection_method = "pacf"
    fit_method = "burg"
    seed = 1

    signs = np.loadtxt(DATA_FOLDER.joinpath("signs-20240720.txt"), dtype="int8", delimiter=",")
    logger.info(f"START")
    logger.info(f"max_order: {max_order} | order_selection_method: pacf | fit_method: {fit_method} | seed: {seed}")
    s2 = time.time()
    ar_model = tradeflow.AR(signs=signs, max_order=max_order, order_selection_method=order_selection_method)
    ar_model = ar_model.fit(method=fit_method, significance_level=0.05, check_residuals=True)

    ar_model.simulate(size=300_000, seed=seed)

    simulation_summary = ar_model.simulation_summary(plot=True, log_scale=True)
    logger.info(f"\n{simulation_summary}")
    e2 = time.time()
    logger.info(f"END | =====> TIME: {round(e2 - s2, 4)}s\n\n")

def test_a():
    assert 1 == 1

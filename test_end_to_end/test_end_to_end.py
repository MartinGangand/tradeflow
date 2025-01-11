import importlib.metadata
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import toml

ROOT_REPOSITORY = Path(__file__).parent.parent

package_info = toml.load(ROOT_REPOSITORY.joinpath("pyproject.toml"))["project"]
PACKAGE_NAME = package_info["name"]
VERSION = package_info["version"]

DATA_FOLDER = Path(__file__).parent.joinpath("data")


@pytest.fixture
def index(request):
    return request.config.getoption("--index")


def test_end_to_end_from_package_installation_to_simulation_of_signs(index):
    # Remove tradeflow from the module search path
    sys.path[:] = [path for path in sys.path if PACKAGE_NAME not in path]

    # Check that the package is not already  installed or can't be accessed
    with pytest.raises(ModuleNotFoundError) as ex:
        import tradeflow
    assert str(ex.value) == f"No module named '{PACKAGE_NAME}'"

    # Install package and check that the version corresponds to version of the recently uploaded package
    print(f"INSTALLING: https://{index}.org/simple/")
    if index == "test.pypi":
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--index-url", f"https://{index}.org/simple/", "--no-deps", "--no-cache-dir", PACKAGE_NAME])
    else:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--index-url", f"https://{index}.org/simple/", "--no-cache-dir", PACKAGE_NAME])
    installed_version = importlib.metadata.version(PACKAGE_NAME)
    assert installed_version == VERSION

    signs = np.loadtxt(DATA_FOLDER.joinpath("signs-20240720.txt"), dtype="int8", delimiter=",")

    import tradeflow
    ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")
    ar_model = ar_model.fit(method="burg", significance_level=0.05, check_residuals=True)

    ar_model.simulate(size=1_000_000, seed=1)
    ar_model.simulation_summary(plot=True, log_scale=True)

    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", PACKAGE_NAME])

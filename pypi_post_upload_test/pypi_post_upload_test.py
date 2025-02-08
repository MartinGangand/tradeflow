import importlib.metadata
import subprocess
import sys
from pathlib import Path
from typing import List

import numpy as np
import pytest
import toml

ROOT_REPOSITORY = Path(__file__).parent.parent
DATA_FOLDER = Path(__file__).parent.joinpath("data")


package_info = toml.load(ROOT_REPOSITORY.joinpath("pyproject.toml"))["project"]
PACKAGE_NAME = package_info["name"]

INDEX_URL_TEST_PYPI = "https://test.pypi.org/simple/"
FIT_METHODS_AR = ["yule_walker", "burg", "ols_with_cst", "mle_without_cst", "mle_with_cst"]


@pytest.fixture
def index(request):
    return request.config.getoption("--index")


@pytest.fixture
def expected_package_version(request):
    return request.config.getoption("--package_version")


@pytest.fixture(scope="function", autouse=True)
def uninstall_package():
    yield
    subprocess.check_call(parse_command_line(f"{sys.executable} -m pip uninstall -y {PACKAGE_NAME}"))


def test_package_installation_and_simulation_of_signs(index, expected_package_version):
    # Remove tradeflow from the module search path
    sys.path[:] = [path for path in sys.path if PACKAGE_NAME not in path]

    # Check that the package is not already installed or can't be accessed
    with pytest.raises(ModuleNotFoundError) as ex:
        import tradeflow
    assert str(ex.value) == f"No module named '{PACKAGE_NAME}'"

    # Install package and check that the installed version corresponds to the freshly uploaded package
    install_package(index=index)
    installed_package_version = importlib.metadata.version(PACKAGE_NAME)
    assert installed_package_version == expected_package_version

    for fit_method in FIT_METHODS_AR:
        signs = np.loadtxt(DATA_FOLDER.joinpath("signs-20240720.txt"), dtype="int8", delimiter=",")

        # Check package usage
        import tradeflow
        ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")
        ar_model = ar_model.fit(method=fit_method, significance_level=0.05, check_residuals=True)
        ar_model.simulate(size=1_000_000, seed=1)
        ar_model.simulation_summary(plot=True, log_scale=True)


def install_package(index: str) -> None:
    if index == "pypi":
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install --no-cache-dir {PACKAGE_NAME}"))
    elif index == "test.pypi":
        # Install package dependencies separately and then install the package from test.pypi without dependencies
        # 'pip install --index-url https://test.pypi.org/simple/ PACKAGE_NAME' does not work because it tries to install the package and its dependencies from index 'test.pypi' but some dependencies are not available
        # 'pip install --index-url https://test.pypi.org/simple/ PACKAGE_NAME --extra-index-url https://pypi.org/simple/' does not work because if the package is also available on index 'pypi', it will install it from there by default

        requirements_file = ROOT_REPOSITORY.joinpath("requirements.txt")
        assert requirements_file.is_file()
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install -r {str(requirements_file)}"))
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install --index-url {INDEX_URL_TEST_PYPI} --no-deps --no-cache-dir {PACKAGE_NAME}"))
    else:
        raise Exception(f"Unknown index {index}.")


def parse_command_line(command_line: str) -> List[str]:
    return command_line.split()

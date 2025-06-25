import argparse
import importlib.metadata
from pathlib import Path
from typing import List, Callable, Literal

import numpy as np
import sys

from scripts import config, utils

DATA_FOLDER = Path(__file__).parent.joinpath("data")

FIT_METHODS_AR = ["yule_walker", "burg", "cmle_without_cst", "cmle_with_cst", "mle_without_cst", "mle_with_cst"]


def basic_tradeflow_usage():
    """
    Run a basic usage test for the `tradeflow` package.

    The function loads sample sign data, fits an AR model using a various methods, simulates signs, and generates a simulation summary plot.

    This function is intended to verify that the core functionality of the `tradeflow` package works as expected after being uploaded to PyPi.
    """
    import tradeflow

    for fit_method in tradeflow.FitMethodAR:
    # for fit_method in FIT_METHODS_AR[:1]:
        signs = np.loadtxt(DATA_FOLDER.joinpath("signs-20240720.txt"), dtype="int8", delimiter=",")

        ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")
        ar_model = ar_model.fit(method=fit_method, significance_level=0.05, check_stationarity=True, check_residuals=True)
        ar_model.simulate(size=1_000_000, seed=1)
        ar_model.simulation_summary(plot=True, log_scale=True)


def main(index: Literal["pypi", "test.pypi"], package_name: str, package_version: str, install_default_version: bool, local_package_directory: Path, func_list: List[Callable]) -> None:
    """
    Main function to install a package from PyPI or Test PyPI, verify its installation, and run a list of validation functions.

    Parameters
    ----------
    index : {'pypi', 'test.pypi'}
        The package index to use for installation ('pypi' or 'test.pypi').
    package_name : str
        The name of the package to install and validate.
    package_version : str
        The version of the package to install and validate.
    install_default_version : bool
        If True, install the default/latest version. Otherwise, install the specified version.
    local_package_directory : Path
        The local directory of the package (used to remove from sys.path).
    func_list : list of Callable
        A list of functions to execute after installation for validation.
    """
    try:
        # Remove the local package directory from the module search path to ensure that the package is not imported from the local repository
        sys.path.remove(str(local_package_directory.parent))

        # Check that the package is not already installed or can't be accessed
        utils.uninstall_package_with_pip(package_name=package_name)
        utils.assert_package_not_importable(package_name=package_name)

        # Install package
        version_to_install = None if install_default_version else package_version
        utils.install_package_with_pip(package_name=package_name, index=index, version=version_to_install)

        # Check that the installed version corresponds to the expected version
        # TODO: create function in utils.py to check that the package is installed with the correct version
        # TODO:see if use version or package_version
        utils.assert_installed_package_version(package_name=package_name, expected_version=package_version)

        for func in func_list:
            func()
    finally:
        utils.uninstall_package_with_pip(package_name=package_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install the specified or default version of the package from index PyPi or Test PyPi and check that the package can be used correctly.")
    parser.add_argument("index", type=str, choices=["pypi", "test.pypi"], help="Specify the package index from which to install the package. Use 'pypi' for the main Python Package Index or 'test.pypi' for the testing instance.")
    parser.add_argument("package_version", type=str, help="Specify the package version.")
    parser.add_argument("--install_default_version", action="store_true", help="If True, don't specify any version to install (use default) and checks that the installed version is 'package_version'. If False, the specified version will be installed.")
    args = parser.parse_args()

    try:
        main(index=args.index,
             package_name=config.PACKAGE_NAME,
             package_version=args.package_version,
             install_default_version=args.install_default_version,
             local_package_directory=config.MAIN_PACKAGE_DIRECTORY,
             func_list=[basic_tradeflow_usage])
        print(f"Package '{config.PACKAGE_NAME}' version '{args.package_version}' installed successfully and basic usage test passed.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred while checking the package installation and usage: {e}")
        sys.exit(1)


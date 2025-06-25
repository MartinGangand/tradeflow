import argparse
import collections.abc
import importlib.metadata
import subprocess
from pathlib import Path
from typing import List, Optional, Callable

import numpy as np
import pytest
import sys

import scripts
from scripts.utils import uninstall_package_with_pip, assert_package_not_importable, install_package_with_pip

print("=====================PATHS==========================")
for p in sys.path:
    print(f"=== sys.path item: {p} ===")
print("=====================END==========================")
from scripts import config, utils

DATA_FOLDER = Path(__file__).parent.joinpath("data")

FIT_METHODS_AR = ["yule_walker", "burg", "cmle_without_cst", "cmle_with_cst", "mle_without_cst", "mle_with_cst"]


def basic_package_usage():
    import tradeflow
    from tradeflow.common.general_utils import get_enum_values

    # for fit_method in get_enum_values(tradeflow.OrderSelectionMethodAR):
    for fit_method in FIT_METHODS_AR[:1]:
        signs = np.loadtxt(DATA_FOLDER.joinpath("signs-20240720.txt"), dtype="int8", delimiter=",")

        ar_model = tradeflow.AR(signs=signs, max_order=100, order_selection_method="pacf")
        ar_model = ar_model.fit(method=fit_method, significance_level=0.05, check_stationarity=True, check_residuals=True)
        ar_model.simulate(size=1_000_000, seed=1)
        ar_model.simulation_summary(plot=True, log_scale=True)


def main(index: str, package_name: str, package_version: str, install_default_version: bool, local_package_directory: Path, func_list: List[Callable]) -> None:
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
        installed_package_version = importlib.metadata.version(package_name)
        if installed_package_version != package_version:
            raise Exception(f"Installed package version '{installed_package_version}' does not match expected version '{package_version}'.")

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
             func_list=[basic_package_usage])
        print(f"Package '{config.PACKAGE_NAME}' version '{args.package_version}' installed successfully and basic usage test passed.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred while checking the package installation and usage: {e}")
        sys.exit(1)


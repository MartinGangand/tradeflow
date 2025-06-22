import argparse
import collections.abc
import importlib.metadata
import subprocess
from pathlib import Path
from typing import List, Optional, Callable

import numpy as np
import pytest
import sys

print("=====================PATHS==========================")
for p in sys.path:
    print(f"=== sys.path item: {p} ===")
print("=====================END==========================")
from scripts import config

ROOT_REPOSITORY = Path(__file__).parent.parent
DATA_FOLDER = Path(__file__).parent.joinpath("data")

INDEX_URL_TEST_PYPI = "https://test.pypi.org/simple/"
FIT_METHODS_AR = ["yule_walker", "burg", "cmle_without_cst", "cmle_with_cst", "mle_without_cst", "mle_with_cst"]


def uninstall_package_with_pip(package_name: str):
    """Uninstall the package if it is installed."""
    subprocess.check_call(parse_command_line(f"{sys.executable} -m pip uninstall -y {package_name}"))


def main(index: str, package_name: str, package_version: str, install_default_version: bool, local_package_directory: Path, func_list: List[Callable]) -> None:
    try:
        # Remove the root repository from the module search path to ensure that the package is not imported from the local repository
        print("=====================PATHS==========================")
        for p in sys.path:
            print(f"=== sys.path item: {p} ===")
        print("=====================END==========================")
        print(f"????????? LOCAL_PACKAGE_DIRECTORY: {local_package_directory}?????????")
        print(f"!!!!!!!!! REMOVING: {local_package_directory.parent}!!!!!!!!!")
        sys.path.remove(str(local_package_directory.parent))

        # Check that the package is not already installed or can't be accessed
        uninstall_package_with_pip(package_name=package_name)
        assert_package_not_importable(package_name=package_name)

        # Install package and check that the installed version corresponds to the freshly uploaded package
        version_to_install = None if install_default_version else package_version
        install_package_with_pip(package_name=package_name, index=index, version=version_to_install)
        installed_package_version = importlib.metadata.version(package_name)
        assert installed_package_version == package_version, f"Installed package version '{installed_package_version}' does not match expected version '{package_version}'."

        for func in func_list:
            func()
    finally:
        uninstall_package_with_pip(package_name=package_name)


def install_package_with_pip(index: str, package_name: str, version: Optional[str]) -> None:
    version_part = f"=={version}" if version is not None else ""
    if index == "pypi":
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install --no-cache-dir {package_name}{version_part}"))
    elif index == "test.pypi":
        # Install package dependencies separately and then install the package from test.pypi without dependencies
        # 'pip install --index-url https://test.pypi.org/simple/ PACKAGE_NAME' does not work because it tries to install the package and its dependencies from index 'test.pypi' but some dependencies are not available
        # 'pip install --index-url https://test.pypi.org/simple/ PACKAGE_NAME --extra-index-url https://pypi.org/simple/' does not work because if the package is also available on index 'pypi', it will install it from there by default

        requirements_file = ROOT_REPOSITORY.joinpath("requirements.txt")
        assert requirements_file.is_file()
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install -r {str(requirements_file)}"))
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install --index-url {INDEX_URL_TEST_PYPI} --no-deps --no-cache-dir {package_name}{version_part}"))
    else:
        raise Exception(f"Unknown index {index}.")


def assert_package_not_importable(package_name: str) -> None:
    with pytest.raises(ModuleNotFoundError) as ex:
        importlib.import_module(package_name)
    assert str(ex.value) == f"No module named '{package_name}'"


def parse_command_line(command_line: str) -> List[str]:
    return command_line.split()


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
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)


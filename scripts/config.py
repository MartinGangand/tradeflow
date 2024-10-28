from pathlib import Path

import toml

REPOSITORY_ROOT = Path(__file__).parent.parent
LIBRARIES_DIRECTORY_NAME = "lib"

package_data = toml.load(REPOSITORY_ROOT.joinpath("pyproject.toml"))["project"]
PACKAGE_NAME = package_data["name"]
VERSION = package_data["version"]

EXPECTED_SHARED_LIBRARIES = ["tradeflow/libtradeflow"]
EXPECTED_NB_WHEELS = 55

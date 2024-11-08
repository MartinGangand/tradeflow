import os.path
from pathlib import Path

import toml

ROOT_REPOSITORY = Path(__file__).parent.parent

package_data = toml.load(ROOT_REPOSITORY.joinpath("pyproject.toml"))["project"]
PACKAGE_NAME = package_data["name"]
VERSION = package_data["version"]

MAIN_PACKAGE_DIRECTORY = ROOT_REPOSITORY.joinpath(PACKAGE_NAME)
SUBPACKAGES_DIRECTORIES = [MAIN_PACKAGE_DIRECTORY.joinpath("common")]

EXPECTED_SHARED_LIBRARIES = [os.path.join(PACKAGE_NAME, "libtradeflow")]
EXPECTED_NB_WHEELS = 55

import os.path
from pathlib import Path

import toml

ROOT_REPOSITORY = Path(__file__).parent.parent

package_info = toml.load(ROOT_REPOSITORY.joinpath("pyproject.toml"))["project"]
PACKAGE_NAME = package_info["name"]

MAIN_PACKAGE_DIRECTORY = ROOT_REPOSITORY.joinpath(PACKAGE_NAME)
SUBPACKAGES_DIRECTORIES = [MAIN_PACKAGE_DIRECTORY.joinpath("common")]

EXPECTED_SHARED_LIBRARIES = [os.path.join(PACKAGE_NAME, "libtradeflow")]
EXPECTED_NB_WHEELS = 72

INDEX_URL_TEST_PYPI = "https://test.pypi.org/simple/"

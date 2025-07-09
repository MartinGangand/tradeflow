import importlib
import io
import os
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import List, Optional, Literal, Union

import requests
import sys
import time
from requests import Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scripts import config
from scripts.config import INDEX_URL_TEST_PYPI

ANY_VALID_STRING = r"[^'\"\s]+"
DEFAULT_SLEEP_TIME_SECONDS = 5


def get_response(url: str) -> Response:
    """
    Return the response of a request for a given url.

    Parameters
    ----------
    url : str
        The url for which to make a request.

    Returns
    -------
    Response
        The response of the request.

    Raises
    ------
    Exception
        If the request is unsuccessful.
    """
    response = requests.get(url=url)
    if not response.ok:
        raise Exception(f"Request for url {url} was unsuccessful")

    return response


def html_page_as_string(url: str) -> str:
    """
    Return the content of an html page as a string.

    Parameters
    ----------
    url : str
        The url of the html page.

    Returns
    -------
    str
        The content of the html page.

    Raises
    ------
    Exception
        If the request is unsuccessful.
    """
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url=url)
        time.sleep(DEFAULT_SLEEP_TIME_SECONDS)
        html_page = driver.page_source
    finally:
        driver.quit()

    return html_page


def fetch_file_names_from_tar_gz(url: str) -> List[str]:
    """
    Return the file names contained in a tar.gz file.

    Parameters
    ----------
    url : str
        The url of the tar.gz file.

    Returns
    -------
    list of str
        The file names contained in the tar.gz file.

    Raises
    ------
    Exception
        If the request is unsuccessful.
    """
    response = get_response(url=url)
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar_file:
        file_names = tar_file.getnames()
        return file_names


def fetch_file_names_from_zip(url: str) -> List[str]:
    """
    Return the file names contained in a zip file.

    Parameters
    ----------
    url : str
        The url of the zip file.

    Returns
    -------
    list of str
        The file names contained in the zip file.

    Raises
    ------
    Exception
        If the request is unsuccessful.
    """
    response = get_response(url=url)
    with zipfile.ZipFile(io.BytesIO(response.content), mode="r") as zip_file:
        file_names = zip_file.namelist()
        return file_names


def find_urls_in_html_page(html_page_content: str, target_url_extension: str) -> List[str]:
    """
    Return urls with a given extension contained in an html page.

    Parameters
    ----------
    html_page_content : str
        The content of the html page.
    target_url_extension : str
        The url extension to look for in the html page (e.g. whl).

    Returns
    -------
    list of str
        Urls with the given `target_url_extension` extension contained in the html page.
    """
    urls = re.findall(pattern=rf"https:{ANY_VALID_STRING}\.{target_url_extension}\b", string=html_page_content)
    return sorted(list(set(urls)))


def find_files_in_directories(directories: List[Path], extensions: List[str], recursive: bool, absolute_path: bool) -> List[str]:
    """
    Find files within specified directories that match given file extensions.

    Parameters
    ----------
    directories : list of Path
        The directories to search for files.
    extensions : list of str
        A list of file extensions to filter files by (without dots). Files with
        matching extensions will be included in the results.
    recursive : bool
        If True, search subdirectories recursively. If False, only search within
        the specified directory.
    absolute_path : bool
        If True, returns absolute file paths. If False, returns paths relative
        to the specified `directory`.

    Returns
    -------
    list of str
        A list of file paths as strings that match the specified extensions.
        The paths are either absolute or relative depending on the `absolute_path` parameter.
    """
    extensions = {f".{ext}" for ext in extensions}
    files = set()
    for directory in directories:
        glob_function = directory.rglob if recursive else directory.glob
        for file_path in glob_function(pattern="*"):
            if not (file_path.is_file() and file_path.suffix in extensions):
                continue

            if not absolute_path:
                file_path = file_path.relative_to(directory)

            files.add(str(file_path))

    return sorted(files)


def find_file_names_with_given_extensions(file_names: List[str], potential_extensions: List[str]) -> List[str]:
    """
    Find file names with an extension in `potential_extensions`.

    Parameters
    ----------
    file_names : list of str
        The file names for which to search files with the given extensions.
    potential_extensions : list of str
        The extensions for which to look for in the given files.

    Returns
    -------
    list of str
        File names with an extension contained in `potential_extensions`.
    """
    joined_extensions = "|".join(potential_extensions)
    matched_file_names = []
    for file_name in file_names:
        if re.search(pattern=rf"{ANY_VALID_STRING}\.(?:{joined_extensions})$", string=file_name) is not None:
            matched_file_names.append(file_name)
    return matched_file_names


def file_names_with_prefixes(file_names: List[str], *prefixes) -> List[str]:
    """
    Generate file paths by prepending a common prefix or multiple prefixes to a list of file names.

    Parameters
    ----------
    file_names : list of str
        A list of file names as strings.
    *prefixes : str
        One or more prefix strings. If multiple prefixes are provided, they are joined
        using `os.path.join()` to create a single path prefix.

    Returns
    -------
    list of str
        A list of file paths with each file name prepended by the constructed prefix.
    """
    prefix = ""
    if len(prefixes) == 1:
        prefix = prefixes[0]
    elif len(prefixes) > 1:
        prefix = os.path.join(prefixes[0], *prefixes[1:])
    return [os.path.join(prefix, file_name) for file_name in file_names]


def paths_relative_to(paths: Union[List[str], List[Path]], relative_to: Union[str, Path]) -> List[str]:
    """
    Return a list of paths relative to a given base path.

    Parameters
    ----------
    paths : list of str or list of Path
        The list of paths to convert to relative paths.
    relative_to : str or Path
        The base path to which the paths should be made relative.

    Returns
    -------
    list of str
        The list of paths as strings, each relative to `relative_to`.
    """
    return [str(Path(path).relative_to(relative_to)) for path in paths]


def parse_command_line(command_line: str) -> List[str]:
    """
    Split a command line string into a list of arguments.

    Parameters
    ----------
    command_line : str
        The command line string to split.

    Returns
    -------
    list of str
        The list of command line arguments.
    """
    return command_line.split()


def uninstall_package_with_pip(package_name: str) -> None:
    """
    Uninstall a package using pip.

    Parameters
    ----------
    package_name : str
        The name of the package to uninstall.
    """
    subprocess.check_call(parse_command_line(f"{sys.executable} -m pip uninstall -y {package_name}"))


def install_package_with_pip(index: Literal["pypi", "test.pypi"], package_name: str, package_version: Optional[str]) -> None:
    """
    Install a package using pip from the specified index.

    Parameters
    ----------
    index : {'pypi', 'test.pypi'}
        The package index to use for installation ('pypi' or 'test.pypi').
    package_name : str
        The name of the package to install.
    package_version : str or None
        The version of the package to install. If None, installs the latest version.

    Raises
    ------
    Exception
        If the index is unknown or installation fails.
    """
    version_part = f"=={package_version}" if package_version is not None else ""
    if index == "pypi":
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install --no-cache-dir {package_name}{version_part}"))
    elif index == "test.pypi":
        # Install package dependencies separately and then install the package from test.pypi without dependencies
        # 'pip install --index-url https://test.pypi.org/simple/ package_name' does not work because it tries to install the package and its dependencies from index 'test.pypi' but some dependencies are not available
        # 'pip install --index-url https://test.pypi.org/simple/ package_name --extra-index-url https://pypi.org/simple/' does not work because if the package 'package_name' is also available on index 'pypi', it will install it from there by default

        # Install dependencies from pypi
        requirements_file = config.ROOT_REPOSITORY.joinpath("requirements.txt")
        assert requirements_file.is_file()
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install -r {str(requirements_file)}"))

        # Install the package from test.pypi without dependencies
        # Install setuptools
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install setuptools>=61.0,<72.1.0"))
        subprocess.check_call(parse_command_line(f"{sys.executable} -m pip install --index-url {INDEX_URL_TEST_PYPI} --no-deps --no-cache-dir {package_name}{version_part}"))
    else:
        raise Exception(f"Can't install package '{package_name}' version '{package_version}' from unknown index '{index}'.")


def assert_package_not_importable(package_name: str) -> None:
    """
    Assert that a package is not importable.

    Parameters
    ----------
    package_name : str
        The name of the package to check.

    Raises
    ------
    RuntimeError
        If the package is importable (i.e., already installed or accessible from the local repository).
    """
    try:
        importlib.import_module(package_name)
    except ImportError:
        # ImportError is raised if the package is not installed or not accessible
        return
    else:
        # If we reach this point, the package is importable
        raise RuntimeError(f"Package '{package_name}' is already installed or accessible, but it should not be.")


def verify_installed_package_version(package_name: str, expected_package_version: str) -> None:
    """
    Assert that the installed version of a package matches the expected version.

    Parameters
    ----------
    package_name : str
        The name of the package to check.
    expected_package_version : str
        The expected version of the package.

    Raises
    ------
    Exception
        If the installed version does not match the expected version.
    """
    installed_version = importlib.metadata.version(package_name)
    if installed_version != expected_package_version:
        raise Exception(f"Installed version '{installed_version}' of package '{package_name}' does not match expected version '{expected_package_version}'.")

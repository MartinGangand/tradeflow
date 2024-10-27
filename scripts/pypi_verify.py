from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List

import toml

from scripts.utils import fetch_file_names_from_tar_gz, find_file_names_with_given_extensions, html_page_as_string, \
    find_urls_in_html_page, find_files_in_directory, file_names_with_prefixes, fetch_file_names_from_zip, \
    ANY_VALID_STRING

REPOSITORY_ROOT = Path(__file__).parent.parent
LIB_DIRECTORY_NAME = "lib"

PACKAGE_NAME = toml.load(REPOSITORY_ROOT.joinpath("pyproject.toml"))["project"]["name"]
VERSION = toml.load(REPOSITORY_ROOT.joinpath("pyproject.toml"))["project"]["version"]
PACKAGE_DIR = REPOSITORY_ROOT.joinpath(PACKAGE_NAME)

PYTHON_EXTENSION = "py"
CPP_EXTENSION = "cpp"
HEADER_EXTENSION = "h"

WHEEL_EXTENSION = "whl"
SOURCE_EXTENSION = "tar.gz"

LINUX = "linux"
MACOS = "macosx"
WINDOWS = "win"

SO_EXTENSION = "so"
DLL_EXTENSION = "dll"
DYLIB_EXTENSION = "dylib"

PASSED = "PASSED"

EXPECTED_SHARED_LIBRARIES = ["tradeflow/libtradeflow"]
EXPECTED_NB_WHEELS = 55


def verify_source(source_url: str, package_name: str, version: str, expected_python_files: List[str], expected_cpp_files: List[str]) -> None:
    """
    Verify a source file containing a PyPi package from an url.

    Parameters
    ----------
    source_url : str
        The url of the source (tar.gz file).
    package_name : str
        The name of the PyPi package.
    version : str
        The version of the PyPi package.
    expected_python_files : list of str
        Python files that the source is expected to contain.
    expected_cpp_files : list of str
        C++ files (cpp and h) that the source is expected to contain.

    Raises
    ------
    Exception
        If the source url is incorrect or the files contained in the source differ from the expected ones.
    """
    print(f"Starting to verify source {source_url}")
    verify_source_url(source_url=source_url, package_name=package_name, version=version)

    file_names = fetch_file_names_from_tar_gz(url=source_url)
    print(f"    Fetched source file names ({file_names})")

    actual_python_files = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[PYTHON_EXTENSION])
    actual_python_files.remove(os.path.join(f"{package_name}-{version}", "setup.py"))
    verify_files(expected_files=expected_python_files, actual_files=actual_python_files, object_name="source", file_type="python")

    actual_cpp_files = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[CPP_EXTENSION, HEADER_EXTENSION])
    verify_files(expected_files=expected_cpp_files, actual_files=actual_cpp_files, object_name="source", file_type="cpp or header")


def verify_source_url(source_url: str, package_name: str, version: str) -> None:
    """
    Verify that source url is correct for a given package name and version.

    Parameters
    ----------
    source_url : str
        The url of the source (tar.gz file).
    package_name : str
        The name of the PyPi package.
    version : str
        The version of the PyPi package.

    Raises
    ------
    Exception
        If the source url is incorrect.
    """
    expected_source_name = f"{package_name}-{version}.{SOURCE_EXTENSION}"
    actual_source_name = source_url.split("/")[-1]
    if actual_source_name != expected_source_name:
        # TODO: improve message: quotes for but was + mention url
        raise Exception(f"expected source distribution url to contain '{expected_source_name}', but was '{actual_source_name}'")

    log_valid(message="Source url")


def verify_wheel(wheel_url: str, package_name: str, version: str, expected_shared_libraries: List[str], expected_python_files: List[str]) -> None:
    """
    Verify a wheel file containing a PyPi package from an url.

    Parameters
    ----------
    wheel_url : str
        The url of the wheel (whl file).
    package_name : str
        The name of the PyPi package.
    version : str
        The version of the PyPi package.
    expected_shared_libraries : list of str
        Names of shared libraries that the wheel is expected to contain.
    expected_python_files : list of str
        Python files that the source is expected to contain.

    Raises
    ------
    Exception
        If the wheel url is incorrect or the files contained in the wheel differ from the expected ones.
    """
    print(f"Starting to verify wheel {wheel_url}")
    verify_wheel_url(wheel_url=wheel_url, package_name=package_name, version=version)

    expected_shared_lib_ext = expected_wheel_shared_libraries_extension(wheel_url=wheel_url)
    file_names = fetch_file_names_from_zip(url=wheel_url)
    print(f"    Fetched wheel file names ({file_names})")

    expected_shared_libs = [f"{shared_lib}.{expected_shared_lib_ext}" for shared_lib in expected_shared_libraries]

    actual_shared_libraries = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[SO_EXTENSION, DLL_EXTENSION, DYLIB_EXTENSION])
    verify_files(expected_files=expected_shared_libs, actual_files=actual_shared_libraries, object_name="wheel", file_type="shared library")

    actual_python_files = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[PYTHON_EXTENSION])
    verify_files(expected_files=expected_python_files, actual_files=actual_python_files, object_name="wheel", file_type="python")


def verify_wheel_url(wheel_url: str, package_name: str, version: str) -> None:
    """
    Verify that wheel url is correct for a given package name and version.

    Parameters
    ----------
    wheel_url : str
        The url of the wheel (whl file).
    package_name : str
        The name of the PyPi package.
    version : str
        The version of the PyPi package.

    Raises
    ------
    Exception
        If the wheel url is incorrect.
    """
    wheel_pattern = rf"{package_name}-{version}-{ANY_VALID_STRING}\.{WHEEL_EXTENSION}\b"
    match = re.search(pattern=wheel_pattern, string=wheel_url)
    if match is None:
        raise Exception(f"expected wheel url '{wheel_url}' to match the pattern '{wheel_pattern}'")

    log_valid(message="Wheel url")


def expected_wheel_shared_libraries_extension(wheel_url: str) -> str:
    """
    Return the expected extension (so, dylib or dll) for shared libraries in a wheel.

    Parameters
    ----------
    wheel_url : str
        The url of the wheel (whl file).

    Returns
    -------
    str
        The expected extension for shared libraries in a wheel.

    Raises
    ------
    Exception
        If the expected shared library extension can't be inferred from the wheel url.
    """
    if not (LINUX in wheel_url or MACOS in wheel_url or WINDOWS in wheel_url):
        raise Exception(f"The wheel name does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")

    extension = ""
    if LINUX in wheel_url:
        extension = SO_EXTENSION
    elif MACOS in wheel_url:
        extension = DYLIB_EXTENSION
    elif WINDOWS in wheel_url:
        extension = DLL_EXTENSION

    print(f"    Wheel shared library extension: {extension}")
    return extension


def verify_files(expected_files: List[str], actual_files: List[str], object_name: str, file_type: str) -> None:
    """
    Verify if `expected_files` and `actual_files` have the same content, otherwise raise an exception.

    Parameters
    ----------
    expected_files : list of str
        The expected file names.
    actual_files : list of str
        The actual file names.
    object_name : str
        The name of the object being manipulated (e.g. wheel), for logging purpose.
    file_type : str
        The type of files being manipulated (e.g. Python), for logging purpose.

    Raises
    ------
    Exception
        If the actual files differ from the expected files.
    """
    if sorted(actual_files) != sorted(expected_files):
        raise Exception(f"expected {object_name} to contain {len(expected_files)} {file_type} file(s) ({expected_files}), but found {len(actual_files)} ({actual_files}) instead")

    log_valid(message=f"Verify {object_name} {file_type} files")


def display_name(url: str, package_name: str, version: str) -> str:
    """
    Try to infer a display name from an url for a given package name and version.

    Parameters
    ----------
    url : str
        The url for which to infer a display name.
    package_name : str
        The name of the PyPi package.
    version : str
        The version of the PyPi package.

    Returns
    -------
    str
        The inferred display name or the initial url if unable to do so.
"""
    name = re.findall(pattern=rf"{package_name}-{version}{ANY_VALID_STRING}", string=url)
    if len(name) != 1:
        return url

    return name[0]


def log_valid(message: str) -> None:
    print(f"    {message}: OK")


def main(index: str, package_name: str, version: str, expected_nb_wheels: int, expected_shared_libraries: List[str], repository: Path) -> int:
    package_dir = repository.joinpath(package_name)
    lib_dir = repository.joinpath(LIB_DIRECTORY_NAME)
    package_and_version = f"{package_name}-{version}"

    package_url = f"https://{index}.org/project/{package_name}/{version}/#files"
    print(f"Starting {os.path.basename(__file__)} script for index '{index}' (url: {package_url})\n")

    pypi_html_page = html_page_as_string(url=package_url)
    source_urls = find_urls_in_html_page(html_page_content=pypi_html_page, target_url_extension=SOURCE_EXTENSION)
    wheel_urls = find_urls_in_html_page(html_page_content=pypi_html_page, target_url_extension=WHEEL_EXTENSION)

    if len(source_urls) != 1:
        raise Exception(f"Expected 1 source url in the html page, but found {len(source_urls)} instead")

    if len(wheel_urls) != expected_nb_wheels:
        raise Exception(f"Expected {expected_nb_wheels} wheel url{'s' if expected_nb_wheels > 1 else ''} in the html page, but found {len(wheel_urls)} instead")

    exit_status = 0
    source_url = source_urls[0]
    source_name = display_name(url=source_url, package_name=package_name, version=version)

    expected_source_python_files = find_files_in_directory(directory=package_dir, extensions=[PYTHON_EXTENSION], recursive=False, absolute_path=False)
    expected_source_python_files_with_prefixes = file_names_with_prefixes(expected_source_python_files, os.path.join(package_and_version, package_name))

    expected_source_cpp_files = find_files_in_directory(directory=lib_dir, extensions=[CPP_EXTENSION, HEADER_EXTENSION], recursive=True, absolute_path=False)
    expected_source_cpp_files_with_prefixes = file_names_with_prefixes(expected_source_cpp_files, os.path.join(package_and_version, LIB_DIRECTORY_NAME))
    try:
        verify_source(source_url=source_url, package_name=package_name, version=version, expected_python_files=expected_source_python_files_with_prefixes, expected_cpp_files=expected_source_cpp_files_with_prefixes)
    except Exception as source_exception:
        exit_status += 1
        print(f"{source_name}: {source_exception}\n")
    else:
        print(f"{source_name}: {PASSED}\n")

    expected_wheel_python_files = find_files_in_directory(directory=package_dir, extensions=[PYTHON_EXTENSION], recursive=False, absolute_path=False)
    expected_wheel_python_files_with_prefix = file_names_with_prefixes(expected_wheel_python_files, package_name)
    for wheel_url in wheel_urls:
        wheel_name = display_name(url=wheel_url, package_name=package_name, version=version)
        try:
            verify_wheel(wheel_url=wheel_url, package_name=package_name, version=version, expected_shared_libraries=expected_shared_libraries, expected_python_files=expected_wheel_python_files_with_prefix)
        except Exception as wheel_exception:
            exit_status += 1
            print(f"{wheel_name}: {wheel_exception}\n")
        else:
            print(f"{wheel_name}: {PASSED}\n")

    return exit_status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify the content of uploaded package to PyPi or Test PyPi")
    parser.add_argument("index", type=str, choices=["pypi", "test.pypi"], help="Whether to use the PyPi or Test PyPi package index")
    args = parser.parse_args()

    try:
        sys.exit(main(index=args.index, package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=EXPECTED_NB_WHEELS, expected_shared_libraries=EXPECTED_SHARED_LIBRARIES, repository=REPOSITORY_ROOT))
    except Exception as e:
        print(e)
        sys.exit(1)

    # TODO: Log with logger or print?
    # TODO: common function for the main because same behavior for wheel and source with exception etc (function with args: function, etc (what takes verify_source() and verify_wheel()))
    # TODO: add verification for the source: check that there are python files? + cpp files?
    # TODO: add verification for the wheel: check that there are python files?
    # TODO: add doc?
    # TODO: in get_shared_library_file(), with cmake the shared lib name is libtradeflow.?, do no longer need to search for pattern. Directly search for the file with exact name?



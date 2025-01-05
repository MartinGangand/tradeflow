import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Literal

from scripts import config
from scripts.file_extensions import FileExtension
from scripts.utils import fetch_file_names_from_tar_gz, find_file_names_with_given_extensions, html_page_as_string, \
    find_urls_in_html_page, find_files_in_directories, fetch_file_names_from_zip, \
    ANY_VALID_STRING, paths_relative_to

LINUX = "linux"
MACOS = "macosx"
WINDOWS = "win"

PASSED = "PASSED"


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
    log_message("Starting to verify source distribution")
    package_and_version = f"{package_name}-{version}"

    verify_source_url(source_url=source_url, package_name=package_name, version=version)

    file_names = fetch_file_names_from_tar_gz(url=source_url)
    log_indented_message(f"Fetched {len(file_names)} file names from the source")

    actual_python_files = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[FileExtension.PYTHON_EXTENSION])
    actual_python_files.remove(os.path.join(f"{package_name}-{version}", "setup.py"))
    actual_python_files = paths_relative_to(paths=actual_python_files, relative_to=package_and_version)

    compare_expected_vs_actual_files(expected_files=expected_python_files, actual_files=actual_python_files, object_name="source", file_type="python")

    actual_cpp_files = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[FileExtension.CPP_EXTENSION, FileExtension.HEADER_EXTENSION])
    actual_cpp_files = paths_relative_to(paths=actual_cpp_files, relative_to=package_and_version)
    compare_expected_vs_actual_files(expected_files=expected_cpp_files, actual_files=actual_cpp_files, object_name="source", file_type="cpp or header")


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
    expected_source_name = f"{package_name}-{version}.{FileExtension.SOURCE_EXTENSION}"
    actual_source_name = source_url.split("/")[-1]
    if actual_source_name != expected_source_name:
        raise Exception(f"expected source distribution url to end with '{expected_source_name}', but was '{source_url}'")

    log_indented_message(message=f"Source url: OK")


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
    log_message(f"Starting to verify wheel {display_name(url=wheel_url, package_name=package_name, version=version)}")
    verify_wheel_url(wheel_url=wheel_url, package_name=package_name, version=version)

    expected_shared_library_extension = expected_wheel_shared_libraries_extension(wheel_url=wheel_url)
    file_names = fetch_file_names_from_zip(url=wheel_url)
    log_indented_message(f"Fetched {len(file_names)} file names from the wheel")

    expected_shared_libraries_with_extension = [f"{expected_shared_library}.{expected_shared_library_extension}" for expected_shared_library in expected_shared_libraries]
    actual_shared_libraries = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[FileExtension.SO_EXTENSION, FileExtension.DLL_EXTENSION, FileExtension.DYLIB_EXTENSION])
    compare_expected_vs_actual_files(expected_files=expected_shared_libraries_with_extension, actual_files=actual_shared_libraries, object_name="wheel", file_type="shared library")

    actual_python_files = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[FileExtension.PYTHON_EXTENSION])
    compare_expected_vs_actual_files(expected_files=expected_python_files, actual_files=actual_python_files, object_name="wheel", file_type="python")


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
    wheel_pattern = rf"{package_name}-{version}-{ANY_VALID_STRING}\.{FileExtension.WHEEL_EXTENSION}\b"
    match = re.search(pattern=wheel_pattern, string=wheel_url)
    if match is None:
        raise Exception(f"expected wheel url '{wheel_url}' to match the pattern '{wheel_pattern}'")

    log_indented_message(message="Wheel url: OK")


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
        The expected extension for shared libraries in the wheel.

    Raises
    ------
    Exception
        If the expected shared library extension can't be inferred from the wheel url.
    """
    ""
    if LINUX in wheel_url:
        extension = FileExtension.SO_EXTENSION
    elif MACOS in wheel_url:
        extension = FileExtension.DYLIB_EXTENSION
    elif WINDOWS in wheel_url:
        extension = FileExtension.DLL_EXTENSION
    else:
        raise Exception(f"The wheel name does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")

    log_indented_message(f"Wheel shared library extension: {extension}")
    return extension


def compare_expected_vs_actual_files(expected_files: List[str], actual_files: List[str], object_name: str, file_type: str) -> None:
    """
    Verify if `expected_files` and `actual_files` contain the same file names, otherwise raise an exception.

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

    log_indented_message(message=f"Verify {object_name} {file_type} files: OK")


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


def log_message(message: str) -> None:
    print(f"{message}")


def log_valid(name: str):
    log_message(f"{name}: {PASSED}\n")


def log_error(name: str, exception: Exception):
    log_message(f"{name}: {exception}\n")


def log_indented_message(message: str) -> None:
    log_message(f"    {message}")


def main(index: Literal["pypi", "test.pypi"], package_name: str, version: str, expected_nb_wheels: int, expected_shared_libraries: List[str], root_repository: Path, main_package_directory: Path, subpackage_directories: List[Path]) -> int:
    """
    Main function to validate package files against expected specifications on a given index.

    Parameters
    ----------
    index : {"pypi", "test.pypi"}
        The name of the package index to check for package availability. Must be either "pypi" or "test.pypi".
    package_name : str
        The name of the package to validate.
    version : str
        The version of the package to validate.
    expected_nb_wheels : int
        The expected number of wheel files for this package version on the index.
    expected_shared_libraries : list of str
        A list of shared library file names expected within the wheel.
    root_repository : Path
        The root directory of the repository containing the package and libraries.
    main_package_directory : str
        The directory of the main package.
    subpackage_directories : str
        The directories of subpackages contained in `main_package_directory` (if any).

    Returns
    -------
    int
        The number of errors encountered during the validation process.

    Raises
    ------
    Exception
        If the number of source URLs or wheel URLs found does not match the expected counts.
    """
    nb_errors = 0
    package_url = f"https://{index}.org/project/{package_name}/{version}/#files"
    log_message(f"Starting {os.path.basename(__file__)} script for index '{index}' (url: {package_url})\n")

    pypi_html_page = html_page_as_string(url=package_url)
    source_urls = find_urls_in_html_page(html_page_content=pypi_html_page, target_url_extension=FileExtension.SOURCE_EXTENSION)
    wheel_urls = find_urls_in_html_page(html_page_content=pypi_html_page, target_url_extension=FileExtension.WHEEL_EXTENSION)

    if len(source_urls) != 1:
        raise Exception(f"Expected 1 source url in the html page, but found {len(source_urls)} instead")

    if len(wheel_urls) != expected_nb_wheels:
        raise Exception(f"Expected {expected_nb_wheels} wheel url{'s' if expected_nb_wheels > 1 else ''} in the html page, but found {len(wheel_urls)} instead")

    expected_python_files = find_files_in_directories(directories=[main_package_directory] + subpackage_directories, extensions=[FileExtension.PYTHON_EXTENSION], recursive=False, absolute_path=True)
    expected_python_files = paths_relative_to(paths=expected_python_files, relative_to=root_repository)

    expected_source_cpp_files = find_files_in_directories(directories=[root_repository], extensions=[FileExtension.CPP_EXTENSION, FileExtension.HEADER_EXTENSION], recursive=True, absolute_path=True)
    expected_source_cpp_files = paths_relative_to(paths=expected_source_cpp_files, relative_to=root_repository)

    source_url = source_urls[0]
    source_name = display_name(url=source_url, package_name=package_name, version=version)
    try:
        verify_source(source_url=source_url, package_name=package_name, version=version, expected_python_files=expected_python_files, expected_cpp_files=expected_source_cpp_files)
    except Exception as source_exception:
        nb_errors += 1
        log_error(name=source_name, exception=source_exception)
    else:
        log_valid(name=source_name)

    for wheel_url in wheel_urls:
        wheel_name = display_name(url=wheel_url, package_name=package_name, version=version)
        try:
            verify_wheel(wheel_url=wheel_url, package_name=package_name, version=version, expected_shared_libraries=expected_shared_libraries, expected_python_files=expected_python_files)
        except Exception as wheel_exception:
            nb_errors += 1
            log_error(name=wheel_name, exception=wheel_exception)
        else:
            log_valid(name=wheel_name)

    return nb_errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify the content of the uploaded package to PyPi or Test PyPi")
    parser.add_argument("index", type=str, choices=["pypi", "test.pypi"], help="Specify the package index on which to validate the package. Use 'pypi' for the main Python Package Index or 'test.pypi' for the testing instance")
    args = parser.parse_args()

    try:
        exit_status = main(index=args.index,
                           package_name=config.PACKAGE_NAME,
                           version=config.VERSION,
                           expected_nb_wheels=config.EXPECTED_NB_WHEELS,
                           expected_shared_libraries=config.EXPECTED_SHARED_LIBRARIES,
                           root_repository=config.ROOT_REPOSITORY,
                           main_package_directory=config.MAIN_PACKAGE_DIRECTORY,
                           subpackage_directories=config.SUBPACKAGES_DIRECTORIES)
        sys.exit(exit_status)
    except Exception as e:
        print(e)
        sys.exit(1)

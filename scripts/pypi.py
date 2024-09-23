from __future__ import annotations

import argparse
import io
import os
import pathlib
import re
import sys
import zipfile
from typing import List

import requests
import toml
from requests import Response

ROOT = pathlib.Path(__file__).parent.parent

PACKAGE_NAME = toml.load(ROOT.joinpath("pyproject.toml"))["project"]["name"]
VERSION = toml.load(ROOT.joinpath("pyproject.toml"))["project"]["version"]

ANY_VALID_STRING = r"[^'\"\s]+"

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


def verify_source(source_url: str, package_name: str, version: str) -> None:
    verify_source_url(source_url=source_url, package_name=package_name, version=version)


def verify_source_url(source_url: str, package_name: str, version: str) -> None:
    expected_source_name = f"{package_name}-{version}.{SOURCE_EXTENSION}"
    actual_source_name = source_url.split("/")[-1]
    if actual_source_name != expected_source_name:
        # TODO: improve message: quotes for but was + mention url
        raise Exception(f"expected source distribution url to contain '{expected_source_name}', but was '{actual_source_name}'")


def verify_wheel(wheel_url: str, package_name: str, version: str, expected_shared_libraries: List[str]) -> None:
    verify_wheel_url(wheel_url=wheel_url, package_name=package_name, version=version)
    expected_shared_lib_ext = expected_wheel_shared_libraries_extension(wheel_url=wheel_url)
    file_names = fetch_file_names_from_zip(url=wheel_url)
    verify_wheel_shared_libraries(file_names=file_names, expected_shared_libraries=[f"{expected_shared_lib}.{expected_shared_lib_ext}" for expected_shared_lib in expected_shared_libraries])


def display_name(url: str, package_name: str, version: str):
    name = re.findall(pattern=rf"{package_name}-{version}{ANY_VALID_STRING}", string=url)
    if len(name) == 1:
        return name[0]
    elif len(name) == 0:
        return url
    else:
        raise Exception("Verify url")


def verify_wheel_url(wheel_url: str, package_name: str, version: str) -> None:
    wheel_pattern = rf"{package_name}-{version}-{ANY_VALID_STRING}\.{WHEEL_EXTENSION}\b"
    match = re.search(pattern=wheel_pattern, string=wheel_url)
    if match is None:
        raise Exception(f"expected wheel url '{wheel_url}' to match the pattern '{wheel_pattern}'")


def expected_wheel_shared_libraries_extension(wheel_url: str) -> str:
    if LINUX in wheel_url:
        return SO_EXTENSION
    elif MACOS in wheel_url:
        return DYLIB_EXTENSION
    elif WINDOWS in wheel_url:
        return DLL_EXTENSION
    else:
        raise Exception(f"The wheel name does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")


def verify_wheel_shared_libraries(file_names: List[str], expected_shared_libraries: List[str]) -> None:
    all_shared_libraries = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[SO_EXTENSION, DLL_EXTENSION, DYLIB_EXTENSION])
    if sorted(all_shared_libraries) != sorted(expected_shared_libraries):
        raise Exception(f"expected wheel to contain shared librar{'ies' if len(expected_shared_libraries) > 1 else 'y'} {expected_shared_libraries}, but found {all_shared_libraries} instead")


# =================================================


def get_response(url: str) -> Response:
    response = requests.get(url=url)
    if not response.ok:
        raise Exception(f"Request for url {url} was unsuccessful")

    return response


def html_page_as_string(url: str) -> str:
    response = get_response(url=url)
    html_page = response.content.decode(encoding=response.encoding, errors="strict")
    return html_page


def fetch_file_names_from_zip(url: str) -> List[str]:
    response = get_response(url=url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        return zip_file.namelist()


def find_urls_in_html_page(html_page: str, target_url_extension: str) -> List[str]:
    urls = re.findall(pattern=rf"https:{ANY_VALID_STRING}\.{target_url_extension}\b", string=html_page)
    return urls


def find_file_names_with_given_extensions(file_names: List[str], potential_extensions: List[str]) -> List[str]:
    joined_extensions = "|".join(potential_extensions)
    matched_shared_libraries = []
    for file_name in file_names:
        if re.search(pattern=rf"{ANY_VALID_STRING}\.(?:{joined_extensions})$", string=file_name) is not None:
            matched_shared_libraries.append(file_name)
    return matched_shared_libraries


def main(index: str, package_name: str, version: str, expected_nb_wheels: int, expected_shared_libraries: List[str]) -> int:
    package_url = f"https://{index}.org/project/{package_name}/{version}/#files"
    print(f"Starting {os.path.basename(__file__)} script for index '{index}' (url: {package_url})\n")

    pypi_html_page = html_page_as_string(url=package_url)
    source_urls = find_urls_in_html_page(html_page=pypi_html_page, target_url_extension=SOURCE_EXTENSION)
    wheel_urls = find_urls_in_html_page(html_page=pypi_html_page, target_url_extension=WHEEL_EXTENSION)

    if len(source_urls) != 1:
        raise Exception(f"Expected 1 source url in the html page, but found {len(source_urls)} instead")

    if len(wheel_urls) != expected_nb_wheels:
        raise Exception(f"Expected {expected_nb_wheels} wheel url{'s' if expected_nb_wheels > 1 else ''} in the html page, but found {len(wheel_urls)} instead")

    exit_status = 0
    source_url = source_urls[0]
    source_name = display_name(url=source_url, package_name=package_name, version=version)
    try:
        verify_source(source_url=source_url, package_name=package_name, version=version)
    except Exception as source_exception:
        exit_status += 1
        print(f"{source_name}: {source_exception}")
    else:
        print(f"{source_name}: {PASSED}")

    for wheel_url in wheel_urls:
        wheel_name = display_name(url=wheel_url, package_name=package_name, version=version)
        try:
            verify_wheel(wheel_url=wheel_url, package_name=package_name, version=version, expected_shared_libraries=expected_shared_libraries)
        except Exception as wheel_exception:
            exit_status += 1
            print(f"{wheel_name}: {wheel_exception}")
        else:
            print(f"{wheel_name}: {PASSED}")

    return exit_status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify the content of uploaded package to PyPi or Test PyPi")
    parser.add_argument("index", type=str, choices=["pypi", "test.pypi"], help="Whether to use the PyPi or Test PyPi package index")
    args = parser.parse_args()

    try:
        sys.exit(main(index=args.index, package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=EXPECTED_NB_WHEELS, expected_shared_libraries=EXPECTED_SHARED_LIBRARIES))
    except Exception as e:
        print(e)
        sys.exit(1)

    # TODO: Log with logger or print?
    # TODO: common function for the main because same behavior for wheel and source with exception etc (function with args: function, etc (what takes verify_source() and verify_wheel()))
    # TODO: add verification for the source: check that there are python files? + cpp files?
    # TODO: add verification for the wheel: check that there are python files?
    # TODO: add doc?
    # TODO: in get_shared_library_file(), with cmake the shared lib name is libtradeflow.?, do no longer need to search for pattern. Directly search for the file with exact name?

# def find_cpp_files(directory: str) -> List[str]:
#     cpp_files = []
#     for root, _, files in os.walk(directory):
#         if root == directory:
#             for filename in fnmatch.filter(files, "*.cpp"):
#                 cpp_files.append(os.path.join(directory, filename))
#
#     return cpp_files

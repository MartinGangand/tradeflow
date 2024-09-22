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

SHARED_LIBRARY_NAME = "libtradeflow"

WHEEL_EXTENSION = "whl"
SOURCE_EXTENSION = "tar.gz"

LINUX = "linux"
MACOS = "macosx"
WINDOWS = "win"

SO_EXTENSION = "so"
DLL_EXTENSION = "dll"
DYLIB_EXTENSION = "dylib"

PASSED = "PASSED"

EXPECTED_NB_WHEELS = 55


def verify_source(source_url: str) -> None:
    validate_source_url_name(source_url=source_url)


def validate_source_url_name(source_url: str) -> None:
    package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
    if package_name_and_version not in source_url:
        raise Exception(f"expected package name and version ('{package_name_and_version}') to be in the source url: {source_url}")


def verify_wheel(wheel_url: str) -> None:
    validate_wheel_url(wheel_url=wheel_url)
    file_names = fetch_file_names_from_zip(url=wheel_url)
    validate_shared_library(wheel_url=wheel_url, file_names=file_names)


def display_name(url: str):
    name = re.findall(pattern=rf'{PACKAGE_NAME}-{VERSION}[^"\s]+', string=url)
    assert len(name) == 1
    return name[0]


def validate_wheel_url(wheel_url: str) -> None:
    package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
    if package_name_and_version not in wheel_url:
        raise Exception(f"expected package name and version ('{package_name_and_version}') to be in the wheel url: {wheel_url}")


def validate_shared_library(wheel_url: str, file_names: List[str]) -> None:
    matched_shared_libraries = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[SO_EXTENSION, DLL_EXTENSION, DYLIB_EXTENSION])

    if len(matched_shared_libraries) != 1:
        raise Exception(f"expected 1 shared library in the wheel, but found {len(matched_shared_libraries)} ({matched_shared_libraries if len(matched_shared_libraries) > 1 else ''})")

    shared_library_name = matched_shared_libraries[0]
    validate_shared_library_extension(wheel_url=wheel_url, shared_library_name=shared_library_name)


def validate_shared_library_extension(wheel_url: str, shared_library_name: str) -> None:
    expected_shared_library_extension = wheel_expected_shared_library_extension(wheel_url=wheel_url)

    is_valid = shared_library_name.endswith(f".{expected_shared_library_extension}")
    if not is_valid:
        raise Exception(f"expected shared library extension to be {expected_shared_library_extension}, but was {shared_library_name.split('.')[-1]}\n")


def wheel_expected_shared_library_extension(wheel_url: str) -> str:
    if LINUX in wheel_url:
        return SO_EXTENSION
    elif MACOS in wheel_url:
        return DYLIB_EXTENSION
    elif WINDOWS in wheel_url:
        return DLL_EXTENSION
    else:
        raise Exception(f"The wheel does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")

# =================================================


def get_request(url: str) -> Response:
    response = requests.get(url, stream=True)
    if not response.ok:
        raise Exception(f"Request for url {url} was unsuccessful")

    return response


def html_page_as_string(url: str) -> str:
    response = get_request(url=url)
    html_page = response.content.decode(encoding=response.encoding, errors="strict")
    return html_page


def fetch_file_names_from_zip(url: str) -> List[str]:
    response = get_request(url=url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        return zip_file.namelist()


def find_urls_in_html_page(html_page: str, target_url_extension: str) -> List[str]:
    urls = re.findall(pattern=rf'https:[^"\s]+\.{target_url_extension}', string=html_page)
    return urls


def find_file_names_with_given_extensions(file_names: List[str], potential_extensions: List[str]) -> List[str]:
    joined_extensions = "|".join(potential_extensions)
    matched_shared_libraries = []
    for file_name in file_names:
        if re.search(pattern=rf"[^'\"\s]+\.(?:{joined_extensions})$", string=file_name) is not None:
            matched_shared_libraries.append(file_name)
    return matched_shared_libraries


def main(index: str):
    package_url = f"https://{index}.org/project/{PACKAGE_NAME}/{VERSION}/#files"
    sys.stdout.write(f"Starting {os.path.basename(__file__)} script for index '{index}' (url: {package_url})\n\n")

    pypi_html_page = html_page_as_string(url=package_url)
    wheel_urls = find_urls_in_html_page(html_page=pypi_html_page, target_url_extension=WHEEL_EXTENSION)
    source_urls = find_urls_in_html_page(html_page=pypi_html_page, target_url_extension=SOURCE_EXTENSION)

    if len(wheel_urls) != EXPECTED_NB_WHEELS:
        raise Exception(f"Expected {EXPECTED_NB_WHEELS} wheel url{'s' if EXPECTED_NB_WHEELS > 1 else ''} in the html page, but found {len(wheel_urls)}")

    if len(source_urls) != 1:
        raise Exception(f"Expected 1 source url in the html page, but found {len(source_urls)}")

    exit_status = 0
    for wheel_url in wheel_urls:
        try:
            verify_wheel(wheel_url=wheel_url)
        except Exception as wheel_exception:
            exit_status += 1
            sys.stdout.write(f"{display_name(url=wheel_url)}: {wheel_exception}\n")
        else:
            sys.stdout.write(f"{display_name(url=wheel_url)}: {PASSED}\n")

    source_url = source_urls[0]
    try:
        verify_source(source_url=source_url)
    except Exception as source_exception:
        exit_status += 1
        sys.stdout.write(f"{display_name(url=source_url)}: {source_exception}\n")
    else:
        sys.stdout.write(f"{display_name(url=source_url)}: {PASSED}\n")

    return exit_status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify the content of uploaded package to PyPi or Test PyPi")
    parser.add_argument("index", type=str, choices=["pypi", "test.pypi"], help="Whether to use the PyPi or Test PyPi package index")
    args = parser.parse_args()

    try:
        sys.exit(main(index=args.index))
    except Exception as e:
        print(e)
        sys.exit(1)

    # TODO: Check the source?
    # TODO: Better log message (ex: print shared lib if several)
    # TODO: check extension name (ex: .so) given wheel name
    # TODO: Add a github action? or look at how pandas is doing
    # TODO: Add arguments for pypi and pypi test with ArgumentParser
    # TODO: Retrieve version/project name from toml?
    # TODO: Use urllib instead of requests? (maybe urllib is part of python directly?)
    # TODO: Log with logger or sys.std?
    # TODO: Should the argument parsing be in the main or in if __name__ == "__main__"

    # Remove validate_wheels() and validate_source() and instead create object directly?
    # Create a parent class with common methods like for error logging and return status...

# def find_cpp_files(directory: str) -> List[str]:
#     cpp_files = []
#     for root, _, files in os.walk(directory):
#         if root == directory:
#             for filename in fnmatch.filter(files, "*.cpp"):
#                 cpp_files.append(os.path.join(directory, filename))
#
#     return cpp_files

# run-python-script:
# name: Run Python Script After Completion
# needs: [upload-testpypi]  # Make this dependent on all other jobs
# runs-on: ubuntu-latest  # Or any other runner you'd like to use
#
# steps:
# - name: Checkout code
# uses: actions/checkout@v4
#
# - name: Set up Python
# uses: actions/setup-python@v5
# with:
#     python-version: '3.12'
#
# - name: Install dependencies
# run: |
# python -m pip install --upgrade pip
# pip install -r requirements.txt
# pip install -r test-requirements.txt
#
# - name: Run script
# run: python scripts/pypi-verify.py


    # # 1. Download wheel and retrieve file names
    # # 2. Find all shared libraries
    # # 3. Assure only 1 shared lib
    # # 4. Assure shared library has the good extension
    #
    # def _display_name(self, url: str) -> str:
    #     wheel_name = re.findall(pattern=rf'{PACKAGE_NAME}-{re.escape(VERSION)}[^"\s]+\.{WHEEL_EXTENSION}', string=url)
    #     assert len(wheel_name) == 1
    #     return wheel_name[0]

# class SourceChecker(Checker):
#
#     def _display_name(self, url: str) -> str:
#         source_name = re.findall(pattern=rf'{PACKAGE_NAME}-{VERSION}\.{SOURCE_EXTENSION}', string=url)
#         assert len(source_name) == 1
#         return source_name[0]
#

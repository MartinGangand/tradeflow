from __future__ import annotations
import sys
import os
for s in sys.path:
    print(s)
print(os.getcwd())
import argparse
import os
import pathlib
import re
import sys
from abc import ABC, abstractmethod
from typing import List

import toml

import utils

PACKAGE_NAME = toml.load(pathlib.Path(__file__).parent.parent.parent.joinpath("pyproject.toml"))["project"]["name"]
VERSION = toml.load(pathlib.Path(__file__).parent.parent.parent.joinpath("pyproject.toml"))["project"]["version"]
URL_PACKAGE = f"https://pypi.org/project/{PACKAGE_NAME}/{VERSION}/#files"
SHARED_LIBRARY_NAME = "libtradeflow"

WHEEL_EXTENSION = "whl"
SOURCE_EXTENSION = "tar.gz"

LINUX = "linux"
MACOS = "macosx"
WINDOWS = "win"

SO_EXTENSION = "so"
DLL_EXTENSION = "dll"
DYLIB_EXTENSION = "dylib"

EXPECTED_NB_WHEELS = 55


class Checker(ABC):

    def __init__(self, checker_name: str, html_page: str, target_url_extension: str, expected_nb_urls: int):
        self._checker_name = checker_name
        self._urls = self._find_urls_in_html_page(html_page=html_page, target_url_extension=target_url_extension, expected_nb_urls=expected_nb_urls)
        self._url_to_messages = {}
        self._exit_status = 0

    def check(self) -> Checker:
        self._process_urls()
        self._add_valid_messages_if_no_errors()
        return self

    def print_results(self) -> Checker:
        sys.stdout.write("\n=========================================\n")
        sys.stdout.write(f"||    Validation results for {self._checker_name}    ||\n")
        sys.stdout.write("=========================================\n")

        for url, messages in self._url_to_messages.items():
            sys.stdout.write(f"{self._display_name(url=url)}: {', '.join(messages)}\n")

        return self

    def exit_status(self) -> int:
        return self._exit_status

    def _find_urls_in_html_page(self, html_page: str, target_url_extension:str, expected_nb_urls: int) -> List[str]:
        urls = re.findall(pattern=rf'https:[^"\s]+\.{target_url_extension}', string=html_page)
        if len(urls) != expected_nb_urls:
            raise Exception(f"{self._checker_name.lower()} checker: expected {expected_nb_urls} url{'s' if expected_nb_urls > 1 else ''} in the html page, but found {len(urls)}")

        return urls

    def _add_error(self, url: str, error_message: str) -> None:
        self._exit_status += 1
        if url not in self._url_to_messages:
            self._url_to_messages[url] = []

        self._url_to_messages[url].append(error_message)

    def _add_valid_messages_if_no_errors(self) -> None:
        for url in self._urls:
            if url not in self._url_to_messages:
                self._url_to_messages[url] = ["PASSED"]

    @abstractmethod
    def _process_urls(self) -> Checker:
        pass

    @abstractmethod
    def _display_name(self, url: str) -> str:
        pass


class WheelsChecker(Checker):

    # 1. Download wheel and retrieve file names
    # 2. Find all shared libraries
    # 3. Assure only 1 shared lib
    # 4. Assure shared library has the good extension
    def __init__(self, html_page: str):
        super().__init__(checker_name="wheels", html_page=html_page, target_url_extension=WHEEL_EXTENSION, expected_nb_urls=EXPECTED_NB_WHEELS)

    def _process_urls(self) -> WheelsChecker:
        for wheel_url in self._urls:
            self._validate_wheel_url(wheel_url=wheel_url)
            file_names = utils.fetch_file_names_from_zip(url=wheel_url)
            self._validate_shared_library(wheel_url=wheel_url, file_names=file_names)

        return self

    def _display_name(self, url: str) -> str:
        wheel_name = re.findall(pattern=rf'{PACKAGE_NAME}-{re.escape(VERSION)}[^"\s]+\.{WHEEL_EXTENSION}', string=url)
        assert len(wheel_name) == 1
        return wheel_name[0]

    def _validate_wheel_url(self, wheel_url: str) -> None:
        package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
        if package_name_and_version not in wheel_url:
            error_message = f"expected package name and version ('{package_name_and_version}') to be in the wheel url: {wheel_url}"
            self._add_error(url=wheel_url, error_message=error_message)

    def _validate_shared_library(self, wheel_url: str, file_names: List[str]) -> None:
        matched_shared_libraries = utils.find_file_names_with_given_extensions(file_names=file_names, potential_extensions=[SO_EXTENSION, DLL_EXTENSION, DYLIB_EXTENSION])

        if len(matched_shared_libraries) != 1:
            error_message = f"expected 1 shared library in the wheel, but found {len(matched_shared_libraries)} ({matched_shared_libraries if len(matched_shared_libraries) > 1 else ''})"
            self._add_error(url=wheel_url, error_message=error_message)
            return

        shared_library_name = matched_shared_libraries[0]
        self._validate_shared_library_extension(wheel_url=wheel_url, shared_library_name=shared_library_name)

    def _validate_shared_library_extension(self, wheel_url: str, shared_library_name: str) -> None:
        expected_shared_library_extension = self._get_wheel_expected_shared_library_extension(wheel_url=wheel_url)

        is_valid = shared_library_name.endswith(f".{expected_shared_library_extension}")
        if not is_valid:
            self._add_error(url=wheel_url,
                            error_message=f"expected shared library extension to be {expected_shared_library_extension}, but was {shared_library_name.split('.')[-1]}\n")

    def _get_wheel_expected_shared_library_extension(self, wheel_url: str) -> str:
        if LINUX in wheel_url:
            return SO_EXTENSION
        elif MACOS in wheel_url:
            return DYLIB_EXTENSION
        elif WINDOWS in wheel_url:
            return DLL_EXTENSION
        else:
            raise Exception(f"The wheel does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")


class SourceChecker(Checker):

    def __init__(self, html_page: str):
        super().__init__(checker_name="source", html_page=html_page, target_url_extension=SOURCE_EXTENSION, expected_nb_urls=1)

    def _process_urls(self) -> SourceChecker:
        source_url = self._urls[0]
        self._validate_source_url_name(source_url=source_url)

        return self

    def _display_name(self, url: str) -> str:
        source_name = re.findall(pattern=rf'{PACKAGE_NAME}-{VERSION}\.{SOURCE_EXTENSION}', string=url)
        assert len(source_name) == 1
        return source_name[0]

    def _validate_source_url_name(self, source_url: str):
        package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
        if package_name_and_version not in source_url:
            error_message = f"expected package name and version ('{package_name_and_version}') to be in the source url: {source_url}"
            self._add_error(url=source_url, error_message=error_message)


def main(index: str):
    package_url = f"https://{index}.org/project/{PACKAGE_NAME}/{VERSION}/#files"
    sys.stdout.write(f"Starting {os.path.basename(__file__)} script for index '{index}' (url: {package_url})")
    pypi_html_page = utils.html_page_as_string(url=package_url)

    wheels_checker = WheelsChecker(html_page=pypi_html_page).check().print_results()
    source_checker = SourceChecker(html_page=pypi_html_page).check().print_results()

    return wheels_checker.exit_status() + source_checker.exit_status()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify the content of uploaded package to PyPi or Test PyPi")
    parser.add_argument("index", type=str, choices=["pypi", "test.pypi"],
                        help="Whether to use the PyPi or Test PyPi package index")
    args = parser.parse_args()

    exit_status = main(index=args.index)
    # if exit_status > 0:
    #     raise Exception(f"EXIT STATUS: {exit_status}")
    sys.exit(exit_status)

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

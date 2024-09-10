from __future__ import annotations

import io
import re
import sys
import zipfile
from abc import ABC, abstractmethod
from typing import List

import requests

PACKAGE_NAME = "tradeflow"
VERSION = "0.0.13"
URL_PYPI_PAGE = f"https://pypi.org/project/{PACKAGE_NAME}/{VERSION}/#files"
SHARED_LIBRARY_NAME = "libtradeflow"

LINUX = "linux"
MACOS = "macosx"
WINDOWS = "win"

SO_EXTENSION = "so"
DLL_EXTENSION = "dll"
DYLIB_EXTENSION = "dylib"
PYD_EXTENSION = "pyd"
WHEEL_EXTENSION = "whl"
SOURCE_EXTENSION = "tar.gz"

ERRORS_KEY = "errors"
VALID_KEY = "valid"

EXPECTED_NB_WHEELS = 55


def get_pypi_html_page():
    response = requests.get(URL_PYPI_PAGE)
    html_page = response.content.decode(encoding=response.encoding, errors="strict")
    return html_page


class Checker(ABC):

    def __init__(self, name: str, html_page: str):
        self._name = name
        self._urls = self._find_urls_in_html_page(html_page=html_page)
        self._results = {
            ERRORS_KEY: [],
            VALID_KEY: []
        }

    @abstractmethod
    def validate(self) -> Checker:
        pass

    def print_results(self) -> Checker:
        sys.stdout.write("\n=========================================\n")
        sys.stdout.write(f"||    Validation results for {self._name}    ||\n")
        sys.stdout.write("=========================================\n")

        for error_message in self._results["valid"]:
            sys.stdout.write(f"{error_message}\n")

        for error_message in self._results["errors"]:
            sys.stderr.write(f"{error_message}\n")

        return self

    def exit_status(self) -> int:
        nb_errors = len(self._results[ERRORS_KEY])
        nb_valid = len(self._results[VALID_KEY])
        assert nb_errors + nb_valid > 0 and not (nb_errors > 0 and nb_valid > 0)
        return nb_errors

    def _is_nb_urls_valid(self, expected_nb_urls: int) -> bool:
        nb_urls = len(self._urls)
        if nb_urls != expected_nb_urls:
            self._results[ERRORS_KEY].append(f"Failing error for {self._name.lower()} checker: expected {expected_nb_urls} url{'s' if expected_nb_urls > 1 else ''} in the html page, but found {nb_urls}")
            return False

        return True

    def _find_urls_in_html_page(self, html_page: str) -> List[str]:
        return re.findall(pattern=rf'https:[^"\s]+\.{self._url_extension()}', string=html_page)

    def _add_error(self, url: str, error_message: str) -> None:
        self._results[ERRORS_KEY].append(f"{self._display_name(url=url)}: {error_message}")

    def _add_valid_message_if_no_errors(self, url: str) -> None:
        self._results[VALID_KEY].append(f"{self._display_name(url=url)}: PASSED")

    @abstractmethod
    def _url_extension(self) -> str:
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
        super().__init__(name="wheels", html_page=html_page)

    def validate(self) -> WheelsChecker:
        if not self._is_nb_urls_valid(expected_nb_urls=EXPECTED_NB_WHEELS):
            return self

        for wheel_url in self._urls:
            self._validate_wheel_url(wheel_url=wheel_url)
            file_names = self._fetch_file_names_from_zip(wheel_url=wheel_url)
            self._validate_shared_library(wheel_url=wheel_url, file_names=file_names)

            self._add_valid_message_if_no_errors(url=wheel_url)
        
        return self

    def _url_extension(self) -> str:
        return WHEEL_EXTENSION

    def _display_name(self, url: str) -> str:
        wheel_name = re.findall(pattern=rf'{PACKAGE_NAME}-{re.escape(VERSION)}[^"\s]+\.{WHEEL_EXTENSION}', string=url)
        assert len(wheel_name) == 1
        return wheel_name[0]

    def _validate_wheel_url(self, wheel_url: str) -> None:
        package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
        if package_name_and_version not in wheel_url:
            self._add_error(url=wheel_url, error_message=f"expected package name and version ('{package_name_and_version}') to be in the wheel url: {wheel_url}")

    def _fetch_file_names_from_zip(self, wheel_url: str) -> List[str]:
        response = requests.get(wheel_url, stream=True)
        if not response.ok:
            self._add_error(url=wheel_url, error_message=f"unable to download the wheel with link: {wheel_url}")

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            return zip_file.namelist()

    def _validate_shared_library(self, wheel_url: str, file_names: List[str]) -> None:
        matched_shared_libraries = self._find_all_shared_libraries(file_names=file_names)

        nb_shared_libraries = len(matched_shared_libraries)
        if nb_shared_libraries != 1:
            self._add_error(url=wheel_url, error_message=f"expected 1 shared library in the wheel, but found {nb_shared_libraries} {matched_shared_libraries if nb_shared_libraries > 1 else ''}")
            return

        shared_library_name = matched_shared_libraries[0]
        self._validate_shared_library_extension(wheel_url=wheel_url, shared_library_name=shared_library_name)

    def _find_all_shared_libraries(self, file_names: List[str]) -> List[str]:
        matched_shared_libraries = re.findall(pattern=rf'{PACKAGE_NAME}/{SHARED_LIBRARY_NAME}\.[^"\s]+?\.(?:{SO_EXTENSION}|{DLL_EXTENSION}|{DYLIB_EXTENSION}|{PYD_EXTENSION})', string=", ".join(file_names))
        return matched_shared_libraries

    def _validate_shared_library_extension(self, wheel_url: str, shared_library_name: str) -> None:
        os_to_shared_library_extension = {
            LINUX: SO_EXTENSION,
            MACOS: SO_EXTENSION,
            WINDOWS: PYD_EXTENSION
        }
        wheel_target_os = self._get_wheel_target_os(wheel_url=wheel_url)
        expected_shared_library_extension = os_to_shared_library_extension[wheel_target_os]

        is_valid = shared_library_name.endswith(f".{expected_shared_library_extension}")
        if not is_valid:
            self._add_error(url=wheel_url, error_message=f"expected shared library extension to be {expected_shared_library_extension}, but was {shared_library_name.split('.')[-1]}\n")

    def _get_wheel_target_os(self, wheel_url: str) -> str:
        if LINUX in wheel_url:
            return LINUX
        elif MACOS in wheel_url:
            return MACOS
        elif WINDOWS in wheel_url:
            return WINDOWS
        else:
            raise Exception(f"The wheel does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")


class SourceChecker(Checker):

    def __init__(self, html_page: str):
        super().__init__(name="source", html_page=html_page)

    def validate(self) -> SourceChecker:
        if not self._is_nb_urls_valid(expected_nb_urls=1):
            return self

        source_url = self._urls[0]
        self._validate_source_url_name(source_url=source_url)
        self._add_valid_message_if_no_errors(url=source_url)
        
        return self

    def _url_extension(self) -> str:
        return SOURCE_EXTENSION

    def _display_name(self, url: str) -> str:
        source_name = re.findall(pattern=rf'{PACKAGE_NAME}-{VERSION}\.{SOURCE_EXTENSION}', string=url)
        assert len(source_name) == 1
        return source_name[0]

    def _validate_source_url_name(self, source_url: str):
        package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
        if package_name_and_version not in source_url:
            self._add_error(url=source_url, error_message=f"expected package name and version ('{package_name_and_version}') to be in the source url: {source_url}")


def main():
    pypi_html_page = get_pypi_html_page()

    wheels_checker = WheelsChecker(html_page=pypi_html_page).validate().print_results()
    source_checker = SourceChecker(html_page=pypi_html_page).validate().print_results()

    return wheels_checker.exit_status() + source_checker.exit_status()


if __name__ == "__main__":
    exit_status = main()
    if exit_status > 0:
        raise Exception(f"EXIT STATUS: {exit_status}")
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

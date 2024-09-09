import io
import re
import sys
import tarfile
import zipfile
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

EXPECTED_NB_WHEELS = 55


def get_pypi_html_page():
    response = requests.get(URL_PYPI_PAGE)
    html_page = response.content.decode(encoding=response.encoding, errors="strict")
    return html_page


def find_urls_in_html_page(html_page: str, extension: str) -> List[str]:
    return re.findall(pattern=rf'https:[^"\s]+\.{extension}', string=html_page)


class WheelChecker:

    # 1. Download wheel and retrieve file names
    # 2. Find all shared libraries
    # 3. Assure only 1 shared lib
    # 4. Assure shared library has the good extension
    def __init__(self, wheel_url: str):
        self._wheel_url = wheel_url

        self._error_message = ""
        self._exit_status = 0

    @property
    def exit_status(self):
        self._validate_wheel()

        assert self._exit_status == 0 and not self._error_message or self._exit_status > 0 and self._error_message
        wheel_name = self._get_wheel_name()
        if self._error_message:
            sys.stderr.write(f"{wheel_name}: FAILED {self._error_message}\n")
        else:
            sys.stdout.write(f"{wheel_name}: PASSED\n")

        return self._exit_status

    def _validate_wheel(self) -> None:
        self._validate_wheel_url()
        file_names = self._fetch_file_names_from_zip()
        self._validate_shared_library(file_names=file_names)

    def _validate_wheel_url(self):
        package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
        if package_name_and_version not in self._wheel_url:
            self._log_error(message=f"expected package name and version ('{package_name_and_version}') to be in the wheel url: {self._wheel_url}")
            self._exit_status += 1

    def _fetch_file_names_from_zip(self) -> List[str]:
        response = requests.get(self._wheel_url, stream=True)
        if not response.ok:
            self._log_error(f"unable to download the wheel with link: {self._wheel_url}")

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            return zip_file.namelist()

    def _validate_shared_library(self, file_names: List[str]) -> None:
        matched_shared_libraries = self._find_all_shared_libraries(file_names=file_names)

        nb_shared_libraries = len(matched_shared_libraries)
        if nb_shared_libraries != 1:
            self._log_error(message=f"expected 1 shared library in the wheel, but found {nb_shared_libraries} {matched_shared_libraries if nb_shared_libraries > 1 else ''}")
            self._exit_status += 1
            return

        shared_library_name = matched_shared_libraries[0]
        if not self._validate_shared_library_extension(shared_library_name=shared_library_name):
            self._exit_status += 1

    def _find_all_shared_libraries(self, file_names: List[str]) -> List[str]:
        matched_shared_libraries = re.findall(pattern=rf'{PACKAGE_NAME}/{SHARED_LIBRARY_NAME}\.[^"\s]+?\.(?:{SO_EXTENSION}|{DLL_EXTENSION}|{DYLIB_EXTENSION}|{PYD_EXTENSION})', string=", ".join(file_names))
        return matched_shared_libraries

    def _validate_shared_library_extension(self, shared_library_name: str) -> bool:
        os_to_shared_library_extension = {
            LINUX: SO_EXTENSION,
            MACOS: SO_EXTENSION,
            WINDOWS: PYD_EXTENSION
        }
        wheel_target_os = self._get_wheel_target_os()
        expected_shared_library_extension = os_to_shared_library_extension[wheel_target_os]
        is_valid = shared_library_name.endswith(f".{expected_shared_library_extension}")
        if not is_valid:
            self._log_error(message=f"expected shared library extension to be {expected_shared_library_extension}, but was {shared_library_name.split('.')[-1]}\n")

        return is_valid

    def _get_wheel_target_os(self) -> str:
        if LINUX in self._wheel_url:
            return LINUX
        elif MACOS in self._wheel_url:
            return MACOS
        elif WINDOWS in self._wheel_url:
            return WINDOWS
        else:
            raise Exception(f"The wheel does not contain '{LINUX}', '{MACOS}' nor '{WINDOWS}'")

    def _get_wheel_name(self):
        wheel_name = re.findall(pattern=rf'{PACKAGE_NAME}-{re.escape(VERSION)}[^"\s]+\.{WHEEL_EXTENSION}', string=self._wheel_url)
        assert len(wheel_name) == 1
        return wheel_name[0]

    def _log_error(self, message: str) -> None:
        self._error_message += f"{message}"


def validate_wheels(html_page: str) -> int:
    sys.stdout.write("\n=======================================\n")
    sys.stdout.write("||    Starting to validate wheels    ||\n")
    sys.stdout.write("=======================================\n")

    exit_status = 0
    wheel_urls = find_urls_in_html_page(html_page=html_page, extension=WHEEL_EXTENSION)
    if len(wheel_urls) != EXPECTED_NB_WHEELS:
        sys.stdout.write(f"Expected {EXPECTED_NB_WHEELS} available wheels, but found {len(wheel_urls)}\n")
        exit_status += 1

    for wheel_url in wheel_urls:
        exit_status += WheelChecker(wheel_url=wheel_url).exit_status

    return exit_status


class SourceChecker:

    def __init__(self, source_url: str):
        self._source_url = source_url

        self._error_message = ""
        self._exit_status = 0

    @property
    def exit_status(self):
        self._validate_source()

        assert self._exit_status == 0 and not self._error_message or self._exit_status > 0 and self._error_message
        source_name = self._get_source_name()
        if self._error_message:
            sys.stderr.write(f"{source_name}: FAILED {self._error_message}\n")
        else:
            sys.stdout.write(f"{source_name}: PASSED\n")
        return self._exit_status

    def _validate_source(self):
        self._validate_source_url()

    def _validate_source_url(self):
        package_name_and_version = f"{PACKAGE_NAME}-{VERSION}"
        if package_name_and_version not in self._source_url:
            self._log_error(message=f"expected package name and version ('{package_name_and_version}') to be in the source url: {self._source_url}")
            self._exit_status += 1

    def _get_source_name(self):
        source_name = re.findall(pattern=rf'{PACKAGE_NAME}-{VERSION}\.{SOURCE_EXTENSION}', string=self._source_url)
        assert len(source_name) == 1
        return source_name[0]

    def _log_error(self, message: str) -> None:
        self._error_message += f"{message}"


def validate_source(html_page: str) -> int:
    sys.stdout.write("\n=======================================\n")
    sys.stdout.write("||    Starting to validate source    ||\n")
    sys.stdout.write("=======================================\n")

    exit_status = 0
    source_urls = find_urls_in_html_page(html_page=html_page, extension=SOURCE_EXTENSION)
    if len(source_urls) != 1:
        sys.stdout.write(f"Expected 1 source distribution, but found {len(source_urls)}\n")
        exit_status += 1

    return SourceChecker(source_url=source_urls[0]).exit_status


def main():
    pypi_html_page = get_pypi_html_page()
    return validate_wheels(html_page=pypi_html_page) + validate_source(html_page=pypi_html_page)


if __name__ == "__main__":
    exit_status = main()
    if exit_status > 0:
        raise Exception(f"EXIT STATUS: {exit_status}")
    sys.exit(exit_status)

    # TODO: Check the source?
    # TODO: Better log message (ex: print shared lib if several)
    # TODO: check extension name (ex: .so) given wheel name
    # TODO: Add a github action? or look at how pandas is doing
    # TODO: Add arguments for pypi and pypi test with ArgParser
    # TODO: Retrieve version/project name from toml?
    # TODO: Use urllib instead of requests? (maybe urllib is part of python directly?)
    # TODO: Log with logger or sys.std?

    # Remove validate_wheels() and validate_source() and instead create object directly?
    # Create a parent class with common methods like for error logging and return status...


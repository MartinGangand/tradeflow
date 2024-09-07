import io
import re
import sys
import zipfile
from typing import List

import requests

VERSION = "0.0.13"
PYPI_URL = f"https://pypi.org/project/tradeflow/{VERSION}/#files"
SHARED_LIBRARY_NAME = "libtradeflow"


def get_wheel_urls() -> List[str]:
    response = requests.get(PYPI_URL)
    html_page = response.content.decode(encoding=response.encoding)
    links = re.findall(pattern=r'https:[^"\s]+\.whl', string=html_page)  # r'https:[^"\s]+\.(?:whl|tar\.gz)'
    return links


def fetch_file_names_from_zip(url: str) -> List[str]:
    response = requests.get(url, stream=True)
    assert response.ok

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        return zip_file.namelist()


def wheel_contain_shared_library(wheel_url: str):
    file_names = fetch_file_names_from_zip(url=wheel_url)
    matched_shared_library = re.findall(pattern=rf'tradeflow/{SHARED_LIBRARY_NAME }\.[^"\s]+?\.(?:so|dll|dylib|pyd)', string=", ".join(file_names))
    sys.stdout.write(f"{get_wheel_name(wheel_url=wheel_url)} => {'OK' if len(matched_shared_library) == 1 else 'ERROR'}\n")
    return len(matched_shared_library) == 1


def get_wheel_name(wheel_url: str):
    wheel_name = re.findall(pattern=r'tradeflow-[^"\s]+\.whl', string=wheel_url)
    assert len(wheel_name) == 1
    return wheel_name[0]


def main():
    valid_wheels = 0
    wheel_urls = get_wheel_urls()
    for wheel_url in wheel_urls:
        valid_wheels += 1 if wheel_contain_shared_library(wheel_url=wheel_url) else 0

    print(f"Valid wheels containing 1 shared library: {valid_wheels}/{len(wheel_urls)}")
    return 0 if valid_wheels == len(wheel_urls) else 1


if __name__ == "__main__":
    sys.exit(main())

    # TODO: Check the source?
    # TODO: Better log message (ex: print shared lib if several)
    # TODO: check extension name (ex: .so) given wheel name
    # TODO: Add a github action?

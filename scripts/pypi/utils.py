import io
import zipfile
from typing import List

import requests
from requests import Response
import re


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


def find_file_names_with_given_extensions(file_names: List[str], potential_extensions: List[str]) -> List[str]:
    joined_extensions = "|".join(potential_extensions)
    matched_shared_libraries = re.findall(pattern=rf'[^"\s]+\.(?:{joined_extensions})', string=", ".join(file_names))
    return matched_shared_libraries

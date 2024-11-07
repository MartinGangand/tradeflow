import io
import os
import re
import tarfile
import zipfile
from pathlib import Path
from typing import List

import requests
from requests import Response

ANY_VALID_STRING = r"[^'\"\s]+"


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
    response = get_response(url=url)
    html_page_content = response.content.decode(encoding=response.encoding, errors="strict")
    return html_page_content


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
    return urls


def find_files_in_directory(directory: Path, extensions: List[str], recursive: bool, absolute_path: bool) -> List[str]:
    """
    Find files within a specified directory that match given file extensions.

    Parameters
    ----------
    directory : Path
        The root directory to search for files.
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
    files = []
    glob_function = directory.rglob if recursive else directory.glob
    for file_path in glob_function(pattern="*"):
        if not (file_path.is_file() and file_path.suffix in extensions):
            continue

        if not absolute_path:
            file_path = file_path.relative_to(directory)

        files.append(str(file_path))

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


def paths_relative_to(paths: List[str], relative_to: Path):
    return [Path(path).relative_to(relative_to) for path in paths]

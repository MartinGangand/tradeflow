import io
import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Any, List
from unittest.mock import MagicMock

import pytest
from numpy.testing import assert_equal
from pytest_mock import MockerFixture

from scripts.utils import get_response, html_page_as_string, fetch_file_names_from_zip, \
    fetch_file_names_from_tar_gz, find_urls_in_html_page, find_file_names_with_given_extensions, \
    find_files_in_directory, file_names_with_prefixes

DATASETS_DIRECTORY = Path(__file__).parent.parent.joinpath("datasets").resolve()
UTF_8 = "utf-8"


def mock_response(mocker: MockerFixture, content: Any, ok: bool) -> MagicMock:
    mocked_response = mocker.Mock()

    mocked_response.content = content
    mocked_response.encoding = UTF_8
    mocked_response.ok = ok

    return mocked_response


def mock_response_with_html_page(mocker: MockerFixture, html_page_content: str) -> MagicMock:
    response_content = html_page_content.encode(encoding=UTF_8, errors="strict")
    return mock_response(mocker=mocker, content=response_content, ok=True)


def mock_response_with_source(mocker: MockerFixture, file_names: List[str]) -> MagicMock:
    response_content = create_source(file_names=file_names)
    return mock_response(mocker=mocker, content=response_content, ok=True)


def mock_response_with_wheel(mocker: MockerFixture, file_names: List[str]) -> MagicMock:
    response_content = create_wheel(file_names=file_names)
    return mock_response(mocker=mocker, content=response_content, ok=True)


def create_source(file_names: List[str]) -> bytes:
    source_buffer = io.BytesIO()

    with tarfile.open(fileobj=source_buffer, mode="w:gz") as tar:
        for file_name in file_names:
            file = tarfile.TarInfo(name=file_name)
            file.size = 0
            tar.addfile(tarinfo=file)

    source_buffer.seek(0)
    return source_buffer.getvalue()


def create_wheel(file_names: List[str]) -> bytes:
    wheel_buffer = io.BytesIO()

    with zipfile.ZipFile(file=wheel_buffer, mode="w") as zip_file:
        for file_name in file_names:
            zip_file.writestr(file_name, "")

    wheel_buffer.seek(0)
    return wheel_buffer.getvalue()


def read_html_page_from_datasets(file_name: str) -> str:
    html_page_path = DATASETS_DIRECTORY.joinpath(file_name)
    with open(html_page_path, "r", encoding=UTF_8) as html_page:
        return html_page.read()


def prepare_directory_with_files(directory_path: Path, file_names: List[str]) -> None:
    directory_path.mkdir(parents=True, exist_ok=False)
    for file_name in file_names:
        directory_path.joinpath(file_name).open(mode="w").close()


class TestGetResponse:

    url = "https://dummy/url.whl"

    def test_get_response(self, mocker):
        expected_response_content = "response content"

        mock_request_get = mock_response(mocker=mocker, content=expected_response_content, ok=True)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        response = get_response(url=self.url)
        assert response.ok is True
        assert response.content == expected_response_content
        request_get.assert_called_once_with(url=self.url)

    def test_get_response_should_raise_exception_when_unsuccessful_request(self, mocker):
        mock_request_get = mock_response(mocker=mocker, content="response content", ok=False)
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            get_response(url=self.url)

        assert str(ex.value) == f"Request for url {self.url} was unsuccessful"


class TestHtmlPageAsString:

    def test_html_page_as_string(self, mocker):
        expected_html_page_content = "Content of the html page"

        mock_request_get = mock_response_with_html_page(mocker=mocker, html_page_content=expected_html_page_content)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        html_page_url = f"https://pypi.org/#files"
        actual_html_page_content = html_page_as_string(url=html_page_url)

        request_get.assert_called_once_with(url=html_page_url)
        assert actual_html_page_content == expected_html_page_content


class TestFetchFileNamesFromTarGz:

    def test_fetch_file_names_from_tar_gz(self, mocker):
        expected_tar_gz_file_names = ["tradeflow/ar_model.py", "tradeflow/simulation.cpp", "tradeflow/simulation.h"]

        mock_request_get = mock_response_with_source(mocker=mocker, file_names=expected_tar_gz_file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        tar_gz_url = "https://url.tar.gz"
        actual_tar_gz_file_names = fetch_file_names_from_tar_gz(url=tar_gz_url)

        request_get.assert_called_once_with(url=tar_gz_url)
        assert_equal(actual=actual_tar_gz_file_names, desired=expected_tar_gz_file_names)


class TestFetchFileNamesFromZip:

    def test_fetch_file_names_from_zip(self, mocker):
        expected_zip_file_names = ["tradeflow/ar_model.py", "tradeflow/libtradeflow.dll"]

        mock_request_get = mock_response_with_wheel(mocker=mocker, file_names=expected_zip_file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        zip_url = "https://url.whl"
        actual_zip_file_names = fetch_file_names_from_zip(url=zip_url)

        request_get.assert_called_once_with(url=zip_url)
        assert_equal(actual=actual_zip_file_names, desired=expected_zip_file_names)


class TestFindUrlsInHtmlPage:

    @pytest.mark.parametrize("target_url_extension,expected_urls", [
        ("tar.gz", [f"https://test-files.pythonhosted.org/packages/package-0.0.1.tar.gz"]),
        ("whl", [
            f"https://test-files.pythonhosted.org/packages/package-0.0.1-cp312-cp312-win_amd64.whl",
            f"https://test-files.pythonhosted.org/packages/package-0.0.1-cp312-cp312-musllinux_1_2_x86_64.whl",
            f"https://test-files.pythonhosted.org/packages/package-0.0.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            f"https://test-files.pythonhosted.org/packages/package-0.0.1-cp312-cp312-macosx_11_0_arm64.whl"
        ]),
        (".whl", []),
        ("whll", []),
        (".so", [])
    ])
    def test_find_urls_in_html_page(self, target_url_extension, expected_urls):
        html_page = read_html_page_from_datasets(file_name="html_page_test_find_urls_in_html_page.html")

        actual_urls = find_urls_in_html_page(html_page_content=html_page, target_url_extension=target_url_extension)
        assert_equal(actual=actual_urls, desired=expected_urls)


class TestFindFilesInDirectory:

    TEMP_DIR = Path(__file__).parent.joinpath("temp")

    FOLDER_A = TEMP_DIR.joinpath("folder_a")
    FOLDER_B = FOLDER_A.joinpath("folder_b")

    @pytest.fixture(scope="function", autouse=True)
    def find_files_in_directory_setup_and_tear_down(self):
        self.TEMP_DIR.mkdir(parents=False, exist_ok=False)

        prepare_directory_with_files(directory_path=self.FOLDER_A, file_names=["file_a1.py", "file_a2.py", "file_a3.cpp", "file_a4.h"])
        prepare_directory_with_files(directory_path=self.FOLDER_B, file_names=["file_b1.py", "file_b2.cpp", "file_b3.h"])

        yield

        shutil.rmtree(path=self.TEMP_DIR)

    @pytest.mark.parametrize("directory,extensions,absolute_path,expected_files", [
        (TEMP_DIR, ["py"], True, []),
        (TEMP_DIR, ["py"], False, []),
        (TEMP_DIR, ["py", "cpp"], False, []),
        (FOLDER_A, ["py"], True, [str(FOLDER_A.joinpath("file_a1.py")), str(FOLDER_A.joinpath("file_a2.py"))]),
        (FOLDER_A, ["py"], False, ["file_a1.py", "file_a2.py"]),
        (FOLDER_A, ["py", "cpp"], False, ["file_a1.py", "file_a2.py", "file_a3.cpp"])
    ])
    def test_find_files_in_directory_when_recursive_is_false(self, directory, extensions, absolute_path, expected_files):
        actual_files = find_files_in_directory(directory=directory, extensions=extensions, recursive=False, absolute_path=absolute_path)
        assert_equal(actual=sorted(actual_files), desired=sorted(expected_files))

    @pytest.mark.parametrize("directory,extensions,absolute_path,expected_files", [
        (TEMP_DIR, ["py"], True, [str(FOLDER_A.joinpath("file_a1.py")), str(FOLDER_A.joinpath("file_a2.py")), str(FOLDER_B.joinpath("file_b1.py"))]),
        (TEMP_DIR, ["py"], False, ["folder_a/file_a1.py", "folder_a/file_a2.py", "folder_a/folder_b/file_b1.py"]),
        (TEMP_DIR, ["py", "cpp"], False, ["folder_a/file_a1.py", "folder_a/file_a2.py", "folder_a/file_a3.cpp", "folder_a/folder_b/file_b1.py", "folder_a/folder_b/file_b2.cpp"]),
        (FOLDER_A, ["py"], True, [str(FOLDER_A.joinpath("file_a1.py")), str(FOLDER_A.joinpath("file_a2.py")), str(FOLDER_B.joinpath("file_b1.py"))]),
        (FOLDER_A, ["py"], False, ["file_a1.py", "file_a2.py", "folder_b/file_b1.py"]),
        (FOLDER_B, ["py"], True, [str(FOLDER_B.joinpath("file_b1.py"))]),
        (FOLDER_B, ["py"], False, ["file_b1.py"]),
        (FOLDER_B, ["py", "h"], True, [str(FOLDER_B.joinpath("file_b1.py")), str(FOLDER_B.joinpath("file_b3.h"))]),
    ])
    def test_find_files_in_directory_when_recursive_is_true(self, directory, extensions, absolute_path, expected_files):
        actual_files = find_files_in_directory(directory=directory, extensions=extensions, recursive=True, absolute_path=absolute_path)
        assert_equal(actual=sorted(actual_files), desired=sorted(expected_files))


class TestFindFileNamesWithGivenExtensions:

    @pytest.mark.parametrize("file_names,potential_extensions,expected_file_names", [
        (["libtradeflow1.so", "tradeflow/libtradeflow2.so", "logger_utils.py"], ["so"], ["libtradeflow1.so", "tradeflow/libtradeflow2.so"]),
        (["libtradeflow.so", "tradeflow/libtradeflow.dll", "logger_utils.py"], ["so", "dll"], ["libtradeflow.so", "tradeflow/libtradeflow.dll"]),
        (["libtradeflow.s", "libtradeflowso", "tradeflow/libtradeflow.dlll", "logger_utils.py", ".so"], ["so", "dll"], [])
    ])
    def test_find_file_names_with_given_extensions(self, file_names, potential_extensions, expected_file_names):
        actual_file_names = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=potential_extensions)
        assert_equal(actual=actual_file_names, desired=expected_file_names)


class TestFileNamesWithPrefixes:

    @pytest.mark.parametrize("actual_files,prefixes,expected_files_with_prefixes", [
        ([], [], []),
        ([], ["p1"], []),
        (["f1.py"], [], ["f1.py"]),
        (["f1.py"], [""], ["f1.py"]),
        (["f1.py"], ["p1"], [os.path.join("p1", "f1.py")]),
        (["f1.py"], ["p1", "p2"], [os.path.join("p1", "p2", "f1.py")]),
        (["f1.py", "f2.py"], [], ["f1.py", "f2.py"]),
        (["f1.py", "f2.py"], ["p1"], [os.path.join("p1", "f1.py"), os.path.join("p1", "f2.py")]),
        (["f1.py", "f2.py"], ["p1", "p2"], [os.path.join("p1", "p2", "f1.py"), os.path.join("p1", "p2", "f2.py")]),
    ])
    def test_file_names_with_prefixes(self, actual_files, prefixes, expected_files_with_prefixes):
        actual_files_with_prefixes = file_names_with_prefixes(actual_files, *prefixes)
        assert_equal(actual=actual_files_with_prefixes, desired=expected_files_with_prefixes)

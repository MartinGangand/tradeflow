import io
import pathlib
import zipfile
from typing import List
from unittest.mock import MagicMock

import pytest
from numpy.testing import assert_equal
from pytest_mock import MockerFixture

from scripts.pypi import find_urls_in_html_page, find_file_names_with_given_extensions, verify_source_url, \
    verify_wheel_url, fetch_file_names_from_zip, html_page_as_string, expected_wheel_shared_libraries_extension, \
    verify_wheel_shared_libraries, verify_source, verify_wheel
from scripts.pypi import main

DATASETS_DIRECTORY = pathlib.Path(__file__).parent.parent.joinpath("datasets").resolve()

UTF_8 = "utf-8"
PACKAGE_NAME = "package"
VERSION = "0.0.1"

WHEEL_CP312_WIN = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-win_amd64.whl"
WHEEL_CP312_MUSLLINUX = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-musllinux_1_2_x86_64.whl"
WHEEL_CP312_MANYLINUX = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
WHEEL_CP312_MACOSX = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-macosx_11_0_arm64.whl"
WHEEL_URL_START = "https://test-files.pythonhosted.org/packages"


def create_wheel(file_names: List[str]) -> bytes:
    wheel_buffer = io.BytesIO()

    with zipfile.ZipFile(wheel_buffer, "a") as zip_file:
        for file_name in file_names:
            zip_file.writestr(file_name, "")

    wheel_buffer.seek(0)
    return wheel_buffer.getvalue()


def read_html_page(file_name: str) -> str:
    html_page_path = DATASETS_DIRECTORY.joinpath(f"{file_name}.html")
    with open(html_page_path, "r", encoding=UTF_8) as html_page:
        return html_page.read()


def mock_response(mocker: MockerFixture, content: bytes, ok: [bool] = None) -> MagicMock:
    mocked_response = mocker.Mock()

    mocked_response.content = content
    mocked_response.encoding = UTF_8
    if ok is not None:
        mocked_response.ok = ok

    return mocked_response


def mock_html_page(mocker: MockerFixture, html_page: str) -> MagicMock:
    response_content = html_page.encode(encoding=UTF_8, errors="strict")
    return mock_response(mocker=mocker, content=response_content, ok=True)


def mock_wheel_requests_get(mocker: MockerFixture, file_names: List[str]) -> MagicMock:
    response_content = create_wheel(file_names)
    return mock_response(mocker=mocker, content=response_content, ok=True)


class TestFindUrlsInHtmlPage:

    @pytest.mark.parametrize("target_url_extension,expected_urls", [
        ("tar.gz", [f"{WHEEL_URL_START}/56/67/532132463e1969baf3ff2bc4fec5489a951185663322709ddb2f66c3f284/package-0.0.1.tar.gz"]),
        ("whl", [
            f"{WHEEL_URL_START}/51/84/58302957f418ff8995b4b1ad9b6931e32de990edd86fe687b3e41af0a8d4/{WHEEL_CP312_WIN}",
            f"{WHEEL_URL_START}/8a/44/2afc38353c0fbaf3b501f3624aac3b66495e5c816880a1d07baa2df5b407/{WHEEL_CP312_MUSLLINUX}",
            f"{WHEEL_URL_START}/e1/6d/24c7c2ba73fa79dfa12534c9d34fb2b180a90e63271868f9ff47215d0b2c/{WHEEL_CP312_MANYLINUX}",
            f"{WHEEL_URL_START}/03/31/338e4767aaf3e291ab7b9304d911a00f7bf73e5db38167188450b6a2b104/{WHEEL_CP312_MACOSX}"
        ]),
        (".whl", []),
        (".so", [])
    ])
    def test_find_urls_in_html_page(self, target_url_extension, expected_urls):
        html_page = read_html_page(file_name="html_page_sample")

        actual_urls = find_urls_in_html_page(html_page=html_page, target_url_extension=target_url_extension)
        assert_equal(actual=actual_urls, desired=expected_urls)


class TestFindFileNamesWithGivenExtensions:

    @pytest.mark.parametrize("file_names,potential_extensions,expected_file_names", [
        (["libtradeflow1.so", "tradeflow/libtradeflow2.so", "logger_utils.py"], ["so"], ["libtradeflow1.so", "tradeflow/libtradeflow2.so"]),
        (["libtradeflow.so", "tradeflow/libtradeflow.dll", "logger_utils.py"], ["so", "dll"], ["libtradeflow.so", "tradeflow/libtradeflow.dll"]),
        (["libtradeflow.s", "libtradeflowso", "tradeflow/libtradeflow.dlll", "logger_utils.py", ".so"], ["so", "dll"], [])
    ])
    def test_find_file_names_with_given_extensions(self, file_names, potential_extensions, expected_file_names):
        actual_file_names = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=potential_extensions)
        assert_equal(actual=actual_file_names, desired=expected_file_names)


class TestVerifySourceUrl:

    def test_verify_source_name_should_not_raise_exception(self):
        source_url = f"{WHEEL_URL_START}/{PACKAGE_NAME}-{VERSION}.tar.gz"
        assert verify_source_url(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION) is None

    @pytest.mark.parametrize("source_name", [
        "package-0.0.1.tar.g",
        "package-0.0.1.tar.gzz",
        "package-0.0.1.whl",
        "package-0.0.1.1.tar.gz",
        "package-0.0.11.tar.gz",
        "package2-0.0.1.tar.gz"
        "package-0.0.1",
        "0.0.1.tar.gz",
        "package-0.0.1",
    ])
    def test_verify_source_name_should_raise_exception(self, source_name):
        source_url = f"{WHEEL_URL_START}/{source_name}"
        with pytest.raises(Exception) as ex:
            verify_source_url(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION)

        assert str(ex.value) == f"expected source distribution url to contain '{PACKAGE_NAME}-{VERSION}.tar.gz', but was '{source_name}'"


class TestVerifyWheelUrl:

    @pytest.mark.parametrize("wheel_name", [
        "package-0.0.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "package-0.0.1-cp312-cp312-musllinux_1_2_x86_64.whl",
        "package-0.0.1-cp312-cp312-macosx_11_0_arm64.whl"
        "package-0.0.1-cp312-cp312-win_amd64.whl",
        "package-0.0.1-any.whl"
    ])
    def test_verify_wheel_name_should_not_raise_exception(self, wheel_name):
        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"
        assert verify_wheel_url(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION) is None

    @pytest.mark.parametrize("wheel_name", [
        "package-0.0.1-any.wh",
        "package-0.0.1-any.whll",
        "package-0.0.1.1-any.whl",
        "package-0.0.11-any.whl",
        "package-0.0.1.whl",
        "package-0.0.1any.whl",
        "0.0.1-any.whl",
        "package-0.0.1-any"
    ])
    def test_verify_wheel_name_should_raise_exception(self, wheel_name):
        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"
        with pytest.raises(Exception) as ex:
            verify_wheel_url(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION)

        assert str(ex.value) == rf"expected wheel url '{wheel_url}' to match the pattern 'package-0.0.1-[^'\"\s]+\.whl\b'"


class TestFetchFileNamesFromZip:

    def test_fetch_file_names_from_zip(self, mocker):
        expected_file_names = ["tradeflow/ar_model.py", "tradeflow/libtradeflow.dll"]

        mock_request_get = mock_wheel_requests_get(mocker=mocker, file_names=expected_file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        actual_file_names = fetch_file_names_from_zip(url="https://dummy/url.whl")

        request_get.assert_called_once_with(url="https://dummy/url.whl")
        assert_equal(actual=actual_file_names, desired=expected_file_names)


class TestHtmlPageAsString:

    def test_html_page_as_string(self, mocker):
        expected_html_page_as_string = "Content of the html page"

        mock_request_get = mock_html_page(mocker=mocker, html_page=expected_html_page_as_string)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        actual_html_page_as_string = html_page_as_string(url=f"https://pypi.org/#files")

        request_get.assert_called_once_with(url=f"https://pypi.org/#files")
        assert_equal(actual=actual_html_page_as_string, desired=expected_html_page_as_string)


class TestExpectedWheelSharedLibrariesExtension:

    @pytest.mark.parametrize("wheel_url,expected_shared_libraries_extension", [
        (f"{WHEEL_URL_START}/{WHEEL_CP312_MANYLINUX}", "so"),
        (f"{WHEEL_URL_START}/{WHEEL_CP312_MUSLLINUX}", "so"),
        (f"{WHEEL_URL_START}/{WHEEL_CP312_MACOSX}", "dylib"),
        (f"{WHEEL_URL_START}/{WHEEL_CP312_WIN}", "dll")
    ])
    def test_expected_wheel_shared_libraries_extension_should_not_raise_exception(self, wheel_url, expected_shared_libraries_extension):
        assert expected_wheel_shared_libraries_extension(wheel_url=wheel_url) == expected_shared_libraries_extension

    @pytest.mark.parametrize("wheel_url", [
        f"{WHEEL_URL_START}/package-0.0.1-cp312-cp312-manylinu_2_17_x86_64.manylinu2014_x86_64.whl",
        f"{WHEEL_URL_START}/package-0.0.1-cp312-cp312-inux_1_2_x86_64.whl",
        f"{WHEEL_URL_START}/package-0.0.1-cp312-cp312-macos_11_0_arm64.whl",
        f"{WHEEL_URL_START}/package-0.0.1-cp312-cp312-wi_amd64.whl"
    ])
    def test_expected_wheel_shared_libraries_extension_should_raise_exception(self, wheel_url):
        with pytest.raises(Exception) as ex:
            expected_wheel_shared_libraries_extension(wheel_url=wheel_url)

        assert str(ex.value) == f"The wheel name does not contain 'linux', 'macosx' nor 'win'"


class TestVerifyWheelSharedLibraries:

    @pytest.mark.parametrize("file_names,expected_shared_libraries", [
        (["package/__init__.py", "package/ar_model.py", "package/lib1.dll", "package-0.0.1.dist-info/LICENSE"], ["package/lib1.dll"]),
        (["__init__.py, ar_model.py", "lib1.so", "package-0.0.1.dist-info/LICENSE"], ["lib1.so"]),
        (["__init__.py, ar_model.py", "lib3.dylib", "lib2.dylib", "lib1.dylib", "package-0.0.1.dist-info/LICENSE"], ["lib3.dylib", "lib2.dylib", "lib1.dylib"]),
        (["__init__.py", "ar_model.py", "lib1.dl", "lib2.dlll", "lib3.dylibb", "lib4.s"], [])
    ])
    def test_verify_wheel_shared_libraries_should_not_raise_exception(self, file_names, expected_shared_libraries):
        assert verify_wheel_shared_libraries(file_names=file_names, expected_shared_libraries=expected_shared_libraries) is None

    @pytest.mark.parametrize("file_names,expected_shared_libraries,expected_matched_shared_libraries", [
        (["package/ar_model.py", "package/lib1.dll", "package-0.0.1.dist-info/LICENSE"], [], ["package/lib1.dll"]),
        (["ar_model.py", "lib1.so", "lib2.so"], ["lib1.so"], ["lib1.so", "lib2.so"]),
        (["ar_model.py"], ["lib1.dylib", "lib2.dylib"], [])
    ])
    def test_verify_wheel_shared_libraries_should_raise_exception(self, file_names, expected_shared_libraries, expected_matched_shared_libraries):
        with pytest.raises(Exception) as ex:
            verify_wheel_shared_libraries(file_names=file_names, expected_shared_libraries=expected_shared_libraries)

        assert str(ex.value) == f"expected wheel to contain shared librar{'ies' if len(expected_shared_libraries) > 1 else 'y'} {expected_shared_libraries}, but found {expected_matched_shared_libraries} instead"


# TODO: add additional test when add new logic in verify_source()
class TestVerifySource:

    def test_verify_source_should_not_raise_exception(self):
        source_url = f"{WHEEL_URL_START}/{PACKAGE_NAME}-{VERSION}.tar.gz"
        assert verify_source(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION) is None

    @pytest.mark.parametrize("source_name,expected_error_message", [
        ("package-0.0.2.tar.gz", f"expected source distribution url to contain 'package-0.0.1.tar.gz', but was 'package-0.0.2.tar.gz'")
    ])
    def test_verify_source_should_raise_exception(self, source_name, expected_error_message):
        source_url = f"{WHEEL_URL_START}/{source_name}"
        with pytest.raises(Exception) as ex:
            verify_source(source_url=source_url, package_name="package", version="0.0.1")

        assert str(ex.value) == expected_error_message


class TestVerifyWheel:

    @pytest.mark.parametrize("wheel_name,file_names,expected_shared_libraries", [
        (WHEEL_CP312_MANYLINUX, ["package/ar_model.py", "package/lib1.so"], ["package/lib1"]),
        (WHEEL_CP312_MUSLLINUX, ["ar_model.py", "lib1.so", "lib2.so"], ["lib1", "lib2"]),
        (WHEEL_CP312_MACOSX, ["ar_model.py"], []),
        (WHEEL_CP312_WIN, ["ar_model.py", "lib1.dll"], ["lib1"])
    ])
    def test_verify_wheel_should_not_raise_exception(self, mocker, wheel_name, file_names, expected_shared_libraries):
        mock_request_get = mock_wheel_requests_get(mocker=mocker, file_names=file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"
        assert verify_wheel(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION, expected_shared_libraries=expected_shared_libraries) is None
        request_get.assert_called_once_with(url=wheel_url)

    @pytest.mark.parametrize("wheel_name,file_names,expected_shared_libraries,expected_error_message", [
        ("package-0.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", ["ar_model.py", "lib1.so"], ["lib1"], rf"expected wheel url 'https://test-files.pythonhosted.org/packages/package-0.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl' to match the pattern 'package-0.0.1-[^'\"\s]+\.whl\b'"),
        (WHEEL_CP312_MUSLLINUX, ["ar_model.py", "lib1.so", "lib2.so"], ["lib1"], "expected wheel to contain shared library ['lib1.so'], but found ['lib1.so', 'lib2.so'] instead"),
        (WHEEL_CP312_MACOSX, ["ar_model.py", "lib1.dylib"], ["lib1", "lib2"], "expected wheel to contain shared libraries ['lib1.dylib', 'lib2.dylib'], but found ['lib1.dylib'] instead"),
        (WHEEL_CP312_WIN, ["ar_model.py", "lib1.so"], ["lib1"], "expected wheel to contain shared library ['lib1.dll'], but found ['lib1.so'] instead")
    ])
    def test_verify_wheel_should_raise_exception(self, mocker, wheel_name, file_names, expected_shared_libraries, expected_error_message):
        mock_request_get = mock_wheel_requests_get(mocker=mocker, file_names=file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"
        with pytest.raises(Exception) as ex:
            verify_wheel(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION, expected_shared_libraries=expected_shared_libraries)
            request_get.assert_called_once_with(url=wheel_url)

        assert str(ex.value) == expected_error_message


class TestMain:

    @staticmethod
    def mock_request_get_valid(mocker: MockerFixture, url: str) -> MagicMock:
        if url == f"https://test.pypi.org/project/{PACKAGE_NAME}/{VERSION}/#files":
            return mock_html_page(mocker=mocker, html_page=read_html_page(file_name="html_page_test_main_valid"))
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_WIN}":
            return mock_wheel_requests_get(mocker=mocker, file_names=["ar_model.py", "lib1.dll"])
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MUSLLINUX}":
            return mock_wheel_requests_get(mocker=mocker, file_names=["ar_model.py", "lib1.so"])
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MANYLINUX}":
            return mock_wheel_requests_get(mocker=mocker, file_names=["ar_model.py", "lib1.so"])
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MACOSX}":
            return mock_wheel_requests_get(mocker=mocker, file_names=["ar_model.py", "lib1.dylib"])

    @staticmethod
    def mock_request_get_invalid(mocker: MockerFixture, url: str) -> MagicMock:
        if url == f"https://test.pypi.org/project/{PACKAGE_NAME}/{VERSION}/#files":
            return mock_html_page(mocker=mocker, html_page=read_html_page(file_name="html_page_test_main_invalid"))
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MANYLINUX}":
            return mock_wheel_requests_get(mocker=mocker, file_names=["ar_model.py", "lib1.so", "lib2.so", "lib3.soo"])
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MACOSX}":
            return mock_wheel_requests_get(mocker=mocker, file_names=["ar_model.py"])

    def test_main_valid(self, mocker, capsys, file_regression):
        mocker.patch("requests.get", side_effect=lambda url: self.mock_request_get_valid(mocker=mocker, url=url))

        exit_status = main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=["lib1"])

        assert exit_status == 0
        file_regression.check(capsys.readouterr().out)

    def test_main_should_raise_exception_when_2_sources_instead_of_1(self, mocker, capsys):
        mock_request_get = mock_html_page(mocker=mocker, html_page=read_html_page(file_name="html_page_test_main_2_sources"))
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            exit_status = main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=["lib1"])

            assert exit_status == 1
            assert str(ex.value) == "Expected 1 source url in the html page, but found 2"

    def test_main_should_raise_exception_when_3_wheels_instead_of_4(self, mocker, capsys):
        mock_request_get = mock_html_page(mocker=mocker, html_page=read_html_page(file_name="html_page_test_main_3_wheels"))
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            exit_status = main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=["lib1"])

            assert exit_status == 1
            assert str(ex.value) == "Expected 4 wheel urls in the html page, but found 3"

    def test_main_invalid(self, mocker, capsys, file_regression):
        mocker.patch("requests.get", side_effect=lambda url: self.mock_request_get_invalid(mocker=mocker, url=url))

        exit_status = main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=["lib1"])

        assert exit_status == 5
        file_regression.check(capsys.readouterr().out)

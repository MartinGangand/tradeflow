import os.path
import os.path
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from scripts.pypi_verify import verify_source_url, \
    verify_wheel_url, expected_wheel_shared_libraries_extension, \
    verify_source, verify_wheel, verify_files, display_name, main
from scripts.utils import file_names_with_prefixes
from scripts.tests.test_utils import mock_response_with_source, mock_response_with_wheel, \
    prepare_directory_with_files, mock_response_with_html_page, read_html_page_from_datasets

TEMP_DIR = Path(__file__).parent.joinpath("temp")

PACKAGE_NAME = "package"
VERSION = "0.0.1"

HTML_PAGE_PYPI_URL_START = "https://test.pypi.org/project"
SOURCE_URL_START = "https://test-files.pythonhosted.org"
WHEEL_URL_START = "https://test-files.pythonhosted.org/packages"

WHEEL_CP312_WIN = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-win_amd64.whl"
WHEEL_CP312_MUSLLINUX = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-musllinux_1_2_x86_64.whl"
WHEEL_CP312_MANYLINUX = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
WHEEL_CP312_MACOSX = f"{PACKAGE_NAME}-{VERSION}-cp312-cp312-macosx_11_0_arm64.whl"


@pytest.fixture(scope="class", autouse=True)
def class_setup_and_tear_down():
    # Create the temporary directory before running tests
    TEMP_DIR.mkdir(parents=False, exist_ok=True)

    yield

    # Delete the temporary directory after running tests
    shutil.rmtree(path=TEMP_DIR)


class TestVerifyFiles:

    @pytest.mark.parametrize("expected_files,actual_files", [
        ([], []),
        (["ar_model.py"], ["ar_model.py"]),
        (["time_series.py", "ar_model.py"], ["ar_model.py", "time_series.py"]),
        (["time_series.py", "ar_model.py", "LICENSE"], ["LICENSE", "time_series.py", "ar_model.py",])
    ])
    def test_verify_files_should_not_raise_exception(self, expected_files, actual_files):
        assert verify_files(expected_files=expected_files, actual_files=actual_files, object_name="obj", file_type="python") is None

    @pytest.mark.parametrize("expected_files,actual_files", [
        (["ar_model.py"], []),
        (["ar_model.py"], ["time_series.py"]),
        (["ar_model.py"], ["time_series.py", "ar_model.py"]),
        (["time_series.py", "ar_model.py"], ["time_series.py"]),
        (["time_series.py", "ar_model.py"], ["time_series.py", "ar_model.py", "setup.py"])
    ])
    def test_verify_files_should_raise_exception(self, expected_files, actual_files):
        with pytest.raises(Exception) as ex:
            verify_files(expected_files=expected_files, actual_files=actual_files, object_name="obj", file_type="python")

        expected_error_message = f"expected obj to contain {len(expected_files)} python file(s) ({expected_files}), but found {len(actual_files)} ({actual_files}) instead"
        assert str(ex.value) == expected_error_message


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


# TODO: add additional test when add new logic in verify_source()
class TestVerifySource:

    @pytest.mark.parametrize("file_names,expected_python_files,expected_cpp_files", [
        (["time_series.py", "ar_model.py"], ["time_series.py", "ar_model.py"], []),
        (["time_series.py", "simulation.cpp"], ["time_series.py"], ["simulation.cpp"]),
        (["package-0.0.1/package/time_series.py", "package-0.0.1/package/ar_model.py", "package-0.0.1/lib/cpp/package/simulation.cpp", "package-0.0.1/lib/cpp/package/simulation.h"],
         ["package-0.0.1/package/time_series.py", "package-0.0.1/package/ar_model.py"],
         ["package-0.0.1/lib/cpp/package/simulation.cpp", "package-0.0.1/lib/cpp/package/simulation.h"])
    ])
    def test_verify_source_should_not_raise_exception(self, mocker, file_names, expected_python_files, expected_cpp_files):
        package_and_version = f"{PACKAGE_NAME}-{VERSION}"
        source_url = f"{SOURCE_URL_START}/{package_and_version}.tar.gz"

        file_names_with_setup = file_names + [os.path.join(package_and_version, "setup.py")]
        mock_request_get = mock_response_with_source(mocker=mocker, file_names=file_names_with_setup)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        assert verify_source(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION, expected_python_files=expected_python_files, expected_cpp_files=expected_cpp_files) is None
        request_get.assert_called_once_with(url=source_url)

    @pytest.mark.parametrize("source_name,expected_error_message", [
        ("package-0.0.1.source.tar.gz", "expected source distribution url to contain 'package-0.0.1.tar.gz', but was 'package-0.0.1.source.tar.gz'"),
        ("package-0.0.2.tar.gz", "expected source distribution url to contain 'package-0.0.1.tar.gz', but was 'package-0.0.2.tar.gz'")
    ])
    def test_verify_source_should_raise_exception_when_invalid_url(self, mocker, source_name, expected_error_message):
        source_url = f"{SOURCE_URL_START}/{source_name}"

        mock_request_get = mock_response_with_source(mocker=mocker, file_names=["ar_model.py", "simulation.cpp", os.path.join(f"{PACKAGE_NAME}-{VERSION}", "setup.py")])
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            verify_source(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION, expected_python_files=["ar_model.py"], expected_cpp_files=["simulation.cpp"])

        assert str(ex.value) == expected_error_message

    @pytest.mark.parametrize("source_name,file_names,expected_python_files,expected_cpp_files,expected_error_message", [
        ("package-0.0.1.tar.gz", ["ar_model.py"], [], [], "expected source to contain 0 python file(s) ([]), but found 1 (['ar_model.py']) instead"),
        ("package-0.0.1.tar.gz", [], ["ar_model.py"], [], "expected source to contain 1 python file(s) (['ar_model.py']), but found 0 ([]) instead"),
        ("package-0.0.1.tar.gz", [], ["time_series.py", "ar_model.py"], [], "expected source to contain 2 python file(s) (['time_series.py', 'ar_model.py']), but found 0 ([]) instead"),
        ("package-0.0.1.tar.gz", ["time_series.py"], ["time_series.py", "ar_model.py"], [], "expected source to contain 2 python file(s) (['time_series.py', 'ar_model.py']), but found 1 (['time_series.py']) instead"),
        ("package-0.0.1.tar.gz", ["time_series.py", "simulation.cpp", "simulation.h"], ["time_series.py", "ar_model.py"], ["simulation.cpp", "simulation.h"], "expected source to contain 2 python file(s) (['time_series.py', 'ar_model.py']), but found 1 (['time_series.py']) instead"),
        ("package-0.0.1.tar.gz", ["time_series.py", "ar_model.py", "model.py"], ["time_series.py", "ar_model.py"], [], "expected source to contain 2 python file(s) (['time_series.py', 'ar_model.py']), but found 3 (['time_series.py', 'ar_model.py', 'model.py']) instead"),
        ("package-0.0.1.tar.gz", ["package-0.0.1/package/time_series.py", "package-0.0.1/lib/cpp/package/simulation.cpp", "package-0.0.1/lib/cpp/package/simulation.h"],
         ["package-0.0.1/package/time_series.py", "package-0.0.1/package/ar_model.py"],
         ["package-0.0.1/lib/cpp/package/simulation.cpp", "package-0.0.1/lib/cpp/package/simulation.h"],
         "expected source to contain 2 python file(s) (['package-0.0.1/package/time_series.py', 'package-0.0.1/package/ar_model.py']), but found 1 (['package-0.0.1/package/time_series.py']) instead"),
    ])
    def test_verify_source_should_raise_exception_when_incorrect_python_files(self, mocker, source_name, file_names, expected_python_files, expected_cpp_files, expected_error_message):
        source_url = f"{SOURCE_URL_START}/{source_name}"

        file_names_with_setup = file_names + [os.path.join(f"{PACKAGE_NAME}-{VERSION}", "setup.py")]
        mock_request_get = mock_response_with_source(mocker=mocker, file_names=file_names_with_setup)
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            verify_source(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION, expected_python_files=expected_python_files, expected_cpp_files=expected_cpp_files)

        assert str(ex.value) == expected_error_message

    @pytest.mark.parametrize("source_name,file_names,expected_python_files,expected_cpp_files,expected_error_message", [
        ("package-0.0.1.tar.gz", ["simulation.cpp"], [], [], "expected source to contain 0 cpp or header file(s) ([]), but found 1 (['simulation.cpp']) instead"),
        ("package-0.0.1.tar.gz", [], [], ["simulation.cpp"], "expected source to contain 1 cpp or header file(s) (['simulation.cpp']), but found 0 ([]) instead"),
        ("package-0.0.1.tar.gz", [], [], ["simulation.cpp", "simulation.h"], "expected source to contain 2 cpp or header file(s) (['simulation.cpp', 'simulation.h']), but found 0 ([]) instead"),
        ("package-0.0.1.tar.gz", ["simulation.cpp"], [], ["simulation.cpp", "simulation.h"], "expected source to contain 2 cpp or header file(s) (['simulation.cpp', 'simulation.h']), but found 1 (['simulation.cpp']) instead"),
        ("package-0.0.1.tar.gz", ["time_series.py", "simulation.cpp"], ["time_series.py"], ["simulation.cpp", "simulation.h"], "expected source to contain 2 cpp or header file(s) (['simulation.cpp', 'simulation.h']), but found 1 (['simulation.cpp']) instead"),
        ("package-0.0.1.tar.gz", ["time_series.py", "simulation.cpp", "simulation.h", "simulation2.cpp"], ["time_series.py"], ["simulation.cpp", "simulation.h"], "expected source to contain 2 cpp or header file(s) (['simulation.cpp', 'simulation.h']), but found 3 (['simulation.cpp', 'simulation.h', 'simulation2.cpp']) instead"),
        ("package-0.0.1.tar.gz", ["package-0.0.1/package/time_series.py", "package-0.0.1/package/ar_model.py", "package-0.0.1/lib/cpp/package/simulation.cpp"],
         ["package-0.0.1/package/time_series.py", "package-0.0.1/package/ar_model.py"],
         ["package-0.0.1/lib/cpp/package/simulation.cpp", "package-0.0.1/lib/cpp/package/simulation.h"],
         "expected source to contain 2 cpp or header file(s) (['package-0.0.1/lib/cpp/package/simulation.cpp', 'package-0.0.1/lib/cpp/package/simulation.h']), but found 1 (['package-0.0.1/lib/cpp/package/simulation.cpp']) instead"),
    ])
    def test_verify_source_should_raise_exception_when_incorrect_cpp_files(self, mocker, source_name, file_names, expected_python_files, expected_cpp_files, expected_error_message):
        source_url = f"{SOURCE_URL_START}/{source_name}"

        file_names_with_setup = file_names + [os.path.join(f"{PACKAGE_NAME}-{VERSION}", "setup.py")]
        mock_request_get = mock_response_with_source(mocker=mocker, file_names=file_names_with_setup)
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            verify_source(source_url=source_url, package_name=PACKAGE_NAME, version=VERSION, expected_python_files=expected_python_files, expected_cpp_files=expected_cpp_files)

        assert str(ex.value) == expected_error_message


class TestVerifyWheel:

    @pytest.mark.parametrize("wheel_name,file_names,expected_shared_libraries,expected_python_files", [
        (WHEEL_CP312_MANYLINUX, ["package/ar_model.py", "package/lib1.so"], ["package/lib1"], ["package/ar_model.py"]),
        (WHEEL_CP312_MUSLLINUX, ["time_series.py", "ar_model.py", "lib1.so", "lib2.so"], ["lib1", "lib2"], ["ar_model.py", "time_series.py"]),
        (WHEEL_CP312_MACOSX, ["ar_model.py"], [], ["ar_model.py"]),
        (WHEEL_CP312_WIN, ["ar_model.py", "lib1.dll"], ["lib1"], ["ar_model.py"])
    ])
    def test_verify_wheel_should_not_raise_exception(self, mocker, wheel_name, file_names, expected_shared_libraries, expected_python_files):
        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"

        mock_request_get = mock_response_with_wheel(mocker=mocker, file_names=file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        assert verify_wheel(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION, expected_shared_libraries=expected_shared_libraries, expected_python_files=expected_python_files) is None
        request_get.assert_called_once_with(url=wheel_url)

    def test_verify_wheel_should_raise_exception_when_invalid_url(self):
        wheel_url = f"{WHEEL_URL_START}/package-0.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
        with pytest.raises(Exception) as ex:
            verify_wheel(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION, expected_shared_libraries=["lib1"], expected_python_files=["ar_model.py"])

        expected_error_message = rf"expected wheel url 'https://test-files.pythonhosted.org/packages/package-0.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl' to match the pattern 'package-0.0.1-[^'\"\s]+\.whl\b'"
        assert str(ex.value) == expected_error_message

    @pytest.mark.parametrize("wheel_name,file_names,expected_shared_libraries,expected_python_files,expected_error_message", [
        (WHEEL_CP312_MUSLLINUX, ["ar_model.py", "lib1.so", "lib2.so"], ["lib1"], ["ar_model.py"], "expected wheel to contain 1 shared library file(s) (['lib1.so']), but found 2 (['lib1.so', 'lib2.so']) instead"),
        (WHEEL_CP312_MACOSX, ["ar_model.py", "lib1.dylib"], ["lib1", "lib2"], ["ar_model.py"], "expected wheel to contain 2 shared library file(s) (['lib1.dylib', 'lib2.dylib']), but found 1 (['lib1.dylib']) instead"),
        (WHEEL_CP312_WIN, ["ar_model.py", "lib1.so"], ["lib1"], ["ar_model.py"], "expected wheel to contain 1 shared library file(s) (['lib1.dll']), but found 1 (['lib1.so']) instead")
    ])
    def test_verify_wheel_should_raise_exception_when_incorrect_python_files(self, mocker, wheel_name, file_names, expected_shared_libraries, expected_python_files, expected_error_message):
        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"

        mock_request_get = mock_response_with_wheel(mocker=mocker, file_names=file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            verify_wheel(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION, expected_shared_libraries=expected_shared_libraries, expected_python_files=expected_python_files)

        assert str(ex.value) == expected_error_message
        request_get.assert_called_once_with(url=wheel_url)

    @pytest.mark.parametrize("wheel_name,file_names,expected_shared_libraries,expected_python_files,expected_error_message", [
        (WHEEL_CP312_MANYLINUX, ["lib1.so"], ["lib1"], ["time_series.py", "ar_model.py"], "expected wheel to contain 2 python file(s) (['time_series.py', 'ar_model.py']), but found 0 ([]) instead"),
        (WHEEL_CP312_MACOSX, ["ar_model.py", "lib1.dylib"], ["lib1"], ["time_series.py", "ar_model.py"], "expected wheel to contain 2 python file(s) (['time_series.py', 'ar_model.py']), but found 1 (['ar_model.py']) instead"),
        (WHEEL_CP312_WIN, ["time_series.py", "ar_model.py", "lib1.dll"], ["lib1"], ["time_series.py"], "expected wheel to contain 1 python file(s) (['time_series.py']), but found 2 (['time_series.py', 'ar_model.py']) instead")
    ])
    def test_verify_wheel_should_raise_exception_when_incorrect_shared_libraries(self, mocker, wheel_name, file_names, expected_shared_libraries, expected_python_files, expected_error_message):
        wheel_url = f"{WHEEL_URL_START}/{wheel_name}"

        mock_request_get = mock_response_with_wheel(mocker=mocker, file_names=file_names)
        request_get = mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            verify_wheel(wheel_url=wheel_url, package_name=PACKAGE_NAME, version=VERSION, expected_shared_libraries=expected_shared_libraries, expected_python_files=expected_python_files)

        assert str(ex.value) == expected_error_message
        request_get.assert_called_once_with(url=wheel_url)


class TestDisplayName:

    @pytest.mark.parametrize("url,expected_display_name", [
        ("https://test-files/package-0.0.1-cp312-cp312-win_amd64.whl", "package-0.0.1-cp312-cp312-win_amd64.whl"),
        ("https://test-files/package-0.0.1.tar.gz", "package-0.0.1.tar.gz"),
        ("https://test-files/package-0.0.1", "https://test-files/package-0.0.1"),
        ("https://test-files/invalid_name.whl", "https://test-files/invalid_name.whl")
    ])
    def test_display_name(self, url, expected_display_name):
        actual_display_name = display_name(url=url, package_name=PACKAGE_NAME, version=VERSION)
        assert actual_display_name == expected_display_name


class TestMain:

    REPOSITORY_ROOT = TEMP_DIR.joinpath("Users", "dev", PACKAGE_NAME)

    PACKAGE_DIR = REPOSITORY_ROOT.joinpath(PACKAGE_NAME)
    PACKAGE_CPP_DIR = REPOSITORY_ROOT.joinpath("lib", "cpp", PACKAGE_NAME)

    EXPECTED_SHARED_LIBRARIES = [os.path.join(PACKAGE_NAME, "lib1")]

    @pytest.fixture(scope="function", autouse=True)
    def main_setup_and_tear_down(self):
        self.REPOSITORY_ROOT.mkdir(parents=True, exist_ok=False)
        prepare_directory_with_files(directory_path=self.PACKAGE_DIR, file_names=["time_series.py", "ar_model.py"])
        prepare_directory_with_files(directory_path=self.PACKAGE_CPP_DIR, file_names=["simulation.cpp", "simulation.h"])

        yield

        shutil.rmtree(path=self.REPOSITORY_ROOT)

    @staticmethod
    def mock_request_get_valid(mocker: MockerFixture, url: str) -> MagicMock:
        if url == f"{HTML_PAGE_PYPI_URL_START}/{PACKAGE_NAME}/{VERSION}/#files":
            return mock_response_with_html_page(mocker=mocker, html_page_content=read_html_page_from_datasets(file_name="html_page_test_main_valid.html"))
        elif url == f"{SOURCE_URL_START}/packages/{PACKAGE_NAME}-{VERSION}.tar.gz":
            package_and_version = f"{PACKAGE_NAME}-{VERSION}"
            file_names_root = file_names_with_prefixes(["LICENCE", "setup.py"], package_and_version)
            file_names_package = file_names_with_prefixes(["time_series.py", "ar_model.py"], package_and_version, PACKAGE_NAME)
            file_names_cpp = file_names_with_prefixes(["simulation.cpp", "simulation.h"], package_and_version, "lib", "cpp", PACKAGE_NAME)
            return mock_response_with_source(mocker=mocker, file_names=file_names_root + file_names_package + file_names_cpp)
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_WIN}":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py", "lib1.dll"], PACKAGE_NAME))
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MUSLLINUX}":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py", "lib1.so"], PACKAGE_NAME))
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MANYLINUX}":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py", "lib1.so"], PACKAGE_NAME))
        elif url == f"{WHEEL_URL_START}/{WHEEL_CP312_MACOSX}":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py", "lib1.dylib"], PACKAGE_NAME))
        # TODO: create function file_names_with_prefix() for [os.path.join(PACKAGE_NAME, file_name) for file_name in file_names]

    @staticmethod
    def mock_request_get_invalid(mocker: MockerFixture, url: str) -> MagicMock:
        if url == f"{HTML_PAGE_PYPI_URL_START}/{PACKAGE_NAME}/{VERSION}/#files":
            return mock_response_with_html_page(mocker=mocker, html_page_content=read_html_page_from_datasets(file_name="html_page_test_main_invalid.html"))
        elif url == f"{SOURCE_URL_START}/packages/source-invalid-missing-cpp-files/{PACKAGE_NAME}-{VERSION}.tar.gz":
            package_and_version = f"{PACKAGE_NAME}-{VERSION}"
            file_names_root = file_names_with_prefixes(["LICENCE", "setup.py"], package_and_version)
            file_names_package = file_names_with_prefixes(["time_series.py", "ar_model.py"], package_and_version, PACKAGE_NAME)
            file_names_cpp = file_names_with_prefixes(["simulation.h"], package_and_version, "lib", "cpp", PACKAGE_NAME)
            return mock_response_with_source(mocker=mocker, file_names=file_names_root + file_names_package + file_names_cpp)
        elif url == f"{SOURCE_URL_START}/packages/{PACKAGE_NAME}-{VERSION}.tar.gz":
            package_and_version = f"{PACKAGE_NAME}-{VERSION}"
            file_names_root = file_names_with_prefixes(["LICENCE", "setup.py"], package_and_version)
            file_names_package = file_names_with_prefixes(["time_series.py", "ar_model.py"], package_and_version, PACKAGE_NAME)
            file_names_cpp = file_names_with_prefixes(["simulation.cpp", "simulation.h"], package_and_version, "lib", "cpp", PACKAGE_NAME)
            return mock_response_with_source(mocker=mocker, file_names=file_names_root + file_names_package + file_names_cpp)
        elif url == f"{WHEEL_URL_START}/{PACKAGE_NAME}-{VERSION}-manylinux-too-many-shared-libraries.whl":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py", "lib1.so", "lib2.so", "lib3.soo"], PACKAGE_NAME))
        elif url == f"{WHEEL_URL_START}/{PACKAGE_NAME}-{VERSION}-macosx-no-shared-libraries.whl":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py"], PACKAGE_NAME))
        elif url == f"{WHEEL_URL_START}/{PACKAGE_NAME}-{VERSION}-win-missing-python-files.whl":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "lib1.dll"], PACKAGE_NAME))
        elif url == f"{WHEEL_URL_START}/{PACKAGE_NAME}-{VERSION}-musllinux-too-many-python-files.whl":
            return mock_response_with_wheel(mocker=mocker, file_names=file_names_with_prefixes(["time_series.py", "ar_model.py", "ar_model2.py", "lib1.so"], PACKAGE_NAME))

    def test_main_valid(self, mocker, capsys, file_regression):
        mocker.patch("requests.get", side_effect=lambda url: self.mock_request_get_valid(mocker=mocker, url=url))

        exit_status = main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=self.EXPECTED_SHARED_LIBRARIES, repository=self.REPOSITORY_ROOT)

        assert exit_status == 0
        file_regression.check(capsys.readouterr().out)

    def test_main_should_raise_exception_when_2_sources_instead_of_1(self, mocker, capsys):
        mock_request_get = mock_response_with_html_page(mocker=mocker, html_page_content=read_html_page_from_datasets(file_name="html_page_test_main_2_sources.html"))
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=self.EXPECTED_SHARED_LIBRARIES, repository=self.REPOSITORY_ROOT)

        assert str(ex.value) == "Expected 1 source url in the html page, but found 2 instead"

    def test_main_should_raise_exception_when_3_wheels_instead_of_4(self, mocker, capsys):
        mock_request_get = mock_response_with_html_page(mocker=mocker, html_page_content=read_html_page_from_datasets(file_name="html_page_test_main_3_wheels.html"))
        mocker.patch("requests.get", return_value=mock_request_get)

        with pytest.raises(Exception) as ex:
            main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=4, expected_shared_libraries=self.EXPECTED_SHARED_LIBRARIES, repository=self.REPOSITORY_ROOT)

        assert str(ex.value) == "Expected 4 wheel urls in the html page, but found 3 instead"

    def test_main_invalid(self, mocker, capsys, file_regression):
        mocker.patch("requests.get", side_effect=lambda url: self.mock_request_get_invalid(mocker=mocker, url=url))

        exit_status = main(index="test.pypi", package_name=PACKAGE_NAME, version=VERSION, expected_nb_wheels=6, expected_shared_libraries=self.EXPECTED_SHARED_LIBRARIES, repository=self.REPOSITORY_ROOT)

        assert exit_status == 7
        file_regression.check(capsys.readouterr().out)

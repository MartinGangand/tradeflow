import ctypes as ct
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tradeflow.common.exceptions import UnsupportedOsException
from tradeflow.common.shared_libraries_registry import SharedLibrary, SharedLibrariesRegistry
from tradeflow.common.singleton import Singleton

SHARED_LIBRARIES_DIRECTORY = Path("temp")


@pytest.fixture
def shared_library_with_2_functions():
    shared_library = SharedLibrary(name="lib", directory=SHARED_LIBRARIES_DIRECTORY)
    shared_library.add_function(name="function_1", argtypes=[ct.c_int, ct.POINTER(ct.c_double)], restype=ct.c_int)
    shared_library.add_function(name="function_2", argtypes=[ct.c_double], restype=ct.c_double)
    return shared_library


class TestSharedLibrariesRegistry:

    @pytest.fixture(scope="function", autouse=True)
    def reset_singleton(self):
        yield
        Singleton._instances.clear()

    def test_load_shared_library(self, mocker, shared_library_with_2_functions):
        mock_get_shared_libraries = mocker.patch.object(SharedLibrariesRegistry, "_get_shared_libraries", return_value=[shared_library_with_2_functions])
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=True)
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        registry = SharedLibrariesRegistry()
        mock_get_shared_libraries.assert_called_once()
        assert registry._name_to_shared_library == {"lib": shared_library_with_2_functions}

        shared_library_1 = registry.find("lib")
        shared_library_2 = registry.find("lib")
        assert shared_library_1 is shared_library_2

        cdll1 = shared_library_1.load()
        cdll2 = shared_library_2.load()
        assert cdll1 is cdll2
        mock_cdll.assert_called_once()

    def test_shared_library_registry_should_be_a_singleton(self, mocker, shared_library_with_2_functions):
        mock_get_shared_libraries = mocker.patch.object(SharedLibrariesRegistry, "_get_shared_libraries", return_value=[shared_library_with_2_functions])
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=True)
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        registry_1 = SharedLibrariesRegistry()
        mock_get_shared_libraries.assert_called_once()

        registry_2 = SharedLibrariesRegistry()
        mock_get_shared_libraries.assert_called_once()  # _get_shared_libraries should not have been called again because SharedLibrariesRegistry should be initialized only once

        assert registry_1 == registry_2
        assert registry_1._name_to_shared_library == {"lib": shared_library_with_2_functions}
        assert registry_2._name_to_shared_library == {"lib": shared_library_with_2_functions}

        cdll1 = registry_1.find("lib").load()
        cdll2 = registry_2.find("lib").load()
        assert cdll1 is cdll2
        mock_cdll.assert_called_once()


class TestSharedLibrary:

    @pytest.mark.parametrize("os_name,expected_shared_library_extension", [
        ("Linux", "so"),
        ("linux", "so"),
        ("Darwin", "dylib"),
        ("darwin", "dylib"),
        ("Windows", "dll"),
        ("windows", "dll")
    ])
    def test_get_shared_library_extension(self, mocker, os_name, expected_shared_library_extension):
        mocker.patch("platform.system", return_value=os_name)

        assert SharedLibrary.get_shared_library_extension() == expected_shared_library_extension

    def test_get_shared_library_extension_should_raise_exception_when_unsupported_os(self, mocker):
        mocker.patch("platform.system", return_value="unsupported_os")

        with pytest.raises(UnsupportedOsException) as ex:
            SharedLibrary.get_shared_library_extension()

        assert str(ex.value) == "Unsupported OS 'unsupported_os'. Supported OS values are Linux, Darwin, and Windows."

    @pytest.mark.parametrize("os_name,shared_library_extension", [
        ("Linux", "so"),
        ("Darwin", "dylib"),
        ("Windows", "dll")
    ])
    def test_load(self, mocker, shared_library_with_2_functions, os_name, shared_library_extension):
        mocker.patch("platform.system", return_value=os_name)
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=True)
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        cdll = shared_library_with_2_functions.load()

        expected_shared_library_path = SHARED_LIBRARIES_DIRECTORY.joinpath(f"lib.{shared_library_extension}")
        mock_cdll.assert_called_once_with(str(expected_shared_library_path), winmode=0)

        loaded_function_1 = getattr(cdll, "function_1")
        assert getattr(loaded_function_1, SharedLibrary.ARGUMENT_TYPES) == (ct.c_int, ct.POINTER(ct.c_double))
        assert getattr(loaded_function_1, SharedLibrary.RESULT_TYPE) == ct.c_int

        loaded_function_2 = getattr(cdll, "function_2")
        assert getattr(loaded_function_2, SharedLibrary.ARGUMENT_TYPES) == (ct.c_double,)
        assert getattr(loaded_function_2, SharedLibrary.RESULT_TYPE) == ct.c_double

    def test_load_should_cache_loaded_shared_libraries(self, mocker, shared_library_with_2_functions):
        mocker.patch("platform.system", return_value="Windows")
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=True)
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        expected_shared_library_path = SHARED_LIBRARIES_DIRECTORY.joinpath(f"lib.dll")

        cdll1 = shared_library_with_2_functions.load()
        mock_cdll.assert_called_once_with(str(expected_shared_library_path), winmode=0)
        assert shared_library_with_2_functions._loaded is cdll1

        cdll2 = shared_library_with_2_functions.load()
        mock_cdll.assert_called_once_with(str(expected_shared_library_path), winmode=0)  # ctypes.CDLL should not have been called again because the cdll is cached
        assert shared_library_with_2_functions._loaded is cdll2

        assert cdll1 is cdll2

    def test_load_should_raise_exception_when_file_does_not_exist(self, mocker):
        mocker.patch("platform.system", return_value="Linux")

        shared_library = SharedLibrary(name="lib", directory=SHARED_LIBRARIES_DIRECTORY)
        with pytest.raises(FileNotFoundError) as ex:
            shared_library.load()

        assert str(ex.value) == f"Shared library 'lib.so' not found in directory '{str(SHARED_LIBRARIES_DIRECTORY)}'."

import ctypes as ct
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tradeflow.common.exceptions import UnsupportedOsException, SharedLibraryNotFoundException
from tradeflow.common.shared_libraries_registry import SharedLibrary, SharedLibrariesRegistry, Function
from tradeflow.common.singleton import Singleton

SHARED_LIBRARIES_DIRECTORY = Path("temp")


@pytest.fixture
def shared_library_with_2_functions(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=True)

    function_1 = Function(name="function_1", argtypes=[ct.c_int, ct.POINTER(ct.c_double)], restype=ct.c_int)
    function_2 = Function(name="function_2", argtypes=[ct.c_double], restype=ct.c_double)

    return SharedLibrary(name="lib", directory=SHARED_LIBRARIES_DIRECTORY, functions=[function_1, function_2])


class TestSharedLibrariesRegistry:

    @pytest.fixture(scope="function", autouse=True)
    def reset_singleton(self):
        yield
        Singleton._instances.clear()

    def test_find(self, mocker, shared_library_with_2_functions):
        mock_get_shared_libraries = mocker.patch.object(SharedLibrariesRegistry, "_get_shared_libraries", return_value=[shared_library_with_2_functions])

        registry = SharedLibrariesRegistry()
        assert registry._name_to_shared_library == {"lib": shared_library_with_2_functions}
        assert mock_get_shared_libraries.call_count == 1

        shared_library_1 = registry.find_shared_library(name="lib")
        assert shared_library_1 is shared_library_with_2_functions

    def test_find_should_raise_exception_when_shared_library_not_in_registry(self):
        registry = SharedLibrariesRegistry()
        with pytest.raises(SharedLibraryNotFoundException) as ex:
            registry.find_shared_library(name="lib")

        assert str(ex.value) == "Shared library 'lib' not found in the registry."

    def test_shared_library_registry_should_be_a_singleton(self, mocker, shared_library_with_2_functions):
        mock_get_shared_libraries = mocker.patch.object(SharedLibrariesRegistry, "_get_shared_libraries", return_value=[shared_library_with_2_functions])

        registry_1 = SharedLibrariesRegistry()
        registry_2 = SharedLibrariesRegistry()

        assert registry_1 is registry_2
        assert registry_1._name_to_shared_library == {"lib": shared_library_with_2_functions}
        mock_get_shared_libraries.assert_called_once()  # _get_shared_libraries should be invoked only once because SharedLibrariesRegistry is initialized once

    def test_only_1_cdll_should_be_created_when_two_registries_load_the_same_shared_library(self, mocker, shared_library_with_2_functions):
        mocker.patch.object(SharedLibrariesRegistry, "_get_shared_libraries", return_value=[shared_library_with_2_functions])
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        registry_1 = SharedLibrariesRegistry()
        registry_2 = SharedLibrariesRegistry()

        cdll_1 = registry_1.find_shared_library(name="lib").load()
        cdll_2 = registry_2.find_shared_library(name="lib").load()
        assert cdll_1 is cdll_2
        mock_cdll.assert_called_once()


class TestSharedLibrary:

    @pytest.mark.parametrize("os_name,expected_shared_library_extension", [
        ("Linux", "so"),
        ("Darwin", "dylib"),
        ("Windows", "dll")
    ])
    def test_load(self, mocker, shared_library_with_2_functions, os_name, expected_shared_library_extension):
        mocker.patch("platform.system", return_value=os_name)
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        expected_shared_library_path = str(SHARED_LIBRARIES_DIRECTORY.joinpath(f"lib.{expected_shared_library_extension}"))

        cdll = shared_library_with_2_functions.load()
        mock_cdll.assert_called_once_with(expected_shared_library_path, winmode=0)
        assert shared_library_with_2_functions._cdll is cdll

        loaded_function_1 = getattr(cdll, "function_1")
        assert getattr(loaded_function_1, SharedLibrary.ARGUMENT_TYPES) == (ct.c_int, ct.POINTER(ct.c_double))
        assert getattr(loaded_function_1, SharedLibrary.RESULT_TYPE) == ct.c_int

        loaded_function_2 = getattr(cdll, "function_2")
        assert getattr(loaded_function_2, SharedLibrary.ARGUMENT_TYPES) == (ct.c_double,)
        assert getattr(loaded_function_2, SharedLibrary.RESULT_TYPE) == ct.c_double

    def test_only_1_cdll_should_be_created_when_loading_shared_library_twice(self, mocker, shared_library_with_2_functions):
        mocker.patch("platform.system", return_value="Windows")
        mock_cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        expected_shared_library_path = str(SHARED_LIBRARIES_DIRECTORY.joinpath(f"lib.dll"))

        cdll1 = shared_library_with_2_functions.load()
        mock_cdll.assert_called_once_with(expected_shared_library_path, winmode=0)
        assert shared_library_with_2_functions._cdll is cdll1

        cdll2 = shared_library_with_2_functions.load()
        assert mock_cdll.call_count == 1  # ctypes.CDLL should not be called again because the cdll is cached
        assert shared_library_with_2_functions._cdll is cdll2

        assert cdll1 is cdll2

    def test_load_should_raise_exception_when_file_does_not_exist(self, mocker):
        mocker.patch("platform.system", return_value="Linux")

        shared_library = SharedLibrary(name="lib", directory=SHARED_LIBRARIES_DIRECTORY, functions=[])
        with pytest.raises(FileNotFoundError) as ex:
            shared_library.load()

        assert str(ex.value) == f"Shared library 'lib.so' not found in directory '{str(SHARED_LIBRARIES_DIRECTORY)}'."

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

import ctypes as ct
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tradeflow.common.exceptions import UnsupportedOsException
from tradeflow.common.shared_libraries_registry import SharedLibrary, SharedLibrariesRegistry

SHARED_LIBRARIES_DIRECTORY = Path("temp")


@pytest.fixture
def shared_library_with_2_functions():
    shared_library = SharedLibrary(name="lib", directory=SHARED_LIBRARIES_DIRECTORY)
    shared_library.add_function(name="function_1", argtypes=[ct.c_int, ct.POINTER(ct.c_double)], restype=ct.c_int)
    shared_library.add_function(name="function_2", argtypes=[ct.c_double], restype=ct.c_double)
    return shared_library


class TestSharedLibrariesRegistry:

    def test_load_shared_library(self, mocker, shared_library_with_2_functions):
        load_shared_library = mocker.patch.object(shared_library_with_2_functions, "load")

        registry = SharedLibrariesRegistry().add_shared_library(shared_library_with_2_functions)
        registry.load_shared_library("lib")

        load_shared_library.assert_called_once()
        assert len(registry._name_to_shared_library) == 1
        assert registry._name_to_shared_library["lib"] == shared_library_with_2_functions
        assert len(registry._name_to_loaded_shared_library) == 1


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
        cdll = mocker.patch("ctypes.CDLL", return_value=MagicMock())

        lib = shared_library_with_2_functions.load()

        expected_shared_library_path = SHARED_LIBRARIES_DIRECTORY.joinpath(f"lib.{shared_library_extension}")
        cdll.assert_called_once_with(str(expected_shared_library_path), winmode=0)

        loaded_function_1 = getattr(lib, "function_1")
        assert getattr(loaded_function_1, SharedLibrary.ARGUMENT_TYPES) == (ct.c_int, ct.POINTER(ct.c_double))
        assert getattr(loaded_function_1, SharedLibrary.RESULT_TYPE) == ct.c_int

        loaded_function_2 = getattr(lib, "function_2")
        assert getattr(loaded_function_2, SharedLibrary.ARGUMENT_TYPES) == (ct.c_double,)
        assert getattr(loaded_function_2, SharedLibrary.RESULT_TYPE) == ct.c_double

    def test_load_should_raise_exception_when_file_does_not_exist(self, mocker, shared_library_with_2_functions):
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch("pathlib.Path.exists", return_value=False)
        mocker.patch("pathlib.Path.is_file", return_value=False)

        with pytest.raises(FileNotFoundError) as ex:
            shared_library_with_2_functions.load()

        assert str(ex.value) == f"Shared library 'lib.so' not found in directory '{str(SHARED_LIBRARIES_DIRECTORY)}'."

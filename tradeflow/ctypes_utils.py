import ctypes as ct
import fnmatch
import os
import platform
from pathlib import Path
from typing import Literal, List

from statsmodels.tools.typing import ArrayLike1D

from tradeflow import logger_utils
from tradeflow.constants import Os, SharedLibraryExtension
from tradeflow.definitions import PACKAGE_DIR
from tradeflow.exceptions import UnsupportedOsException

logger = logger_utils.get_logger(__name__)

ARGUMENT_TYPES = "argtypes"
RESULT_TYPES = "restype"

SHARED_LIBRARY_NAME = "libtradeflow"
SHARED_LIBRARY_EXTENSIONS = ["so", "dll", "dylib"]

function_to_argtypes_and_restype = {
    "simulate": {
        # size (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), seed (int), res (int*)
        ARGUMENT_TYPES: (ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.c_int, ct.POINTER(ct.c_int)),
        RESULT_TYPES: ct.c_void_p
    }
}


def get_c_type_from_string(c_type_str: Literal["int", "double"]) -> ct._SimpleCData:
    """
    Return a ctypes type corresponding to a given C data type (in a string).

    Parameters:
    -----------
    c_type_str : Literal["int", "double"]
        A string indicating the desired C data type.

    Returns:
    --------
    ct._SimpleCData
        The corresponding ctypes type.
    """
    c_type_str_to_c_type = {
        "int": ct.c_int,
        "double": ct.c_double
    }

    if c_type_str not in c_type_str_to_c_type:
        raise Exception(f"Unknown type {c_type_str}")

    return c_type_str_to_c_type[c_type_str]


class CArray:

    @staticmethod
    def of(c_type_str: Literal["int", "double"], arr: ArrayLike1D) -> ct.Array:
        """
        Create a ctypes array from a Python list.

        Parameters
        ----------
        c_type_str : {'int', 'double'}
            The type of the array to be created.
        arr : array_like
            The array from which to create the ctypes array.

        Returns
        -------
        ct.Array
            The ctypes array containing the elements of `arr`.
        """
        c_type = get_c_type_from_string(c_type_str=c_type_str)
        return (c_type * len(arr))(*arr)


class CArrayEmpty:

    @staticmethod
    def of(c_type_str: Literal["int", "double"], size: int) -> ct.Array:
        """
        Create an empty ctypes array of a given size.

        Parameters
        ----------
        c_type_str : {'int', 'double'}
            The type of the array to be created.
        size : int
            The size of the ctypes array to create.

        Returns
        -------
        ct.Array
            The empty ctypes array of size `size`.
        """
        c_type_str = get_c_type_from_string(c_type_str=c_type_str)
        return (c_type_str * size)()


def load_shared_library() -> ct.CDLL:
    """
    Return the shared library of the project.

    Returns
    -------
    ct.CDLL
        The loaded shared library.
    """
    shared_library_extension = get_shared_library_extension()
    lib_file = get_shared_library_file(directory=PACKAGE_DIR, shared_library_name=SHARED_LIBRARY_NAME, shared_library_extension=shared_library_extension)
    shared_lib = ct.CDLL(lib_file, winmode=0)
    set_shared_library_functions(shared_lib=shared_lib)

    return shared_lib


def get_shared_library_extension() -> str:
    # TODO: test
    os_to_shared_library_extension = {
        Os.LINUX: SharedLibraryExtension.SO,
        Os.DARWIN: SharedLibraryExtension.DYLIB,
        Os.WINDOWS: SharedLibraryExtension.DLL,
    }
    os = platform.system()
    if os not in os_to_shared_library_extension:
        raise UnsupportedOsException(f"OS '{os}' is not supported, it must be either Linux, Darwin or Windows.")

    return os_to_shared_library_extension[os]


def set_shared_library_functions(shared_lib: ct.CDLL) -> None:
    """
    Set argument and result types of functions in the shared library.

    Parameters
    ----------
    shared_lib : ct.CDLL
        The shared library for which to set argument and result types for all functions.
    """
    for function_name in function_to_argtypes_and_restype.keys():
        setattr(getattr(shared_lib, function_name), ARGUMENT_TYPES, function_to_argtypes_and_restype.get(function_name).get(ARGUMENT_TYPES))
        setattr(getattr(shared_lib, function_name), RESULT_TYPES, function_to_argtypes_and_restype.get(function_name).get(RESULT_TYPES))


def get_shared_library_file(directory: Path, shared_library_name: str, shared_library_extension: str) -> str:
    """
    Return the path to the shared library `shared_library_name`.

    Parameters
    ----------
    directory : Path
        The directory in which to search for the shared library.
    shared_library_name : str
        The name of the shared library.
    shared_library_extension : str
        The extension of the shared library (so, dylib or dll).

    Returns
    -------
    str
        The path to the shared library, the extension of the file can be 'so' (Linux), 'dll' (Windows), 'dylib' (macOS), or 'pyd'.
    """
    shared_library = directory.joinpath(f"{shared_library_name}.{shared_library_extension}")
    if not (shared_library.exists() and shared_library.is_file()):
        raise FileNotFoundError(f"No shared library found for name '{shared_library_name}' with extension '{shared_library_extension}' in directory {directory}.")

    return str(shared_library)

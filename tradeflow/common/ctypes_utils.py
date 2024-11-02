import ctypes as ct
import platform
from pathlib import Path
from typing import Literal, Dict, Tuple

from statsmodels.tools.typing import ArrayLike1D

from tradeflow.common.shared_libraries_functions import shared_library_to_function_to_argtypes_and_restype, ARGUMENT_TYPES, \
    RESULT_TYPES, SHARED_LIBRARIES_DIRECTORY, Os, SharedLibraryExtension, UnsupportedOsException
from tradeflow.common import logger_utils

logger = logger_utils.get_logger(__name__)


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


def load_shared_library(shared_library_name: str) -> ct.CDLL:
    """
    Return the shared library of the project.

    Returns
    -------
    ct.CDLL
        The loaded shared library.
    """
    shared_library_extension = get_shared_library_extension()
    shared_library_file = get_shared_library_file(directory=SHARED_LIBRARIES_DIRECTORY, shared_library_name=shared_library_name, shared_library_extension=shared_library_extension)
    shared_library = ct.CDLL(shared_library_file, winmode=0)
    set_shared_library_functions(shared_lib=shared_library, function_to_argtypes_and_restype=shared_library_to_function_to_argtypes_and_restype[shared_library_name])

    return shared_library


def get_shared_library_extension() -> str:
    """
    Determine the shared library file extension based on the operating system.

    Returns
    -------
    str
        The file extension for shared libraries, specific to the current operating system.

    Raises
    ------
    UnsupportedOsException
        If the operating system is not Linux, Darwin (macOS), or Windows.
    """
    os_name_to_shared_library_extension = {
        Os.LINUX: SharedLibraryExtension.SO,
        Os.DARWIN: SharedLibraryExtension.DYLIB,
        Os.WINDOWS: SharedLibraryExtension.DLL,
    }

    os_name = platform.system().lower()
    extension = os_name_to_shared_library_extension.get(os_name)

    if extension is None:
        raise UnsupportedOsException(f"Unsupported OS '{os_name}'. Supported OS values are Linux, Darwin, and Windows.")

    return extension


def set_shared_library_functions(shared_lib: ct.CDLL, function_to_argtypes_and_restype: Dict[str, Dict[str, Tuple[str]]]) -> None:
    """
    Set argument and result types of functions in the shared library.

    Parameters
    ----------
    shared_lib : ct.CDLL
        The shared library for which to set argument and result types for all functions.
    function_to_argtypes_and_restype : dict of
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

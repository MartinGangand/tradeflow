import ctypes as ct
import glob
from pathlib import Path
from typing import Literal

from statsmodels.tools.typing import ArrayLike1D

from tradeflow import logger_utils
from tradeflow.definitions import ROOT_DIR
from tradeflow.exceptions import TooManySharedLibrariesException

logger = logger_utils.get_logger(__name__)

ARGUMENT_TYPES = "argtypes"
RESULT_TYPES = "restype"

SHARED_LIBRARY_NAME = "libcpp"
SHARED_LIBRARY_EXTENSIONS = ["so", "dll", "dylib", "pyd"]

function_to_argtypes_and_restype = {
    "my_simulate": {
        # size (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), seed (int), simulation (int*)
        ARGUMENT_TYPES: (ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.c_int, ct.POINTER(ct.c_int)),
        RESULT_TYPES: ct.c_void_p
    }
}


class CArray:

    @staticmethod
    def of(c_type: Literal["int", "double"], arr: ArrayLike1D) -> ct.Array:
        """
        Create a ctypes array from a Python list.

        Parameters
        ----------
        c_type : {'int', 'double'}
            The type of the array to be created.
        arr : array_like
            The array from which to create the ctypes array.

        Returns
        -------
        ct.Array
            The ctypes array containing the elements of `arr`.
        """
        match c_type:
            case "int":
                c_type = ct.c_int
            case "double":
                c_type = ct.c_double
            case _:
                raise Exception(f"Unknown type {c_type}")

        return (c_type * len(arr))(*arr)


class CArrayEmpty:

    @staticmethod
    def of(c_type: Literal["int", "double"], size: int) -> ct.Array:
        """
        Create an empty ctypes array of a given size.

        Parameters
        ----------
        c_type : {'int', 'double'}
            The type of the array to be created.
        size : int
            The size of the ctypes array to create.

        Returns
        -------
        ct.Array
            The empty ctypes array of size `size`.
        """
        match c_type:
            case "int":
                c_type = ct.c_int
            case "double":
                c_type = ct.c_double
            case _:
                raise Exception(f"Unknown type {c_type}")

        return (c_type * size)()


def load_shared_library() -> ct.CDLL:
    """
    Return the shared library of the project.

    Returns
    -------
    ct.CDLL
        The loaded shared library.
    """
    lib_file = get_shared_library_file(directory=ROOT_DIR, shared_library_name=SHARED_LIBRARY_NAME)
    shared_lib = ct.CDLL(lib_file, winmode=0)
    set_shared_library_functions(shared_lib=shared_lib)

    return shared_lib


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


def get_shared_library_file(directory: str, shared_library_name: str) -> str:
    """
    Return the path to the shared library `shared_library_name`.

    Parameters
    ----------
    directory : str
        The directory in which to search the shared library.
    shared_library_name : str
        The name of the shared library.

    Returns
    -------
    str
        The path to the shared library, the extension of the file can be 'so' (Linux), 'dll' (Windows), 'dylib' (macOS), or 'pyd'.
    """
    directory = Path(directory)
    shared_library_files = []
    for potential_extension in SHARED_LIBRARY_EXTENSIONS:
        shared_library_files.extend(glob.glob(f"{shared_library_name}.{potential_extension}", root_dir=directory))
        shared_library_files.extend(glob.glob(f"{shared_library_name}.*.{potential_extension}", root_dir=directory))

    if len(shared_library_files) == 0:
        raise FileNotFoundError(f"No shared library found for name '{shared_library_name}' with one of the extension in {SHARED_LIBRARY_EXTENSIONS} in directory {str(directory)}.")
    if len(shared_library_files) >= 2:
        raise TooManySharedLibrariesException(f"{len(shared_library_files)} shared libraries found with name '{shared_library_name}' with extension in {SHARED_LIBRARY_EXTENSIONS} have been found: {', '.join(shared_library_files)} in directory: {str(directory)}.")

    return str(directory.joinpath(shared_library_files[0]))

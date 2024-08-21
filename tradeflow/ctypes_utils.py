import ctypes as ct
import glob
from pathlib import Path
from typing import Literal

from statsmodels.tools.typing import ArrayLike1D

from tradeflow import logger_utils
from tradeflow.constants import SHARED_LIBRARY_EXTENSIONS
from tradeflow.definitions import ROOT_DIR

logger = logger_utils.get_logger(__name__)

lib_to_function_to_argtypes_and_restype = {
    "simulate": {
        "my_simulate": {
            # size (int), seed (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), simulation (int*)
            "argtypes": (ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int),
                         ct.POINTER(ct.c_int)),
            "restype": ct.c_void_p
        }
    }
}

ARGSTYPES = "argtypes"
RESTYPE = "restype"


class CArray:

    @staticmethod
    def of(c_type: Literal["int", "double"], arr: ArrayLike1D) -> ct.Array:
        """
        Create a ctypes array from a Python array.

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


def load_shared_library(shared_lib_name: str) -> ct.CDLL:
    """
    Return a shared library written in C++ for efficiency reasons.

    Returns
    -------
    ct.CDLL
        The loaded shared library.
    """
    lib_file = get_shared_library_file(directory=ROOT_DIR, lib_name=shared_lib_name)
    cpp_lib = ct.CDLL(lib_file, winmode=0)
    set_modules_functions_argtypes_and_restype(cpp_lib=cpp_lib, shared_lib_name=shared_lib_name)

    return cpp_lib


def set_module_functions_argtypes_and_restype(cpp_lib: ct.CDLL, shared_lib_name: str) -> None:
    """
    Set the argument and result types of all function of a module.

    Parameters
    ----------
    cpp_lib : ct.CDLL
        The shared library for which to set argument and results types for all functions.
    shared_library_name : str
        The nane of the shared library (the name of the C++ file).
    """
    function_to_argtypes_and_restype = lib_to_function_to_argtypes_and_restype.get(shared_lib_name)
    for function in function_to_argtypes_and_restype.keys():
        setattr(getattr(cpp_lib, function), ARGSTYPES, function_to_argtypes_and_restype.get(function).get(ARGSTYPES))
        setattr(getattr(cpp_lib, function), RESTYPE, function_to_argtypes_and_restype.get(function).get(RESTYPE))


def get_shared_library_file(directory: str, lib_name: str) -> str:
    # TODO: doc
    dir_ = directory
    directory = Path(directory)
    shared_library_files = []
    for potential_extension in SHARED_LIBRARY_EXTENSIONS:
        shared_library_files.extend(glob.glob(f"{lib_name}.{potential_extension}", root_dir=directory))
        shared_library_files.extend(glob.glob(f"{lib_name}.*.{potential_extension}", root_dir=directory))

    if len(shared_library_files) == 0:
        raise FileNotFoundError(
            f"No shared libray file for library {lib_name} with one of the extension in {SHARED_LIBRARY_EXTENSIONS} in directory {dir_}")
    if len(shared_library_files) >= 2:
        raise Exception(
            f"{len(shared_library_files)} shared library files for library {lib_name} with extension in {SHARED_LIBRARY_EXTENSIONS} have been found: {', '.join(shared_library_files)} (directory: {directory})")

    return str(directory.joinpath(shared_library_files[0]))

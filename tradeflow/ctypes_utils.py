import ctypes as ct
import glob
import os
import pathlib
from pathlib import Path
from typing import Literal

from statsmodels.tools.typing import ArrayLike1D

from tradeflow import logger_utils
from tradeflow.constants import SHARED_LIBRARY_EXTENSIONS
from tradeflow.definitions import ROOT_DIR

logger = logger_utils.get_logger(__name__)


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


def load_simulate_lib() -> ct.CDLL:
    """
    Return the shared library used to simulate signs.

    The simulation of signs is performed with the `simulate(...)` function.

    This function is written in C++ for efficiency reasons.

    Returns
    -------
    ct.CDLL
        The loaded shared library.
    """
    lib_file = get_shared_library_file(directory=ROOT_DIR, lib_name="simulate")
    cpp_lib = ct.CDLL(lib_file, winmode=0)

    # Arguments: size (int), seed (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), simulation (int*)
    # setattr(getattr(cpp_lib, "my_simulate"), "argtypes", (ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int)))
    cpp_lib.my_simulate.argtypes = (ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
    cpp_lib.my_simulate.restype = ct.c_void_p
    return cpp_lib


def get_shared_library_file(directory: str, lib_name: str) -> str:
    dir_ = directory
    directory = Path(directory)
    shared_library_files = []
    for potential_extension in SHARED_LIBRARY_EXTENSIONS:
        shared_library_files.extend(glob.glob(f"{lib_name}.{potential_extension}", root_dir=directory))
        shared_library_files.extend(glob.glob(f"{lib_name}.*.{potential_extension}", root_dir=directory))

    if len(shared_library_files) == 0:
        raise FileNotFoundError(f"No shared libray file for library {lib_name} with one of the extension in {SHARED_LIBRARY_EXTENSIONS} in directory {dir_}")
    if len(shared_library_files) >= 2:
        raise Exception(f"{len(shared_library_files)} shared library files for library {lib_name} with extension in {SHARED_LIBRARY_EXTENSIONS} have been found: {', '.join(shared_library_files)} (directory: {directory})")

    return str(directory.joinpath(shared_library_files[0]))

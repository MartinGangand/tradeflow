import ctypes as ct
import glob
import os
import pathlib
from typing import Literal

import numpy as np
from statsmodels.tools.typing import ArrayLike1D


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
    root_dir = pathlib.Path(__file__).parent.absolute()
    lib_file = glob.glob('simulate*.so', root_dir=root_dir)[0]
    clib = ct.CDLL(os.path.join(root_dir, lib_file), winmode=0)

    # Arguments: size (int), seed (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), simulation (int*)
    clib.my_simulate.argtypes = (ct.c_int, ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
    clib.my_simulate.restype = ct.c_void_p
    return clib

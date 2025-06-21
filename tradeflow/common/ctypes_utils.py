import ctypes as ct
from typing import Literal, Any

from statsmodels.tools.typing import ArrayLike1D

from tradeflow.common import logger_utils

logger = logger_utils.get_logger(__name__)


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
            The type of elements in the array to be created.
        size : int
            The size of the ctypes array to create.

        Returns
        -------
        ct.Array
            The empty ctypes array of size `size`.
        """
        c_type_str = get_c_type_from_string(c_type_str=c_type_str)
        return (c_type_str * size)()


def get_c_type_from_string(c_type_str: Literal["int", "double"]) -> Any:
    """
    Return a ctypes type corresponding to a given C data type (from a string).

    Parameters:
    -----------
    c_type_str : {'int', 'double'}
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

import ctypes as ct
from pathlib import Path

SHARED_LIBRARIES_DIRECTORY = Path(__file__).parent.parent

ARGUMENT_TYPES = "argtypes"
RESULT_TYPES = "restype"

# TODO: create class? Registry?
shared_library_to_function_to_argtypes_and_restype = {
    "libtradeflow": {
        "simulate": {
            # size (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), seed (int), res (int*)
            ARGUMENT_TYPES: (ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.c_int, ct.POINTER(ct.c_int)),
            RESULT_TYPES: ct.c_void_p
        }
    }
}


class Os:
    LINUX = "linux"
    DARWIN = "darwin"
    WINDOWS = "windows"


class SharedLibraryExtension:
    SO = "so"
    DYLIB = "dylib"
    DLL = "dll"

class UnsupportedOsException(Exception):
    """Raised when the OS is not supported to load the shared library"""
    pass

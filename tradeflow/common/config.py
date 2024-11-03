import ctypes as ct
from pathlib import Path

from tradeflow.common.shared_libraries_registry import SharedLibrariesRegistry, SharedLibrary

SHARED_LIBRARIES_DIRECTORY = Path(__file__).parent.parent

# simulate: size (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), seed (int), res (int*)
registry = SharedLibrariesRegistry().add_shared_library(
    SharedLibrary(name="libtradeflow", directory=SHARED_LIBRARIES_DIRECTORY).add_function(name="simulate",
                                                                                          argtypes=[ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.c_int, ct.POINTER(ct.c_int)],
                                                                                          restype=ct.c_void_p)
)

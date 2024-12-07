from __future__ import annotations

import ctypes as ct
import platform
from pathlib import Path
from typing import Dict, Tuple, Union, List

from tradeflow.common import logger_utils
from tradeflow.common.config import LIBTRADEFLOW_SHARED_LIBRARY_DIRECTORY
from tradeflow.common.exceptions import UnsupportedOsException, SharedLibraryNotFoundException
from tradeflow.common.general_utils import check_condition
from tradeflow.common.singleton import Singleton

logger = logger_utils.get_logger(__name__)


class SharedLibrariesRegistry(metaclass=Singleton):

    def __init__(self) -> None:
        self._name_to_shared_library: Dict[str, SharedLibrary] = {}
        self._set_shared_libraries(self._get_shared_libraries())

    def _set_shared_libraries(self, shared_libraries: List[SharedLibrary]) -> None:
        for shared_library in shared_libraries:
            self._add_shared_library(shared_library=shared_library)

    def _get_shared_libraries(self) -> List[SharedLibrary]:
        # simulate: size (int), inverted_params (double*), constant_parameter (double), nb_params (int), last_signs (int*), seed (int), res (int*)
        simulate = Function(name="simulate", argtypes=[ct.c_int, ct.POINTER(ct.c_double), ct.c_double, ct.c_int, ct.POINTER(ct.c_int), ct.c_int, ct.POINTER(ct.c_int)], restype=ct.c_void_p)
        libtradeflow = SharedLibrary(name="libtradeflow", directory=LIBTRADEFLOW_SHARED_LIBRARY_DIRECTORY, functions=[simulate])
        return [libtradeflow]

    def _add_shared_library(self, shared_library: SharedLibrary) -> SharedLibrariesRegistry:
        assert shared_library.name not in self._name_to_shared_library
        self._name_to_shared_library[shared_library.name] = shared_library
        logger.info(f"Added shared library '{shared_library.name}' to the registry")
        return self

    def find_shared_library(self, name: str) -> SharedLibrary:
        check_condition(condition=name in self._name_to_shared_library, exception=SharedLibraryNotFoundException(f"Shared library '{name}' not found in the registry."))
        return self._name_to_shared_library.get(name)


class SharedLibrary:

    LINUX = "linux"
    DARWIN = "darwin"
    WINDOWS = "windows"

    SO = "so"
    DYLIB = "dylib"
    DLL = "dll"

    ARGUMENT_TYPES = "argtypes"
    RESULT_TYPE = "restype"

    def __init__(self, name: str, directory: Path, functions: List[Function]) -> None:
        self._name = name
        self._directory = directory
        self._functions = functions
        self._cdll = None  # Loaded shared library is cached after the first call to load()

    @property
    def name(self):
        return self._name

    def load(self) -> ct.CDLL:
        """
        Return the shared library of the project.

        Returns
        -------
        ct.CDLL
            The loaded shared library.
        """
        if self._cdll is not None:
            return self._cdll

        shared_library_extension = SharedLibrary.get_shared_library_extension()
        shared_library_path = self._directory.joinpath(f"{self._name}.{shared_library_extension}")
        check_condition(condition=shared_library_path.exists() and shared_library_path.is_file(),
                        exception=FileNotFoundError(f"Shared library '{self._name}.{shared_library_extension}' not found in directory '{self._directory}'."))

        cdll = ct.CDLL(str(shared_library_path), winmode=0)
        for function in self._functions:
            setattr(getattr(cdll, function.name), self.ARGUMENT_TYPES, function.argtypes)
            setattr(getattr(cdll, function.name), self.RESULT_TYPE, function.restype)

        logger.info(f"Loaded shared library '{self._name}'")
        self._cdll = cdll
        return self._cdll

    @staticmethod
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
            SharedLibrary.LINUX: SharedLibrary.SO,
            SharedLibrary.DARWIN: SharedLibrary.DYLIB,
            SharedLibrary.WINDOWS: SharedLibrary.DLL,
        }

        os_name = platform.system().lower()
        extension = os_name_to_shared_library_extension.get(os_name)

        check_condition(condition=extension is not None, exception=UnsupportedOsException(f"Unsupported OS '{os_name}'. Supported OS values are Linux, Darwin, and Windows."))
        return extension


class Function:

    def __init__(self, name: str, argtypes: List[Union[ct._CData, ct.POINTER(ct._CData)]], restype: Union[ct._CData, ct.POINTER(ct._CData)]) -> None:
        self._name = name
        self._argtypes = tuple(argtypes)
        self._restype = restype

    @property
    def name(self) -> str:
        return self._name

    @property
    def argtypes(self) -> Tuple[Union[ct._CData, ct.POINTER(ct._CData)], ...]:
        return self._argtypes

    @property
    def restype(self) -> Union[ct._CData, ct.POINTER(ct._CData)]:
        return self._restype

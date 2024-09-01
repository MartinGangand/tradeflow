import fnmatch
import os.path
from typing import List

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

PROJECT = "tradeflow"
CPP_FOLDER = os.path.join("lib", "cpp")
SHARED_LIBRARY_NAME = "libtradeflow"
CPP_MODULES = ["simulation"]


class CppExtension(Extension):
    pass


class new_build_ext(build_ext):
    extra_compile_args = {
        f"{PROJECT}.{SHARED_LIBRARY_NAME}": {
            "unix": ["-std=c++17"],
            "msvc": ["/std:c++17"]
        }
    }

    def build_extension(self, ext):
        extra_args = self.extra_compile_args.get(ext.name)
        if extra_args is not None:
            compiler_type = self.compiler.compiler_type
            ext.extra_compile_args += extra_args.get(compiler_type, [])

        build_ext.build_extension(self, ext)

    def get_export_symbols(self, ext):
        return ext.export_symbols


def build_tradeflow_cpp_extension(module: str) -> CppExtension:
    cpp_extension = CppExtension(name=f"{PROJECT}.lib{module}",
                                 sources=find_cpp_files(directory=os.path.join(CPP_FOLDER, module)),
                                 language="c++"
                                 )
    return cpp_extension


def find_cpp_files(directory: str):
    matched_files = []
    for root, _, files in os.walk(directory):
        if root == directory:
            for filename in fnmatch.filter(files, "*.cpp"):
                matched_files.append(os.path.join(directory, filename))

    return matched_files


setup(
    packages=[PROJECT, os.path.join(CPP_FOLDER, "tradeflow")],
    ext_modules=[build_tradeflow_cpp_extension(module="tradeflow")],
    cmdclass={'build_ext': new_build_ext},
    package_data={"": ["*.h"]}
)

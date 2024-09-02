import fnmatch
import os
import pathlib
from typing import List

import toml
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

PACKAGE_NAME = toml.load(pathlib.Path(__file__).parent.joinpath("pyproject.toml"))["project"]["name"]
CPP_FOLDER_RELATIVE = os.path.join("lib", "cpp")


class CppExtension(Extension):
    pass


class new_build_ext(build_ext):
    extra_compile_args = {
        "unix": ["-std=c++17"],
        "msvc": ["/std:c++17"]
    }

    def build_extension(self, ext):
        extra_args = self.extra_compile_args.get(self.compiler.compiler_type, [])
        ext.extra_compile_args += extra_args

        super().build_extension(ext)

    def get_export_symbols(self, ext):
        return ext.export_symbols


def build_cpp_module(folder_name: str) -> CppExtension:
    cpp_module = CppExtension(name=f"{PACKAGE_NAME}.lib{folder_name}",
                              sources=find_cpp_files(directory=os.path.join(CPP_FOLDER_RELATIVE, folder_name)),
                              language="c++"
                              )
    return cpp_module


def find_cpp_files(directory: str) -> List[str]:
    cpp_files = []
    for root, _, files in os.walk(directory):
        if root == directory:
            for filename in fnmatch.filter(files, "*.cpp"):
                cpp_files.append(os.path.join(directory, filename))

    return cpp_files


setup(
    packages=[PACKAGE_NAME],
    ext_modules=[build_cpp_module(folder_name="tradeflow")],
    cmdclass={'build_ext': new_build_ext}
)

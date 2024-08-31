import os.path
from typing import List

from setuptools import Extension, setup, find_packages
from setuptools.command.build_ext import build_ext

PROJECT = "tradeflow"
CPP_FOLDER = "lib/cpp"
SHARED_LIBRARY_NAME = "libcpp"
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


def build_cpp_extension() -> List[CppExtension]:
    cpp_extension = CppExtension(name=f"{PROJECT}.{SHARED_LIBRARY_NAME}",
                                 sources=[os.path.join(CPP_FOLDER, f"{cpp_module}.cpp") for cpp_module in CPP_MODULES],
                                 language="c++"
                                 )
    return [cpp_extension]


setup(
    packages=[PROJECT, CPP_FOLDER],
    ext_modules=build_cpp_extension(),
    cmdclass={'build_ext': new_build_ext},
    package_data={"": ["*.h"]}
)

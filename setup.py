from typing import List

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

PROJECT = "tradeflow"
SHARED_LIBRARY_NAME = "libcpp"
CPP_MODULES = ["simulate"]


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
        return ext.export_symbols + list(map(lambda module: f"my_{module}", CPP_MODULES))


def build_cpp_extension() -> List[CppExtension]:
    cpp_extension = CppExtension(name=f"{PROJECT}.{SHARED_LIBRARY_NAME}",
                                 sources=[f"{PROJECT}/{cpp_module}.cpp" for cpp_module in CPP_MODULES],
                                 language="c++"
                                 )
    return [cpp_extension]


setup(
    packages=[PROJECT],
    ext_modules=build_cpp_extension(),
    cmdclass={'build_ext': new_build_ext}
)

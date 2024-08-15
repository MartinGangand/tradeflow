from typing import List

from setuptools import Extension, setup, find_packages
from setuptools.command.build_ext import build_ext

CPP_MODULES = ["simulate"]


class CTypesExtension(Extension):
    pass


class new_build_ext(build_ext):
    extra_compile_args = {
        'tradeflow.simulate': {
            'unix': ['-std=c++17'],
            'msvc': ['/std:c++17']
        }
    }

    def build_extension(self, ext):
        extra_args = self.extra_compile_args.get(ext.name)
        if extra_args is not None:
            ctype = self.compiler.compiler_type
            ext.extra_compile_args = extra_args.get(ctype, [])

        build_ext.build_extension(self, ext)

    def get_export_symbols(self, ext):
        return ext.export_symbols + list(map(lambda module: "my_" + module, CPP_MODULES))


def build_cpp_extensions() -> List[CTypesExtension]:
    cpp_extensions = []
    for cpp_module in CPP_MODULES:
        cpp_extension = CTypesExtension(name=f"tradeflow.{cpp_module}",
                                        sources=[f"tradeflow/{cpp_module}.cpp"],
                                        language="c++"
                                        )
        cpp_extensions.append(cpp_extension)
    return cpp_extensions


setup(
    packages=find_packages(),
    ext_modules=build_cpp_extensions(),
    cmdclass={'build_ext': new_build_ext}
)

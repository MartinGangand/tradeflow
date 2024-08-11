import os
import sys

from setuptools import Extension, setup, find_packages
from setuptools.command.build_ext import build_ext


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

    # def build_extension(self, ext):
    #     self._ctypes = isinstance(ext, CTypesExtension)
    #     return super().build_extension(ext)
    # def finalize_options(self):
    #     super().finalize_options()
    #     self.compiler = "unix"

    def get_export_symbols(self, ext):
        print("===================", ext.export_symbols + ["my_simulate"], "=====")
        return ext.export_symbols + ["my_simulate"]

    # def get_ext_filename(self, ext_name):
    #     if self._ctypes:
    #         return ext_name + ".so"
    #     return super().get_ext_filename(ext_name)


setup(
    packages=find_packages(),
    py_modules=["tradeflow.ar_model"],
    ext_modules=[
        CTypesExtension(
            name="tradeflow.simulate",
            sources=["tradeflow/simulate.cpp"],
            language="c++"
        )
    ],
    cmdclass={'build_ext': new_build_ext}
)


# Windows:
# COMPILER: <distutils._msvccompiler.MSVCCompiler> & msvc | OS: nt | SYS: win32
#
# Ubuntu:
# COMPILER: <distutils.unixccompiler.UnixCCompiler> & unix | OS: posix | SYS: linux
#
# Mac:
# COMPILER: <distutils.unixccompiler.UnixCCompiler> & unix | OS: posix | SYS: darwin
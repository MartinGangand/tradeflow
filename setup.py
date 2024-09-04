import fnmatch
import os.path
import pathlib
import sys
from glob import glob
from typing import List
import subprocess

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

PROJECT = "tradeflow"
# CPP_FOLDER = os.path.join("lib", "cpp")
# SHARED_LIBRARY_NAME = "libtradeflow"
# CPP_MODULES = ["simulation"]


def find_cpp_files(directory: str):
    matched_files = []
    for root, _, files in os.walk(directory):
        if root == directory:
            for filename in fnmatch.filter(files, "*.cpp"):
                matched_files.append(os.path.join(directory, filename))

    return matched_files


class CMakeExtension(Extension):

    def __init__(self, name):
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])


class new_build_ext(build_ext):

    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)
        super().run()

    def build_cmake(self, ext):
        cwd = pathlib.Path().absolute()

        # these dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        build_temp = pathlib.Path(self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)
        extdir = pathlib.Path(self.get_ext_fullpath(ext.name))
        extdir.mkdir(parents=True, exist_ok=True)

        # example of cmake args
        config = 'Debug' if self.debug else 'Release'
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + str(extdir.parent.absolute()),
            '-DCMAKE_BUILD_TYPE=' + config
        ]

        # example of build args
        build_args = [
            '--config', config,
            # '--', '-j4'
        ]

        os.chdir(str(build_temp))
        self.spawn(['cmake', str(cwd.joinpath('lib', 'cpp', 'tradeflow').absolute())] + cmake_args)
        if not self.dry_run:
            self.spawn(['cmake', '--build', '.'] + build_args)
        # Troubleshooting: if fail on line above then delete all possible
        # temporary CMake files including "CMakeCache.txt" in top level dir.
        os.chdir(str(cwd))


setup(
    packages=[PROJECT],
    ext_modules=[CMakeExtension("tradeflow/libtradeflow")],
    cmdclass={'build_ext': new_build_ext},
)

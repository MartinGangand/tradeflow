import os
import re
import subprocess
import sys
from pathlib import Path

import toml
from setuptools import Extension, setup, find_packages
from setuptools.command.build_ext import build_ext

PACKAGE_NAME = toml.load(Path(__file__).parent.joinpath("pyproject.toml"))["project"]["name"]


class CMakeExtension(Extension):

    def __init__(self, name: str):
        super().__init__(name, sources=[])


class CMakeBuild(build_ext):

    def build_extension(self, ext: CMakeExtension) -> None:
        cwd = Path().cwd()
        extdir = cwd.joinpath(self.get_ext_fullpath(ext.name)).parent.resolve()

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        build_type = "Debug" if debug else "Release"

        cmake_args = [
            f"-DMY_PROJECT_SOURCE_DIR={extdir}",
            f"-DCMAKE_BUILD_TYPE={build_type}"
        ]
        build_args = ["--config", build_type]

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        build_temp = Path(self.build_temp).joinpath(ext.name)
        build_temp.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["cmake", cwd, *cmake_args], cwd=build_temp, check=True
        )
        subprocess.run(
            ["cmake", "--build", ".", *build_args], cwd=build_temp, check=True
        )


setup(
    packages=find_packages(exclude=["scripts"]),
    ext_modules=[CMakeExtension(name=PACKAGE_NAME)],
    cmdclass={'build_ext': CMakeBuild}
)

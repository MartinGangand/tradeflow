from setuptools import Extension, setup, find_packages
from setuptools.command.build_ext import build_ext as build_ext_orig


class CTypesExtension(Extension):
    pass

# class build_ext(build_ext_orig):
    # def build_extension(self, ext):
    #     self._ctypes = isinstance(ext, CTypesExtension)
    #     return super().build_extension(ext)
#
#     def get_export_symbols(self, ext):
#         if self._ctypes:
#             return ext.export_symbols
#         return super().get_export_symbols(ext)
#
#     def get_ext_filename(self, ext_name):
#         if self._ctypes:
#             return ext_name + ".so"
#         return super().get_ext_filename(ext_name)

# class new_build_ext(build_ext_orig):
#     def build_extension(self, ext):
#         ext.extra_c_compile_args += std_c_flags(self)
#         ext.extra_cxx_compile_args += std_cxx_flags(self)
#         build_ext_orig.build_extension(self, ext)


setup(
    packages=find_packages(),
    install_requires=[
           "matplotlib>=3.0.0",
           "numpy>=1.21.0, < 2.0.0",
           "pandas>=2.2.2",
           "statsmodels>=0.12.2",
           "pytest>=8.2.2"
    ],
    py_modules=["tradeflow.ar_model"],
    ext_modules=[
        CTypesExtension(
            name="tradeflow.simulate",
            sources=["tradeflow/simulate.cpp"],
            extra_compile_args=["-std=c++17"],
            language="c++"
        )
    ],
    cmdclass={'build_ext': build_ext_orig}
)

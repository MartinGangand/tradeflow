"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import pathlib

from setuptools import setup, find_packages

import versioneer

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="tradeflow",
    description="A package to simulate autocorrelated time series of signs",  # Optional
    packages=find_packages(),  # Required,
    # version=versioneer.get_version(),
    version="0.0.3",
    # cmdclass=versioneer.get_cmdclass(),
)

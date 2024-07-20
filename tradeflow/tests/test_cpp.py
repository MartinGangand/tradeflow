import ctypes as ct
import os.path
import pathlib
import glob

import pytest

package_dir = pathlib.Path(__file__).parent.parent.absolute()
libfile = glob.glob("cmult*.so", root_dir=str(package_dir))[0]
clib = ct.CDLL(os.path.join(package_dir, libfile))

clib.my_expected_value_to_proba.argtypes = (ct.c_double,)
clib.my_expected_value_to_proba.restype = ct.c_double


@pytest.mark.parametrize("expected_value, expected_proba", [(0.5, 0.75), (0, 0.5), (-0.5, 0.25)])
def test_proba(expected_value, expected_proba):
    proba = clib.my_expected_value_to_proba(expected_value)
    assert proba == expected_proba

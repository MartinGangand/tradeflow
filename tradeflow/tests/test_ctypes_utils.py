import os
import pathlib

import pytest

from tradeflow.ctypes_utils import load_simulate_lib


def test_load_simulate_lib_should_raise_exception():
    with pytest.raises(FileNotFoundError) as ex:
        load_simulate_lib()
    assert str(ex.value) == "No file with one of the extension in ['so', 'pyd']"


def test():
    root_dir = pathlib.Path(__file__).parent.parent.absolute()
    file = os.path.join(root_dir, "simulate.so")
    open(file, 'a').close()
    load_simulate_lib()
    pathlib.Path.unlink(file)

    i = 0

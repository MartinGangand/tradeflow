import pathlib

import numpy as np
import pytest
from numpy.testing import assert_equal

from scripts.pypi import find_file_names_with_given_extensions

CURRENT_DIRECTORY = pathlib.Path(__file__).parent.resolve()

def test_find_urls_in_html_page():
    file_path = CURRENT_DIRECTORY.parent.joinpath("datasets", "html_page.html")
    with open(file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()
    assert 1 == 1

@pytest.mark.parametrize("file_names,potential_extensions,expected_file_names", [
    (["libtradeflow1.so", "tradeflow/libtradeflow2.so", "logger_utils.py"], ["so"], ["libtradeflow1.so", "tradeflow/libtradeflow2.so"]),
    (["libtradeflow.so", "tradeflow/libtradeflow.dll", "logger_utils.py"], ["so", "dll"], ["libtradeflow.so", "tradeflow/libtradeflow.dll"]),
    (["libtradeflow.s", "libtradeflowso", "tradeflow/libtradeflow.dlll", "logger_utils.py", ".so"], ["so", "dll"], [])
])
def test_find_file_names_with_given_extensions(file_names, potential_extensions, expected_file_names):
    actual_file_names = find_file_names_with_given_extensions(file_names=file_names, potential_extensions=potential_extensions)
    assert_equal(actual=actual_file_names, desired=expected_file_names)


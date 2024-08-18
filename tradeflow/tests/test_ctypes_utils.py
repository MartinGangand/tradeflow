import os
import pathlib
import re
from pathlib import Path
import shutil
from typing import List

import pytest

from tradeflow.ctypes_utils import get_shared_library_file

TEMP_FOLDER = str(pathlib.Path(__file__).parent.joinpath("temp").resolve())


@pytest.fixture(autouse=True)
def my_setup_and_tear_down():
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(name=TEMP_FOLDER)

    yield

    shutil.rmtree(path=TEMP_FOLDER)


def save_empty_files(file_names: List[str]) -> None:
    for file_name in file_names:
        file = os.path.join(TEMP_FOLDER, file_name)
        open(file, 'w').close()


@pytest.mark.parametrize("files_to_save,lib_name,expected_shared_library_rel", [
    (["lib1.x-3-x.so"], "lib1", "lib1.x-3-x.so"),
    (["lib1.x-3-x.so", "lib1.py", "lib1.x-3-x.py"], "lib1", "lib1.x-3-x.so"),
    (["lib1.x-3-x.so", "lib.so", "lib12.so", "lib.x-3-x.so", "lib12.x-3-x.so"], "lib1", "lib1.x-3-x.so")
])
def test_get_shared_library_file(files_to_save, lib_name, expected_shared_library_rel):
    save_empty_files(file_names=files_to_save)
    shared_library_abs = get_shared_library_file(directory=TEMP_FOLDER, lib_name=lib_name)
    shared_library_rel = Path(shared_library_abs).relative_to(TEMP_FOLDER)
    assert str(shared_library_rel) == expected_shared_library_rel


def test_get_shared_library_file_should_raise_exception_when_no_shared_library():
    with pytest.raises(FileNotFoundError) as ex:
        get_shared_library_file(directory=TEMP_FOLDER, lib_name="lib1")

    pattern = fr"No shared libray file for library lib1 with one of the extension in \['so', 'pyd', 'dll'\] in directory .*$"
    assert re.match(pattern, str(ex.value))


@pytest.mark.parametrize("files_to_save,lib_name,expected_matched_files", [
    (["lib1.x-3-x.so", "lib1.x-3-x.pyd", "lib1.dll"], "lib1", ["lib1.x-3-x.so", "lib1.x-3-x.pyd", "lib1.dll"]),
    (["lib1.x-3-x.so", "lib1.so", "lib1.dll", "lib1.py"], "lib1", ["lib1.so", "lib1.x-3-x.so", "lib1.dll"]),
])
def test_get_shared_library_file_should_raise_exception_when_several_shared_library(files_to_save, lib_name, expected_matched_files):
    save_empty_files(file_names=files_to_save)
    with pytest.raises(Exception) as ex:
        get_shared_library_file(directory=TEMP_FOLDER, lib_name="lib1")

    pattern = fr"{len(expected_matched_files)} shared library files for library lib1 with extension in \['so', 'pyd', 'dll'\] have been found: {', '.join(expected_matched_files)} \(directory: .*\)$"
    assert re.match(pattern, str(ex.value))

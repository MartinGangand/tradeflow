import os
import pathlib
import re
import shutil
from pathlib import Path
from typing import List

import pytest

from tradeflow.ctypes_utils import get_shared_library_file, find_files
from tradeflow.exceptions import TooManySharedLibrariesException

TEMP_DIR = pathlib.Path(__file__).parent.joinpath("temp").resolve()


@pytest.fixture(scope="function", autouse=True)
def setup_and_tear_down():
    # Create the temporary directory before running a test
    os.makedirs(name=TEMP_DIR, exist_ok=False)

    yield

    # Delete the temporary directory after running a test
    shutil.rmtree(path=TEMP_DIR)


def prepare_temporary_directory_with_files(file_names: List[str]) -> None:
    for file_name in file_names:
        TEMP_DIR.joinpath(file_name).open(mode="w").close()


@pytest.mark.parametrize("files_to_save,expected_shared_library_rel", [
    (["lib1.x-3-x.so"], "lib1.x-3-x.so"),
    (["lib1.x-3-x.so", "lib1.py", "lib1.x-3-x.py"], "lib1.x-3-x.so"),
    (["lib1.x-3-x.so", "lib.so", "lib12.so", "lib.x-3-x.so", "lib12.x-3-x.so"], "lib1.x-3-x.so")
])
def test_get_shared_library_file(files_to_save, expected_shared_library_rel):
    prepare_temporary_directory_with_files(file_names=files_to_save)

    shared_library_abs = get_shared_library_file(directory=TEMP_DIR, shared_library_name="lib1")
    shared_library_rel = Path(shared_library_abs).relative_to(TEMP_DIR)
    assert str(shared_library_rel) == expected_shared_library_rel


@pytest.mark.parametrize("files_to_save", [
    ["lib1.py", "lib1.x-3-x.py"],
    ["lib.so", "lib11.dll", "lib111.dylib", "lib1111.pyd"],
    ["lib1.dl", "lib1.dlll"],
    ["lib1.oso"]])
def test_get_shared_library_file_should_raise_exception_when_no_shared_library(files_to_save):
    prepare_temporary_directory_with_files(file_names=files_to_save)

    with pytest.raises(FileNotFoundError) as ex:
        get_shared_library_file(directory=TEMP_DIR, shared_library_name="lib1")

    pattern = fr"No shared library found for name 'lib1' with one of the extension in \['so', 'dll', 'dylib'\] in directory .*{re.escape(os.path.join('tradeflow', 'tests', 'temp'))}.$"
    assert re.match(pattern, str(ex.value))


@pytest.mark.parametrize("files_to_save,expected_found_shared_libraries", [
    (["lib1.x-3-x.so", "lib1.dll", "lib1.x-3-x.dylib"], ["lib1.x-3-x.so", "lib1.dll", "lib1.x-3-x.dylib"]),
    (["lib1.so", "lib1.x-3-x.so", "lib1.dll", "lib1.py"], ["lib1.so", "lib1.x-3-x.so", "lib1.dll"])
])
def test_get_shared_library_file_should_raise_exception_when_several_shared_libraries(files_to_save, expected_found_shared_libraries):
    prepare_temporary_directory_with_files(file_names=files_to_save)

    with pytest.raises(TooManySharedLibrariesException) as ex:
        get_shared_library_file(directory=TEMP_DIR, shared_library_name="lib1")

    pattern = fr"{len(expected_found_shared_libraries)} shared libraries found with name 'lib1' with extension in \['so', 'dll', 'dylib'\] have been found: {', '.join(expected_found_shared_libraries)} in directory: .*{re.escape(os.path.join('tradeflow', 'tests', 'temp'))}.$"
    assert re.match(pattern, str(ex.value))


@pytest.mark.parametrize("pattern,expected_matched_files", [
    ("file1.txt", ["file1.txt"]),
    ("file1*.txt", ["file1.txt"]),
    ("*.txt", ["file1.txt"]),
    ("file*.py", ["file2.py"]),
    ("*.so", ["file3.so", "file4.x-3.x.so", "file5.so"]),
    ("file4.*.so", ["file4.x-3.x.so"]),
    ("file*.*.so", ["file4.x-3.x.so"]),
    ("*.dlll", []),
    ("*.dl", []),
    ("*", ["file1.txt", "file2.py", "file3.so", "file3.dll", "file3.dylib", "file3.pyd", "file4.x-3.x.so", "file5.so"])
])
def test_find_files(pattern, expected_matched_files):
    files_to_save = ["file1.txt", "file2.py", "file3.so", "file3.dll", "file3.dylib", "file3.pyd", "file4.x-3.x.so", "file5.so"]
    prepare_temporary_directory_with_files(file_names=files_to_save)

    matched_files = find_files(pattern=pattern, directory=TEMP_DIR)
    assert set(matched_files) == set(expected_matched_files)

import os
import pathlib
import re
import shutil
from pathlib import Path
from typing import List

import pytest

from tradeflow.ctypes_utils import get_shared_library_file

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


@pytest.mark.parametrize("files_to_save,shared_library_extension", [
    (["lib1.so"], "so"),
    (["lib1.dylib", "lib1.so", "lib1.py"], "dylib"),
    (["lib1.dll", "lib2.dll", "lib12.dll"], "dll")
])
def test_get_shared_library_file(files_to_save, shared_library_extension):
    prepare_temporary_directory_with_files(file_names=files_to_save)

    shared_library_abs = get_shared_library_file(directory=TEMP_DIR, shared_library_name="lib1", shared_library_extension=shared_library_extension)
    shared_library_rel = Path(shared_library_abs).relative_to(TEMP_DIR)
    assert str(shared_library_rel) == f"lib1.{shared_library_extension}"


@pytest.mark.parametrize("files_to_save,shared_library_extension", [
    (["lib1.py", "lib1.dll"], "so"),
    (["lib.so", "lib11.dll", "lib111.dylib", "lib1111.pyd"], "dylib"),
    (["lib1.dl", "lib1.dlll"], "dll")
])
def test_get_shared_library_file_should_raise_exception_when_no_shared_library(files_to_save, shared_library_extension):
    prepare_temporary_directory_with_files(file_names=files_to_save)

    with pytest.raises(FileNotFoundError) as ex:
        get_shared_library_file(directory=TEMP_DIR, shared_library_name="lib1", shared_library_extension=shared_library_extension)

    pattern = fr"No shared library found for name 'lib1' with extension '{shared_library_extension}' in directory .*{re.escape(os.path.join('tradeflow', 'tests', 'temp'))}.$"
    assert re.match(pattern, str(ex.value))

from pathlib import Path
from unittest.mock import call

import pytest

from scripts.check_package_installation_and_usage import main


class TestMain:

    INDEX = "index"
    PACKAGE_NAME = "package"
    PACKAGE_VERSION = "1.1.6"
    MAIN_PACKAGE_DIRECTORY = Path("dev").joinpath("package").joinpath("main_package_directory")

    @pytest.fixture(scope="function", autouse=True)
    def mock_dependencies(self, mocker):
        self.mock_sys_path = mocker.patch("sys.path")
        self.mock_install = mocker.patch("scripts.utils.install_package_with_pip")
        self.mock_assert_not_importable = mocker.patch("scripts.utils.assert_package_not_importable")
        self.mock_uninstall = mocker.patch("scripts.utils.uninstall_package_with_pip")

    @pytest.mark.parametrize("install_default_version", [False, True])
    def test_main_valid(self, mocker, install_default_version):
        mocker.patch("importlib.metadata.version", return_value=self.PACKAGE_VERSION)

        func_1 = mocker.Mock()
        func_2 = mocker.Mock()
        main(index=self.INDEX, package_name=self.PACKAGE_NAME, package_version=self.PACKAGE_VERSION, install_default_version=install_default_version, local_package_directory=self.MAIN_PACKAGE_DIRECTORY, func_list=[func_1, func_2])

        self.mock_sys_path.remove.assert_called_once_with(str(self.MAIN_PACKAGE_DIRECTORY.parent))
        self.mock_assert_not_importable.assert_called_once_with(package_name=self.PACKAGE_NAME)

        # Check that the package is installed with the correct parameters
        package_version = None if install_default_version else self.PACKAGE_VERSION
        self.mock_install.assert_called_once_with(package_name=self.PACKAGE_NAME, index=self.INDEX, package_version=package_version)

        # Check that the functions in func_list are called
        func_1.assert_called_once_with()
        func_2.assert_called_once_with()

        # mock_uninstall is called twice: once before installation and once after uninstallation of the package
        assert self.mock_uninstall.call_count == 2
        self.mock_uninstall.assert_has_calls([call(package_name=self.PACKAGE_NAME), call(package_name=self.PACKAGE_NAME)])

    @pytest.mark.parametrize("install_default_version", [False, True])
    def test_main_should_raise_exception_when_incorrect_installed_version(self, mocker, install_default_version):
        mocker.patch("importlib.metadata.version", return_value="1.0.0")

        func_1 = mocker.Mock()
        func_2 = mocker.Mock()

        with pytest.raises(Exception) as ex:
            main(index=self.INDEX, package_name=self.PACKAGE_NAME, package_version=self.PACKAGE_VERSION, install_default_version=install_default_version, local_package_directory=self.MAIN_PACKAGE_DIRECTORY, func_list=[func_1, func_2])

        assert str(ex.value) == f"Installed version '1.0.0' of package '{self.PACKAGE_NAME}' does not match expected version '{self.PACKAGE_VERSION}'."

        self.mock_sys_path.remove.assert_called_once_with(str(self.MAIN_PACKAGE_DIRECTORY.parent))
        self.mock_assert_not_importable.assert_called_once_with(package_name=self.PACKAGE_NAME)

        # Check that the package is installed with the correct parameters
        version = None if install_default_version else self.PACKAGE_VERSION
        self.mock_install.assert_called_once_with(package_name=self.PACKAGE_NAME, index=self.INDEX, package_version=version)

        # Check that the functions in func_list are not called
        func_1.assert_not_called()
        func_2.assert_not_called()

        # mock_uninstall is called twice: once before installation and once after uninstallation of the package
        assert self.mock_uninstall.call_count == 2
        self.mock_uninstall.assert_has_calls([call(package_name=self.PACKAGE_NAME), call(package_name=self.PACKAGE_NAME)])

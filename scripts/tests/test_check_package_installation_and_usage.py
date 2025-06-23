import pytest
from unittest.mock import call, Mock

from scripts.check_package_installation_and_usage import uninstall_package_with_pip, parse_command_line, \
    install_package_with_pip, INDEX_URL_TEST_PYPI, config


class TestUninstallPackageWithPip:

    def test_uninstall_package_with_pip(self, mocker):
        mocker.patch("sys.executable", new="python")
        mock_check_call = mocker.patch("subprocess.check_call")

        uninstall_package_with_pip("test_package")

        mock_check_call.assert_called_once_with(["python", "-m", "pip", "uninstall", "-y", "test_package"])


class TestParseCommandLine:

    def test_parse_command_line(self):
        actual = parse_command_line(command_line="python -m pip install package_name==1.0.0")
        assert actual == ["python", "-m", "pip", "install", "package_name==1.0.0"]


class TestInstallPackageWithPip:

    # @pytest.mark.parametrize("index", ["pypi", "test.pypi"])
    def test_install_package_with_pip(self, mocker):
        mocker.patch("sys.executable", new="python")
        mock_check_call = mocker.patch("subprocess.check_call")

        install_package_with_pip(index="pypi", package_name="test_package", version="1.0.0")

        mock_check_call.assert_called_once_with(["python", "-m", "pip", "install", "--no-cache-dir", "test_package==1.0.0"])

    def test_install_package_with_pip_with_test_pypi(self, mocker):
        mocker.patch("sys.executable", new="python")
        # mocker.patch("scripts.config.ROOT_REPOSITORY", new="python")
        mock_check_call = mocker.patch("subprocess.check_call")

        install_package_with_pip(index="test.pypi", package_name="test_package", version="1.0.0")

        assert mock_check_call.call_count == 2
        c1 = ["python", "-m", "pip", "install", "-r", str(config.ROOT_REPOSITORY.joinpath("requirements.txt"))]
        c2 = ["python", "-m", "pip", "install", "--index-url", f"{INDEX_URL_TEST_PYPI}", "--no-deps", "--no-cache-dir", "test_package==1.0.0"]
        mock_check_call.assert_has_calls([call(c1), call(c2)])
        # mock_check_call.assert_called_once_with(["python", "-m", "pip", "install", "--index-url", f"{INDEX_URL_TEST_PYPI}", "--no-deps", "--no-cache-dir", "test_package==1.0.0"])


def test_install_package_with_pip_test_pypi(mocker):
    package_name = "dummy_package"
    version = "1.2.3"
    version_part = f"=={version}"
    requirements_file = "/fake/root/requirements.txt"
    index = "test.pypi"

    # Mock config.ROOT_REPOSITORY.joinpath().is_file() and __str__()
    mock_root = mocker.Mock()
    mock_requirements = mocker.Mock()
    mock_requirements.is_file.return_value = True
    # mocker.patch.object(mock_requirements, "__str__", lambda self=mock_requirements: requirements_file)
    mock_requirements.__str__ = lambda self=mock_requirements: requirements_file
    mock_root.joinpath.return_value = mock_requirements
    mocker.patch("scripts.check_package_installation_and_usage.config.ROOT_REPOSITORY", new=mock_root)

    # Mock sys.executable
    mocker.patch("sys.executable", new="python")

    # Mock subprocess.check_call
    mock_check_call = mocker.patch("subprocess.check_call")

    install_package_with_pip(index, package_name, version)

    c1 = ["python", "-m", "pip", "install", "-r", requirements_file]
    c2 = [
        "python", "-m", "pip", "install",
        "--index-url", f"{INDEX_URL_TEST_PYPI}",
        "--no-deps", "--no-cache-dir", f"{package_name}{version_part}"
    ]
    mock_check_call.assert_has_calls([mocker.call(c1), mocker.call(c2)])
    assert mock_check_call.call_count == 2
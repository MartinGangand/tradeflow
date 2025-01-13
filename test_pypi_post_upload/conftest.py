def pytest_addoption(parser):
    parser.addoption(
        "--index", action="store", default="pypi", choices=("pypi", "test.pypi"), help="Specify the package index on which to validate the package. Use 'pypi' for the main Python Package Index or 'test.pypi' for the testing instance",
    )

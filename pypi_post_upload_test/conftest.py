def pytest_addoption(parser):
    parser.addoption(
        "--index",
        action="store",
        default="pypi",
        choices=("pypi", "test.pypi"),
        help="Specify the package index from which to install the package. Use 'pypi' for the main Python Package Index or 'test.pypi' for the testing instance."
    )

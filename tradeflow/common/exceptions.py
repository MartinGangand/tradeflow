class EnumValueException(Exception):
    """Raised when the enum value is not valid"""
    pass


class UnsupportedOsException(Exception):
    """Raised if the OS is not supported when loading a shared library"""
    pass

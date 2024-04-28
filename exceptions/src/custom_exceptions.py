class EnumValueException(Exception):
    "Raised when the enum value is not valid"
    pass

class IllegalValueException(Exception):
    "Raised when a value is not in a valid state"
    pass

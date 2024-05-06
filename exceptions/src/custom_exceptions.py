class EnumValueException(Exception):
    "Raised when the enum value is not valid"
    pass

class IllegalValueException(Exception):
    "Raised when a value is not in a valid state"
    pass

class ModelNotFittedException(Exception):
    "Raised when the model need the parameters but it has not been fitted"
    pass

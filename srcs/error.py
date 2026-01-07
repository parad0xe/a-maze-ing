from enum import IntEnum


class Err(IntEnum):
    NO_ERROR = 0
    INPUT_ERROR = 1
    PARSE_ERROR = 2


class ParseError(Exception):
    pass


class SetterError(Exception):
    pass

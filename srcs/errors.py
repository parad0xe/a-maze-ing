from enum import IntEnum


class ParseError(Exception):
    pass


class ExitCode(IntEnum):
    VALIDATION_ERROR = 1
    FILE_ERROR = 2
    ARGUMENTS_ERROR = 3
    UNEXPECTED_ERROR = 4

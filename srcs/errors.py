from enum import IntEnum


class ParseError(Exception):
    """
    This exception signals a configuration parsing failure.
    """
    pass


class ExitCode(IntEnum):
    """
    This enum defines process exit codes for common failure cases.

    Attributes:
        VALIDATION_ERROR (int): Validation failed for the loaded configuration.
        FILE_ERROR (int): File IO or encoding error occurred during export.
        ARGUMENTS_ERROR (int): Invalid or missing command line arguments.
        UNEXPECTED_ERROR (int): Any other unhandled error occurred.
    """
    VALIDATION_ERROR = 1
    FILE_ERROR = 2
    ARGUMENTS_ERROR = 3
    UNEXPECTED_ERROR = 4

"""
Custom exceptions for the application
"""


class SchedulingException(Exception):
    """Base exception for scheduling errors"""
    pass


class InvalidInputException(SchedulingException):
    """Raised when input validation fails"""
    pass


class AlgorithmExecutionException(SchedulingException):
    """Raised when algorithm execution fails"""
    pass


class FileHandlingException(SchedulingException):
    """Raised when file I/O operations fail"""
    pass


class TimeoutException(SchedulingException):
    """Raised when algorithm execution times out"""
    pass

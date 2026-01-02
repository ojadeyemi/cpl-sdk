"""Exceptions for the CPL SDK."""


class CPLSDKError(Exception):
    """Base exception for CPL SDK errors."""

    pass


class RequestError(CPLSDKError):
    """Exception raised when an HTTP request fails."""

    pass


class APITimeoutError(CPLSDKError):
    """Exception raised when an API request times out."""

    pass

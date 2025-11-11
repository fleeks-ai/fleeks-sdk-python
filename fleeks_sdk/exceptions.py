"""
Exceptions for the Fleeks SDK.
"""

from typing import Optional, Any
import httpx


class FleeksException(Exception):
    """Base exception for Fleeks SDK."""
    pass


class FleeksAPIError(FleeksException):
    """Exception raised for API errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class FleeksRateLimitError(FleeksAPIError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str, 
        retry_after: int = 60,
        status_code: int = 429,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class FleeksAuthenticationError(FleeksAPIError):
    """Exception raised for authentication errors."""
    
    def __init__(
        self, 
        message: str = "Authentication failed. Check your API key.",
        status_code: int = 401,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message, status_code, response)


class FleeksPermissionError(FleeksAPIError):
    """Exception raised for permission/authorization errors."""
    
    def __init__(
        self, 
        message: str = "Permission denied. Check your API key scopes.",
        status_code: int = 403,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message, status_code, response)


class FleeksResourceNotFoundError(FleeksAPIError):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self, 
        message: str = "Resource not found.",
        status_code: int = 404,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message, status_code, response)


class FleeksValidationError(FleeksAPIError):
    """Exception raised for validation errors."""
    
    def __init__(
        self, 
        message: str = "Validation error.",
        status_code: int = 422,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message, status_code, response)


class FleeksConnectionError(FleeksException):
    """Exception raised for connection errors."""
    pass


class FleeksStreamingError(FleeksException):
    """Exception raised for streaming-related errors."""
    pass


class FleeksTimeoutError(FleeksException):
    """Exception raised for timeout errors."""
    pass
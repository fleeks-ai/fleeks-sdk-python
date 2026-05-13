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


class FleeksFeatureUnsupportedError(FleeksAPIError):
    """
    Raised when the connected backend does not support a feature this SDK
    method requires (e.g. dashboards/messages on a backend older than the
    2026-04-28 always-on agent dashboards release).

    Detected when the backend returns 404 / 405 / 501 for a known endpoint
    path that newer backends serve.
    """

    def __init__(
        self,
        message: str = (
            "This Fleeks backend does not support the requested feature. "
            "Upgrade the backend (minimum 2026-04-28 always-on dashboards "
            "release) or pin an older SDK version."
        ),
        status_code: Optional[int] = None,
        response: Optional[httpx.Response] = None,
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


class WorkspaceNotReadyError(FleeksAPIError):
    """
    Raised when an operation requires a running workspace container but none
    is available (HTTP 409 with error_code='container_not_running').

    Attributes:
        ready_for_preview: Always False when raised.
        remediation: List of suggested remediation steps from the backend.
        project_id: Project ID that triggered the error.
    """

    def __init__(
        self,
        message: str = "Workspace exists but no running container is available. Start the workspace container first.",
        status_code: int = 409,
        response: Optional[Any] = None,
        project_id: Optional[int] = None,
        remediation: Optional[list] = None,
    ):
        super().__init__(message, status_code, response)
        self.ready_for_preview: bool = False
        self.project_id = project_id
        self.remediation: list = remediation or []
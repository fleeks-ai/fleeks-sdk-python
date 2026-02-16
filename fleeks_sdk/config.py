"""
Configuration for the Fleeks SDK.
"""

import os
from typing import Optional
from .exceptions import FleeksException


class Config:
    """Configuration settings for the Fleeks SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        version: str = "0.1.0",
        **kwargs
    ):
        """
        Initialize configuration.

        Args:
            api_key: Fleeks API key (defaults to FLEEKS_API_KEY env var)
            base_url: Base URL for the API (defaults to FLEEKS_BASE_URL env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            version: SDK version
        """
        self.api_key = api_key or os.getenv('FLEEKS_API_KEY')
        self.base_url = base_url or os.getenv('FLEEKS_BASE_URL', 'https://api.fleeks.ai')
        self.timeout = timeout
        self.max_retries = max_retries
        self.version = version

        # Socket.IO configuration
        self.socketio_path = kwargs.get('socketio_path', '/socket.io')
        self.socketio_namespace = kwargs.get('socketio_namespace', '/')
        
        # Streaming configuration
        self.auto_reconnect = kwargs.get('auto_reconnect', True)
        self.reconnect_attempts = kwargs.get('reconnect_attempts', 5)
        self.reconnect_delay = kwargs.get('reconnect_delay', 1.0)
        
        # Rate limiting configuration
        self.respect_rate_limits = kwargs.get('respect_rate_limits', True)
        self.rate_limit_buffer = kwargs.get('rate_limit_buffer', 0.1)  # 10% buffer

    def validate(self) -> None:
        """Validate the configuration."""
        if not self.api_key:
            raise FleeksException(
                "API key is required. Set FLEEKS_API_KEY environment variable "
                "or pass api_key parameter."
            )

        if not self.base_url:
            raise FleeksException("Base URL is required.")

        if self.timeout <= 0:
            raise FleeksException("Timeout must be positive.")

        if self.max_retries < 0:
            raise FleeksException("Max retries must be non-negative.")

    @property
    def socketio_url(self) -> str:
        """Get the full Socket.IO URL."""
        return f"{self.base_url.rstrip('/')}{self.socketio_path}"

    def __repr__(self) -> str:
        # Don't expose the full API key in repr
        masked_key = f"{self.api_key[:8]}..." if self.api_key else "None"
        return (
            f"Config(api_key='{masked_key}', base_url='{self.base_url}', "
            f"timeout={self.timeout}, max_retries={self.max_retries})"
        )
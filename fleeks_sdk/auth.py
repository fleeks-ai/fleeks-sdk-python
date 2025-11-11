"""
Authentication handling for the Fleeks SDK.
"""

from typing import Optional, Dict, Any
import hashlib
import hmac
import time
from .exceptions import FleeksAuthenticationError


class APIKeyAuth:
    """API Key authentication handler."""
    
    def __init__(self, api_key: str):
        """
        Initialize API key authentication.
        
        Args:
            api_key: The API key for authentication
        """
        self.api_key = api_key
        self._validate_api_key()
    
    def _validate_api_key(self) -> None:
        """Validate the API key format."""
        if not self.api_key:
            raise FleeksAuthenticationError("API key cannot be empty")
        
        if not self.api_key.startswith('fleeks_'):
            raise FleeksAuthenticationError(
                "Invalid API key format. API keys should start with 'fleeks_'"
            )
        
        if len(self.api_key) < 32:
            raise FleeksAuthenticationError(
                "API key appears to be too short. Please check your API key."
            )
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of headers needed for authentication
        """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'X-API-Key': self.api_key
        }
    
    def sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """
        Sign a request for enhanced security (if needed in the future).
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body
            
        Returns:
            Dictionary containing signature headers
        """
        timestamp = str(int(time.time()))
        
        # Create signature string
        string_to_sign = f"{method}\n{path}\n{timestamp}\n{body}"
        
        # Create HMAC signature (using API key as secret)
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Timestamp': timestamp,
            'X-Signature': signature
        }
    
    def __repr__(self) -> str:
        # Don't expose the full API key
        masked_key = f"{self.api_key[:12]}..." if self.api_key else "None"
        return f"APIKeyAuth(api_key='{masked_key}')"
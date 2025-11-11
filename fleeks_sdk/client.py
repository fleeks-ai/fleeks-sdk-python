"""
Async client for the Fleeks SDK.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List, Union, AsyncContextManager
from contextlib import asynccontextmanager

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

from .config import Config
from .exceptions import FleeksAPIError, FleeksException, FleeksRateLimitError
from .auth import APIKeyAuth
from .workspaces import WorkspaceManager
from .agents import AgentManager
from .files import FileManager
from .terminal import TerminalManager
from .containers import ContainerManager
from .streaming import StreamingClient


class FleeksClient:
    """
    Async client for interacting with the Fleeks API.
    
    Features:
    - Full async/await support with httpx
    - Automatic retry with exponential backoff
    - Rate limiting awareness
    - Socket.IO streaming support
    - Comprehensive error handling
    - Type hints throughout
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[Config] = None,
        **kwargs
    ):
        """
        Initialize the Fleeks client.

        Args:
            api_key: Your Fleeks API key (can also be set via FLEEKS_API_KEY env var)
            config: Configuration object
            **kwargs: Additional config options (base_url, timeout, retries)
        """
        if config is None:
            config = Config(api_key=api_key, **kwargs)

        config.validate()

        self.config = config
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip('/')

        # Initialize HTTP client
        self._client: Optional[httpx.AsyncClient] = None
        
        # Initialize auth handler
        self.auth = APIKeyAuth(self.api_key)
        
        # Initialize service managers (lazy loaded)
        self._workspaces: Optional[WorkspaceManager] = None
        self._agents: Optional[AgentManager] = None
        self._files: Optional[FileManager] = None
        self._terminal: Optional[TerminalManager] = None
        self._containers: Optional[ContainerManager] = None
        self._streaming: Optional[StreamingClient] = None

    async def __aenter__(self) -> "FleeksClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    'X-API-Key': self.api_key,  # Backend expects X-API-Key header, not Bearer
                    'Content-Type': 'application/json',
                    'User-Agent': f'fleeks-python-sdk/{self.config.version}',
                    'Accept': 'application/json'
                },
                follow_redirects=True
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Fleeks API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            FleeksAPIError: For API-specific errors
            FleeksRateLimitError: For rate limit exceeded
            FleeksException: For general errors
        """
        await self._ensure_client()
        
        url = f"/api/v1/sdk/{endpoint.lstrip('/')}"
        
        try:
            response = await self._client.request(method, url, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                raise FleeksRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    retry_after=int(retry_after)
                )
            
            response.raise_for_status()
            
            # Handle different content types
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return {'data': response.text, 'content_type': content_type}
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get('detail', str(e))
            except:
                error_detail = str(e)
            
            raise FleeksAPIError(
                f"API request failed ({e.response.status_code}): {error_detail}",
                status_code=e.response.status_code,
                response=e.response
            )
        except httpx.RequestError as e:
            raise FleeksException(f"Request failed: {str(e)}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request('GET', endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        kwargs = {}
        if json is not None:
            kwargs['json'] = json
        elif data is not None:
            kwargs['data'] = data
        if files is not None:
            kwargs['files'] = files
        return await self._make_request('POST', endpoint, **kwargs)

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        kwargs = {}
        if json is not None:
            kwargs['json'] = json
        elif data is not None:
            kwargs['data'] = data
        return await self._make_request('PUT', endpoint, **kwargs)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request('DELETE', endpoint)

    async def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        await self._ensure_client()
        response = await self._client.get('/health')
        response.raise_for_status()
        return response.json()

    # Property accessors for service managers (lazy loading)
    
    @property
    def workspaces(self) -> WorkspaceManager:
        """Access workspace management operations."""
        if self._workspaces is None:
            self._workspaces = WorkspaceManager(self)
        return self._workspaces

    @property
    def agents(self) -> AgentManager:
        """Access agent management operations."""
        if self._agents is None:
            self._agents = AgentManager(self)
        return self._agents

    @property
    def files(self) -> FileManager:
        """Access file management operations."""
        if self._files is None:
            self._files = FileManager(self)
        return self._files

    @property
    def terminal(self) -> TerminalManager:
        """Access terminal operations."""
        if self._terminal is None:
            self._terminal = TerminalManager(self)
        return self._terminal

    @property
    def containers(self) -> ContainerManager:
        """Access container management operations."""
        if self._containers is None:
            self._containers = ContainerManager(self)
        return self._containers

    @property
    def streaming(self) -> StreamingClient:
        """Access real-time streaming operations."""
        if self._streaming is None:
            self._streaming = StreamingClient(self)
        return self._streaming

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            
        # Close streaming connection if open
        if self._streaming is not None:
            await self._streaming.disconnect()

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics and rate limits."""
        return await self.get('/usage/stats')

    async def get_api_key_info(self) -> Dict[str, Any]:
        """Get information about the current API key."""
        return await self.get('/auth/key-info')


# Convenience function for quick usage
@asynccontextmanager
async def create_client(
    api_key: Optional[str] = None,
    **kwargs
) -> AsyncContextManager[FleeksClient]:
    """
    Create and manage a Fleeks client with automatic cleanup.
    
    Usage:
        async with create_client() as client:
            workspaces = await client.workspaces.list()
    """
    client = FleeksClient(api_key=api_key, **kwargs)
    try:
        yield client
    finally:
        await client.close()
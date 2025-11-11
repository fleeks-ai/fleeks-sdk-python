"""
Fleeks Python SDK

A comprehensive async Python SDK for interacting with Fleeks services.

Features:
- Full async/await support
- Socket.IO real-time streaming
- Comprehensive workspace management
- Agent orchestration
- File operations
- Terminal control
- Container management
- Automatic retry and rate limiting
- Type hints throughout
"""

__version__ = "0.1.0"
__author__ = "Fleeks Inc"
__email__ = "support@fleeks.com"

# Core client and utilities
from .client import FleeksClient, create_client
from .config import Config
from .auth import APIKeyAuth

# Service managers
from .workspaces import WorkspaceManager, WorkspaceConfig, WorkspaceInfo
from .agents import AgentManager, AgentConfig, AgentInfo, AgentRole, AgentStatus, AgentHandoffRequest
from .files import FileManager, FileInfo, FileUploadConfig, FileSearchOptions
from .terminal import TerminalManager, TerminalConfig, TerminalSession, TerminalExecutionResult
from .containers import ContainerManager, ContainerInfo, ContainerStats, ContainerExecResult
from .streaming import StreamingClient

# Exceptions
from .exceptions import (
    FleeksException,
    FleeksAPIError,
    FleeksRateLimitError,
    FleeksAuthenticationError,
    FleeksPermissionError,
    FleeksResourceNotFoundError,
    FleeksValidationError,
    FleeksConnectionError,
    FleeksStreamingError,
    FleeksTimeoutError
)

__all__ = [
    # Core
    "FleeksClient",
    "create_client",
    "Config",
    "APIKeyAuth",
    
    # Service managers
    "WorkspaceManager",
    "AgentManager", 
    "FileManager",
    "TerminalManager",
    "ContainerManager",
    "StreamingClient",
    
    # Data models
    "WorkspaceConfig",
    "WorkspaceInfo",
    "AgentConfig",
    "AgentInfo",
    "AgentRole",
    "AgentStatus",
    "AgentHandoffRequest",
    "FileInfo",
    "FileUploadConfig", 
    "FileSearchOptions",
    "TerminalConfig",
    "TerminalSession",
    "TerminalExecutionResult",
    "ContainerInfo",
    "ContainerStats",
    "ContainerExecResult",
    
    # Exceptions
    "FleeksException",
    "FleeksAPIError",
    "FleeksRateLimitError",
    "FleeksAuthenticationError",
    "FleeksPermissionError",
    "FleeksResourceNotFoundError",
    "FleeksValidationError",
    "FleeksConnectionError",
    "FleeksStreamingError",
    "FleeksTimeoutError",
]
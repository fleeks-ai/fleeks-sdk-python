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
- Embed management for shareable code environments
- Container lifecycle control (heartbeat, hibernate, keep-alive)
- Automatic retry and rate limiting
- Type hints throughout
"""

__version__ = "0.3.0"
__author__ = "Fleeks Inc"
__email__ = "support@fleeks.com"

# Core client and utilities
from .client import FleeksClient, create_client
from .config import Config
from .auth import APIKeyAuth

# Service managers
from .workspaces import WorkspaceManager
from .agents import AgentManager
from .files import FileManager
from .terminal import TerminalManager
from .containers import ContainerManager
from .streaming import StreamingClient
from .embeds import EmbedManager

# Lifecycle management
from .lifecycle import (
    IdleAction,
    LifecycleState,
    LifecycleConfig,
    HeartbeatResponse,
    TimeoutExtensionResponse,
    KeepAliveResponse,
    HibernationResponse,
    LifecycleStatus,
    TIER_LIMITS
)

# Embed types and models
from .embeds import (
    EmbedTemplate,
    DisplayMode,
    EmbedLayoutPreset,
    EmbedTheme,
    EmbedStatus,
    EmbedSettings,
    EmbedFile,
    EmbedInfo,
    EmbedSession,
    EmbedAnalytics,
    Embed
)

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

# Data models
from .models import (
    WorkspaceInfo,
    PreviewURLInfo,
    AgentType,
    AgentStatus,
    AgentExecution,
    AgentHandoff,
    AgentStatusInfo,
    AgentOutput,
    AgentList
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
    "EmbedManager",
    
    # Lifecycle
    "IdleAction",
    "LifecycleState",
    "LifecycleConfig",
    "HeartbeatResponse",
    "TimeoutExtensionResponse",
    "KeepAliveResponse",
    "HibernationResponse",
    "LifecycleStatus",
    "TIER_LIMITS",
    
    # Embeds
    "EmbedTemplate",
    "DisplayMode",
    "EmbedLayoutPreset",
    "EmbedTheme",
    "EmbedStatus",
    "EmbedSettings",
    "EmbedFile",
    "EmbedInfo",
    "EmbedSession",
    "EmbedAnalytics",
    "Embed",
    
    # Data models
    "WorkspaceInfo",
    "PreviewURLInfo",
    "AgentType",
    "AgentStatus",
    "AgentExecution",
    "AgentHandoff",
    "AgentStatusInfo",
    "AgentOutput",
    "AgentList",
    
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
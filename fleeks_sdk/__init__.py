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

__version__ = "0.5.2"
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
from .deploy import DeployManager
from .schedules import ScheduleManager
from .channels import ChannelManager
from .automations import AutomationManager
from .previews import PreviewManager

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
    AgentStopResponse,
    AgentStatusInfo,
    AgentOutput,
    AgentList,
    SubAgentResult,
    SubAgentUsage,
    DeploymentStatusEnum,
    DeployResponse,
    DeployStatus,
    DeployListItem,
    DeployLogEvent,
    DeployLogs,
    ProvisionDbResult,
    MobileDistributeResult,
    DesktopDistributeResult,
    DiagnoseResult,
    HealthCheckResult,
    RuntimeLogEntry,
    RuntimeLogsResult,
    LatencyMetrics,
    MetricsResult,
    MultiServiceDeployResult,
    MultiDeployResult,
    # Schedule / Always-On
    ScheduleType,
    DaemonStatus,
    ProjectType,
    Schedule,
    ScheduleList,
    ScheduleStartResult,
    DaemonStatusInfo,
    DaemonLogs,
    QuotaMetric,
    QuotaCounter,
    QuotaUsage,
    # Channels
    ChannelType,
    ChannelTypeInfo,
    Channel,
    ChannelList,
    AuthFlowResult,
    # Automations
    TriggerType,
    Automation,
    AutomationList,
    AutomationTestResult,
    # Preview sessions (new — 2026-03-10)
    PreviewStatus,
    PreviewFramework,
    PreviewSession,
    PreviewSessionList,
    PreviewHealth,
    PreviewDetectResult,
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
    "DeployManager",
    "ScheduleManager",
    "ChannelManager",
    "AutomationManager",
    "PreviewManager",
    
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
    "AgentStopResponse",
    "AgentStatusInfo",
    "AgentOutput",
    "AgentList",
    "SubAgentResult",
    "SubAgentUsage",
    "DeploymentStatusEnum",
    "DeployResponse",
    "DeployStatus",
    "DeployListItem",
    "DeployLogEvent",
    "DeployLogs",
    "ProvisionDbResult",
    "MobileDistributeResult",
    "DesktopDistributeResult",
    "DiagnoseResult",
    "HealthCheckResult",
    "RuntimeLogEntry",
    "RuntimeLogsResult",
    "LatencyMetrics",
    "MetricsResult",
    "MultiServiceDeployResult",
    "MultiDeployResult",
    # Schedule / Always-On
    "ScheduleType",
    "DaemonStatus",
    "ProjectType",
    "Schedule",
    "ScheduleList",
    "ScheduleStartResult",
    "DaemonStatusInfo",
    "DaemonLogs",
    "QuotaMetric",
    "QuotaCounter",
    "QuotaUsage",
    # Channels
    "ChannelType",
    "ChannelTypeInfo",
    "Channel",
    "ChannelList",
    "AuthFlowResult",
    # Automations
    "TriggerType",
    "Automation",
    "AutomationList",
    "AutomationTestResult",
    # Preview sessions
    "PreviewStatus",
    "PreviewFramework",
    "PreviewSession",
    "PreviewSessionList",
    "PreviewHealth",
    "PreviewDetectResult",
    
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
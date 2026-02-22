"""
Container lifecycle management for the Fleeks SDK.

Provides fine-grained control over container lifecycle including:
- Idle timeout configuration
- Keep-alive heartbeats
- Hibernation and wake (Pro+ tiers)
- Always-on mode (Enterprise tier)
- Preview-aware lifecycle

Backend endpoints (to be implemented):
- POST /api/v1/sdk/containers/{container_id}/heartbeat
- POST /api/v1/sdk/containers/{container_id}/extend-timeout
- POST /api/v1/sdk/containers/{container_id}/keep-alive
- POST /api/v1/sdk/containers/{container_id}/hibernate
- POST /api/v1/sdk/containers/{container_id}/wake
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class IdleAction(str, Enum):
    """
    Action to take when container becomes idle.
    
    Availability varies by tier:
    - SHUTDOWN: Available on all tiers
    - HIBERNATE: Pro+ tiers only
    - KEEP_ALIVE: Enterprise tier only
    """
    SHUTDOWN = "shutdown"
    """Stop container completely (default). Fast startup on next request."""
    
    HIBERNATE = "hibernate"
    """Pause container preserving state. Very fast resume. Pro+ only."""
    
    KEEP_ALIVE = "keep_alive"
    """Never auto-shutdown. Enterprise only."""


class LifecycleState(str, Enum):
    """Current lifecycle state of a container."""
    RUNNING = "running"
    """Container is running normally."""
    
    HIBERNATING = "hibernating"
    """Container is hibernated (memory preserved)."""
    
    STOPPED = "stopped"
    """Container is stopped (no resources consumed)."""
    
    STARTING = "starting"
    """Container is starting up."""
    
    WAKING = "waking"
    """Container is waking from hibernation."""


@dataclass
class LifecycleConfig:
    """
    Container lifecycle configuration.
    
    Controls how containers behave during idle periods and their maximum
    lifetime. Some features are tier-locked.
    
    Attributes:
        idle_timeout_minutes: Minutes of inactivity before idle_action triggers.
            Default is 30 minutes. Maximum varies by tier.
        max_duration_hours: Maximum container lifetime in hours. None = no limit.
            Enterprise tier only for unlimited.
        idle_action: What to do when container becomes idle.
        auto_wake: Automatically wake hibernated containers on API request.
        keep_alive_on_preview: Keep container alive while preview URL has active
            connections (websocket or HTTP polling).
        heartbeat_interval_seconds: Recommended interval for heartbeat calls
            when running long operations.
    
    Example:
        >>> # Standard config (30min idle, then shutdown)
        >>> config = LifecycleConfig()
        
        >>> # Extended timeout with hibernation (Pro+)
        >>> config = LifecycleConfig(
        ...     idle_timeout_minutes=120,
        ...     idle_action=IdleAction.HIBERNATE,
        ...     keep_alive_on_preview=True
        ... )
        
        >>> # Always-on for production (Enterprise)
        >>> config = LifecycleConfig(
        ...     idle_action=IdleAction.KEEP_ALIVE,
        ...     max_duration_hours=None
        ... )
    """
    
    idle_timeout_minutes: int = 30
    """Minutes of inactivity before action triggers (default: 30)."""
    
    max_duration_hours: Optional[int] = None
    """Maximum container lifetime in hours (None = tier default)."""
    
    idle_action: IdleAction = IdleAction.SHUTDOWN
    """What to do when idle (tier-dependent features)."""
    
    auto_wake: bool = True
    """Auto-wake from hibernation on API request."""
    
    keep_alive_on_preview: bool = False
    """Keep alive while preview URL has active connections."""
    
    heartbeat_interval_seconds: int = 300
    """Recommended heartbeat interval (5 minutes) for long operations."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API request."""
        return {
            'idle_timeout_minutes': self.idle_timeout_minutes,
            'max_duration_hours': self.max_duration_hours,
            'idle_action': self.idle_action.value,
            'auto_wake': self.auto_wake,
            'keep_alive_on_preview': self.keep_alive_on_preview,
            'heartbeat_interval_seconds': self.heartbeat_interval_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LifecycleConfig':
        """Create from API response dict."""
        return cls(
            idle_timeout_minutes=data.get('idle_timeout_minutes', 30),
            max_duration_hours=data.get('max_duration_hours'),
            idle_action=IdleAction(data.get('idle_action', 'shutdown')),
            auto_wake=data.get('auto_wake', True),
            keep_alive_on_preview=data.get('keep_alive_on_preview', False),
            heartbeat_interval_seconds=data.get('heartbeat_interval_seconds', 300)
        )
    
    @classmethod
    def quick_test(cls) -> 'LifecycleConfig':
        """Preset for quick tests (15 min timeout)."""
        return cls(idle_timeout_minutes=15)
    
    @classmethod
    def development(cls) -> 'LifecycleConfig':
        """Preset for development sessions (2 hour timeout, hibernate)."""
        return cls(
            idle_timeout_minutes=120,
            idle_action=IdleAction.HIBERNATE
        )
    
    @classmethod
    def agent_task(cls) -> 'LifecycleConfig':
        """Preset for AI agent single-task execution."""
        return cls(
            idle_timeout_minutes=60,
            max_duration_hours=2
        )
    
    @classmethod
    def always_on(cls) -> 'LifecycleConfig':
        """Preset for always-on services (Enterprise)."""
        return cls(
            idle_action=IdleAction.KEEP_ALIVE,
            max_duration_hours=None,
            keep_alive_on_preview=True
        )


@dataclass
class HeartbeatResponse:
    """
    Response from container heartbeat.
    
    Matches backend: HeartbeatResponse
    
    Attributes:
        container_id: Container ID
        status: Container status (e.g., 'active')
        last_heartbeat: ISO timestamp of this heartbeat
        idle_timeout_seconds: Idle timeout in seconds
        next_timeout_at: Timestamp when container will timeout if no activity
        message: Status message
    """
    container_id: str
    status: str
    last_heartbeat: str
    idle_timeout_seconds: int
    next_timeout_at: str
    message: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeartbeatResponse':
        """Create from API response dict."""
        return cls(
            container_id=data['container_id'],
            status=data.get('status', 'active'),
            last_heartbeat=data['last_heartbeat'],
            idle_timeout_seconds=data.get('idle_timeout_seconds', 1800),
            next_timeout_at=data['next_timeout_at'],
            message=data.get('message', '')
        )


@dataclass
class TimeoutExtensionResponse:
    """
    Response from timeout extension request.
    
    Matches backend: ExtendTimeoutResponse
    
    Attributes:
        container_id: Container ID
        success: Whether extension was successful
        new_timeout_at: New timeout timestamp
        added_minutes: Minutes that were added
        max_allowed_minutes: Maximum minutes allowed for user's tier
        message: Status message
    """
    container_id: str
    success: bool
    new_timeout_at: str
    added_minutes: int
    max_allowed_minutes: int
    message: str
    minutes_extended: int = 0  # Alias returned by backend for SDK compatibility
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeoutExtensionResponse':
        """Create from API response dict."""
        added = data.get('added_minutes', 0)
        return cls(
            container_id=data['container_id'],
            success=data.get('success', True),
            new_timeout_at=data['new_timeout_at'],
            added_minutes=added,
            max_allowed_minutes=data.get('max_allowed_minutes', 30),
            message=data.get('message', ''),
            minutes_extended=data.get('minutes_extended', added),
        )


@dataclass
class KeepAliveResponse:
    """
    Response from keep-alive toggle.
    
    Matches backend: KeepAliveResponse
    
    Attributes:
        container_id: Container ID
        keep_alive_enabled: Current keep-alive state
        requires_tier: Tier required for this feature
        user_tier: User's current tier
        is_authorized: Whether user is authorized for this feature
        message: Status message
    """
    container_id: str
    keep_alive_enabled: bool
    requires_tier: str
    user_tier: str
    is_authorized: bool
    message: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeepAliveResponse':
        """Create from API response dict."""
        return cls(
            container_id=data['container_id'],
            keep_alive_enabled=data.get('keep_alive_enabled', False),
            requires_tier=data.get('requires_tier', 'TEAM_ENTERPRISE'),
            user_tier=data.get('user_tier', 'FREE'),
            is_authorized=data.get('is_authorized', False),
            message=data.get('message', '')
        )


@dataclass
class HibernationResponse:
    """
    Response from hibernation or wake operations.
    
    Matches backend: HibernateResponse
    
    Attributes:
        container_id: Container ID
        status: Container status (e.g., 'hibernated', 'running')
        action: Action performed ('hibernate' or 'wake')
        estimated_resume_seconds: Estimated time to resume (for hibernation)
        message: Status message
    """
    container_id: str
    status: str
    action: str
    estimated_resume_seconds: Optional[int]
    message: str

    @property
    def state(self) -> str:
        """Alias for status, for convenience."""
        return self.status
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HibernationResponse':
        """Create from API response dict."""
        return cls(
            container_id=data['container_id'],
            status=data.get('status', 'unknown'),
            action=data.get('action', 'unknown'),
            estimated_resume_seconds=data.get('estimated_resume_seconds'),
            message=data.get('message', '')
        )


@dataclass
class LifecycleStatus:
    """
    Current lifecycle status of a container.
    
    Matches backend: LifecycleStatusResponse
    
    Attributes:
        container_id: Container ID
        state: Current lifecycle state (running, hibernating, stopped, starting, waking)
        idle_timeout_minutes: Configured idle timeout
        idle_action: Configured idle action (shutdown, hibernate, keep_alive)
        keep_alive_enabled: Whether keep-alive is enabled
        last_activity_at: Timestamp of last activity
        timeout_at: When container will timeout (None if keep_alive)
        time_remaining_seconds: Seconds until timeout (None if keep_alive)
        uptime_seconds: Total uptime in seconds
    """
    container_id: str
    state: str
    idle_timeout_minutes: int
    idle_action: str
    keep_alive_enabled: bool
    last_activity_at: str
    timeout_at: Optional[str]
    time_remaining_seconds: Optional[int]
    uptime_seconds: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LifecycleStatus':
        """Create from API response dict."""
        return cls(
            container_id=data['container_id'],
            state=data.get('state', 'running'),
            idle_timeout_minutes=data.get('idle_timeout_minutes', 30),
            idle_action=data.get('idle_action', 'shutdown'),
            keep_alive_enabled=data.get('keep_alive_enabled', False),
            last_activity_at=data['last_activity_at'],
            timeout_at=data.get('timeout_at'),
            time_remaining_seconds=data.get('time_remaining_seconds'),
            uptime_seconds=data.get('uptime_seconds', 0)
        )


# Tier limits for documentation and validation
TIER_LIMITS = {
    'FREE': {
        'max_idle_timeout_minutes': 30,
        'max_extensions': 0,
        'hibernate': False,
        'keep_alive': False,
    },
    'BASIC': {
        'max_idle_timeout_minutes': 60,
        'max_extensions': 2,
        'hibernate': False,
        'keep_alive': False,
    },
    'PRO': {
        'max_idle_timeout_minutes': 120,
        'max_extensions': 5,
        'hibernate': True,
        'keep_alive': False,
    },
    'ULTIMATE': {
        'max_idle_timeout_minutes': 240,
        'max_extensions': 10,
        'hibernate': True,
        'keep_alive': False,
    },
    'ENTERPRISE': {
        'max_idle_timeout_minutes': None,  # Unlimited
        'max_extensions': None,  # Unlimited
        'hibernate': True,
        'keep_alive': True,
    },
}

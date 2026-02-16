"""
Container management - matches backend /api/v1/sdk/containers endpoints exactly.

Backend endpoints:
- GET /api/v1/sdk/containers/{container_id}/info
- GET /api/v1/sdk/containers/{container_id}/stats
- POST /api/v1/sdk/containers/{container_id}/exec
- GET /api/v1/sdk/containers/{container_id}/processes
- POST /api/v1/sdk/containers/{container_id}/restart
- POST /api/v1/sdk/containers/{container_id}/heartbeat
- POST /api/v1/sdk/containers/{container_id}/extend-timeout
- POST /api/v1/sdk/containers/{container_id}/keep-alive
- POST /api/v1/sdk/containers/{container_id}/hibernate
- POST /api/v1/sdk/containers/{container_id}/wake
- GET /api/v1/sdk/containers/{container_id}/lifecycle
"""

from typing import Dict, Any, List, Optional
from .models import (
    ContainerInfo,
    ContainerStats,
    ContainerProcess,
    ContainerProcessList,
    ContainerExecResult
)
from .lifecycle import (
    LifecycleConfig,
    LifecycleState,
    LifecycleStatus,
    HeartbeatResponse,
    TimeoutExtensionResponse,
    KeepAliveResponse,
    HibernationResponse
)
from .exceptions import FleeksResourceNotFoundError, FleeksAPIError


class ContainerManager:
    """
    Manager for container operations.
    
    Provides access to container information, stats, command execution,
    process management, and container lifecycle operations.
    """
    
    def __init__(self, client, project_id: str, container_id: str):
        """
        Initialize container manager.
        
        Args:
            client: FleeksClient instance
            project_id: Project/workspace ID
            container_id: Container ID
        """
        self.client = client
        self.project_id = project_id
        self.container_id = container_id
    
    async def get_info(self) -> ContainerInfo:
        """
        Get container information.
        
        GET /api/v1/sdk/containers/{container_id}/info
        
        Returns:
            ContainerInfo: Complete container details including template,
                          languages, resource limits, ports
        
        Example:
            >>> info = await workspace.containers.get_info()
            >>> print(f"Container: {info.container_id}")
            >>> print(f"Template: {info.template}")
            >>> print(f"Languages: {', '.join(info.languages)}")
        """
        response = await self.client._make_request(
            'GET',
            f'containers/{self.container_id}/info'
        )
        return ContainerInfo.from_dict(response)
    
    async def get_stats(self) -> ContainerStats:
        """
        Get real-time container resource statistics.
        
        GET /api/v1/sdk/containers/{container_id}/stats
        
        Returns:
            ContainerStats: Real-time metrics including:
                - CPU usage percentage
                - Memory usage (MB and percentage)
                - Network I/O (RX/TX in MB)
                - Disk I/O (read/write in MB)
                - Process count
        
        Example:
            >>> stats = await workspace.containers.get_stats()
            >>> print(f"CPU: {stats.cpu_percent}%")
            >>> print(f"Memory: {stats.memory_mb}MB ({stats.memory_percent}%)")
            >>> print(f"Processes: {stats.process_count}")
        """
        response = await self.client._make_request(
            'GET',
            f'containers/{self.container_id}/stats'
        )
        return ContainerStats.from_dict(response)
    
    async def exec(
        self,
        command: str,
        working_dir: str = "/workspace",
        timeout_seconds: int = 30,
        environment: Optional[Dict[str, str]] = None
    ) -> ContainerExecResult:
        """
        Execute command inside container.
        
        POST /api/v1/sdk/containers/{container_id}/exec
        
        Args:
            command: Command to execute
            working_dir: Working directory (default: /workspace)
            timeout_seconds: Command timeout in seconds (1-3600)
            environment: Additional environment variables
        
        Returns:
            ContainerExecResult: Execution result with stdout/stderr/exit_code
        
        Example:
            >>> result = await workspace.containers.exec("python --version")
            >>> print(result.stdout)  # Python 3.11.5
            >>> 
            >>> result = await workspace.containers.exec(
            ...     "npm install",
            ...     working_dir="/workspace/frontend",
            ...     timeout_seconds=300
            ... )
        """
        data = {
            'command': command,
            'working_dir': working_dir,
            'timeout_seconds': timeout_seconds
        }
        if environment:
            data['environment'] = environment
        
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/exec',
            json=data
        )
        return ContainerExecResult.from_dict(response)
    
    async def get_processes(self) -> ContainerProcessList:
        """
        Get list of running processes in container.
        
        GET /api/v1/sdk/containers/{container_id}/processes
        
        Returns:
            ContainerProcessList: List of processes with PID, user, command,
                                 CPU and memory usage
        
        Example:
            >>> processes = await workspace.containers.get_processes()
            >>> print(f"Running {processes.process_count} processes:")
            >>> for proc in processes.processes:
            ...     print(f"  PID {proc.pid}: {proc.command} ({proc.cpu_percent}% CPU)")
        """
        response = await self.client._make_request(
            'GET',
            f'containers/{self.container_id}/processes'
        )
        return ContainerProcessList.from_dict(response)
    
    async def restart(self) -> Dict[str, Any]:
        """
        Restart the container.
        
        POST /api/v1/sdk/containers/{container_id}/restart
        
        Returns:
            dict: Restart confirmation with status and message
        
        Warning:
            This will restart the container and interrupt any running processes.
            All in-memory state will be lost.
        
        Example:
            >>> result = await workspace.containers.restart()
            >>> print(result['message'])  # Container restarted successfully
        """
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/restart'
        )
        return response
    
    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================
    
    async def heartbeat(self) -> HeartbeatResponse:
        """
        Send heartbeat to prevent idle shutdown.
        
        POST /api/v1/sdk/containers/{container_id}/heartbeat
        
        Call this periodically to keep the container alive when running
        long background tasks. Resets the idle timeout timer.
        
        Returns:
            HeartbeatResponse: Heartbeat status with next timeout timestamp
        
        Example:
            >>> # Keep container alive during long operation
            >>> for batch in process_large_dataset():
            ...     await process(batch)
            ...     heartbeat = await workspace.containers.heartbeat()
            ...     print(f"Next timeout: {heartbeat.next_timeout_at}")
        """
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/heartbeat'
        )
        return HeartbeatResponse.from_dict(response)
    
    async def extend_timeout(
        self,
        additional_minutes: int = 30
    ) -> TimeoutExtensionResponse:
        """
        Extend container timeout.
        
        POST /api/v1/sdk/containers/{container_id}/extend-timeout
        
        Adds additional time to the current timeout. Tier-dependent limits
        apply to how much time can be added and how many extensions allowed.
        
        Args:
            additional_minutes: Minutes to add (1-480, tier-dependent max)
        
        Returns:
            TimeoutExtensionResponse: Extension confirmation with new timeout
        
        Raises:
            FleeksPermissionError: If tier doesn't allow extension or limit reached
        
        Example:
            >>> ext = await workspace.containers.extend_timeout(60)
            >>> print(f"Extended by {ext.added_minutes} minutes")
            >>> print(f"New timeout: {ext.new_timeout_at}")
            >>> print(f"Max allowed: {ext.max_allowed_minutes}")
        """
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/extend-timeout',
            json={'additional_minutes': max(1, min(480, additional_minutes))}
        )
        return TimeoutExtensionResponse.from_dict(response)
    
    async def set_keep_alive(self, enabled: bool = True) -> KeepAliveResponse:
        """
        Enable/disable keep-alive mode.
        
        POST /api/v1/sdk/containers/{container_id}/keep-alive
        
        When enabled, container never auto-shuts down due to idle timeout.
        This feature is only available on Enterprise tier.
        
        Args:
            enabled: Enable or disable keep-alive
        
        Returns:
            KeepAliveResponse: Keep-alive status
        
        Raises:
            FleeksPermissionError: If tier doesn't support keep-alive
        
        Example:
            >>> # Enable always-on mode (Enterprise only)
            >>> result = await workspace.containers.set_keep_alive(True)
            >>> if result.keep_alive_enabled:
            ...     print("Container will never auto-shutdown")
        """
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/keep-alive',
            json={'enabled': enabled}
        )
        return KeepAliveResponse.from_dict(response)
    
    async def hibernate(self) -> HibernationResponse:
        """
        Manually hibernate container.
        
        POST /api/v1/sdk/containers/{container_id}/hibernate
        
        Hibernation pauses the container while preserving state. Resume is
        fast (typically under 5 seconds). This feature is available on
        Pro tier and above.
        
        Returns:
            HibernationResponse: Hibernation status
        
        Raises:
            FleeksPermissionError: If tier doesn't support hibernation
        
        Example:
            >>> # Put container to sleep
            >>> result = await workspace.containers.hibernate()
            >>> print(f"Status: {result.status}")  # hibernated
            >>> 
            >>> # Later, wake it up
            >>> await workspace.containers.wake()
        """
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/hibernate'
        )
        return HibernationResponse.from_dict(response)
    
    async def wake(self) -> HibernationResponse:
        """
        Wake container from hibernation.
        
        POST /api/v1/sdk/containers/{container_id}/wake
        
        Resumes a hibernated container. State is preserved from before
        hibernation. Wake time is typically under 5 seconds.
        
        Returns:
            HibernationResponse: Wake status with estimated ready time
        
        Example:
            >>> result = await workspace.containers.wake()
            >>> print(f"Status: {result.status}")  # running
            >>> if result.estimated_resume_seconds:
            ...     print(f"Ready in ~{result.estimated_resume_seconds}s")
        """
        response = await self.client._make_request(
            'POST',
            f'containers/{self.container_id}/wake'
        )
        return HibernationResponse.from_dict(response)
    
    async def get_lifecycle_status(self) -> LifecycleStatus:
        """
        Get current lifecycle status.
        
        GET /api/v1/sdk/containers/{container_id}/lifecycle
        
        Returns detailed information about the container's lifecycle state,
        timeouts, and keep-alive configuration.
        
        Returns:
            LifecycleStatus: Current lifecycle configuration and state
        
        Example:
            >>> status = await workspace.containers.get_lifecycle_status()
            >>> print(f"State: {status.state}")
            >>> print(f"Idle timeout: {status.idle_timeout_minutes}min")
            >>> if status.time_remaining_seconds:
            ...     print(f"Time until shutdown: {status.time_remaining_seconds}s")
            >>> if status.keep_alive_enabled:
            ...     print("Keep-alive is ON")
        """
        response = await self.client._make_request(
            'GET',
            f'containers/{self.container_id}/lifecycle'
        )
        return LifecycleStatus.from_dict(response)
    
    async def configure_lifecycle(
        self,
        config: LifecycleConfig
    ) -> LifecycleStatus:
        """
        Update container lifecycle configuration.
        
        PUT /api/v1/sdk/containers/{container_id}/lifecycle
        
        Allows modifying the container's lifecycle settings. Some options
        are tier-dependent.
        
        Args:
            config: New lifecycle configuration
        
        Returns:
            LifecycleStatus: Updated lifecycle status
        
        Raises:
            FleeksPermissionError: If config options exceed tier limits
        
        Example:
            >>> from fleeks_sdk.lifecycle import LifecycleConfig, IdleAction
            >>> 
            >>> # Configure for long-running development
            >>> config = LifecycleConfig(
            ...     idle_timeout_minutes=120,
            ...     idle_action=IdleAction.HIBERNATE,
            ...     keep_alive_on_preview=True
            ... )
            >>> status = await workspace.containers.configure_lifecycle(config)
            >>> print(f"Configured: {status.idle_timeout_minutes}min timeout")
        """
        response = await self.client._make_request(
            'PUT',
            f'containers/{self.container_id}/lifecycle',
            json=config.to_dict()
        )
        return LifecycleStatus.from_dict(response)


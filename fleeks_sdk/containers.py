"""
Container management - matches backend /api/v1/sdk/containers endpoints exactly.

Backend endpoints:
- GET /api/v1/sdk/containers/{container_id}/info
- GET /api/v1/sdk/containers/{container_id}/stats
- POST /api/v1/sdk/containers/{container_id}/exec
- GET /api/v1/sdk/containers/{container_id}/processes
- POST /api/v1/sdk/containers/{container_id}/restart
"""

from typing import Dict, Any, List, Optional
from .models import (
    ContainerInfo,
    ContainerStats,
    ContainerProcess,
    ContainerProcessList,
    ContainerExecResult
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
            f'/api/v1/sdk/containers/{self.container_id}/info'
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
            f'/api/v1/sdk/containers/{self.container_id}/stats'
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
            f'/api/v1/sdk/containers/{self.container_id}/exec',
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
            f'/api/v1/sdk/containers/{self.container_id}/processes'
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
            f'/api/v1/sdk/containers/{self.container_id}/restart'
        )
        return response

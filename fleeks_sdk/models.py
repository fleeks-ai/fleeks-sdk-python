"""
Data models matching backend Pydantic schemas exactly.

All models correspond 1:1 with backend response schemas from:
- app/api/api_v1/endpoints/sdk/workspaces.py
- app/api/api_v1/endpoints/sdk/containers.py
- app/api/api_v1/endpoints/sdk/files.py
- app/api/api_v1/endpoints/sdk/terminal.py
- app/api/api_v1/endpoints/sdk/agents.py
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class AgentType(str, Enum):
    """Agent types - matches backend AgentExecuteRequest"""
    AUTO = "auto"
    CODE = "code"
    RESEARCH = "research"
    DEBUG = "debug"
    TEST = "test"


class JobStatus(str, Enum):
    """Terminal job status - matches backend TerminalExecuteResponse"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentStatus(str, Enum):
    """Agent execution status - matches backend AgentStatusResponse"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    """File type classification"""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


# ============================================================================
# WORKSPACE MODELS
# ============================================================================

@dataclass
class WorkspaceInfo:
    """
    Workspace information - matches backend WorkspaceResponse.
    
    Represents a complete workspace with polyglot container environment.
    Includes preview URLs for instant HTTPS access to workspace applications.
    """
    project_id: str
    container_id: str
    template: str
    status: str
    created_at: str
    languages: List[str]
    resource_limits: Dict[str, str]
    preview_url: Optional[str] = None
    websocket_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceInfo':
        """Create from API response dict"""
        return cls(
            project_id=data['project_id'],
            container_id=data['container_id'],
            template=data['template'],
            status=data['status'],
            created_at=data['created_at'],
            languages=data['languages'],
            resource_limits=data['resource_limits'],
            preview_url=data.get('preview_url'),
            websocket_url=data.get('websocket_url')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        result = {
            'project_id': self.project_id,
            'container_id': self.container_id,
            'template': self.template,
            'status': self.status,
            'created_at': self.created_at,
            'languages': self.languages,
            'resource_limits': self.resource_limits
        }
        if self.preview_url:
            result['preview_url'] = self.preview_url
        if self.websocket_url:
            result['websocket_url'] = self.websocket_url
        return result


@dataclass
class WorkspaceHealth:
    """
    Workspace health status - matches backend health endpoint response.
    
    Provides comprehensive health metrics including container and agent status.
    """
    project_id: str
    status: str
    container: Dict[str, Any]
    agents: Dict[str, Any]
    last_activity: str
    uptime_seconds: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceHealth':
        """Create from API response dict"""
        return cls(
            project_id=data['project_id'],
            status=data['status'],
            container=data['container'],
            agents=data['agents'],
            last_activity=data['last_activity'],
            uptime_seconds=data['uptime_seconds']
        )


@dataclass
class PreviewURLInfo:
    """
    Preview URL information - matches backend preview-url endpoint response.
    
    Provides instant HTTPS access to workspace applications with zero configuration.
    """
    project_id: str
    preview_url: str
    websocket_url: str
    status: str
    container_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreviewURLInfo':
        """Create from API response dict"""
        return cls(
            project_id=data['project_id'],
            preview_url=data['preview_url'],
            websocket_url=data['websocket_url'],
            status=data['status'],
            container_id=data['container_id']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            'project_id': self.project_id,
            'preview_url': self.preview_url,
            'websocket_url': self.websocket_url,
            'status': self.status,
            'container_id': self.container_id
        }


# ============================================================================
# CONTAINER MODELS
# ============================================================================

@dataclass
class ContainerInfo:
    """
    Container information - matches backend ContainerInfoResponse.
    
    Provides complete container configuration and status.
    """
    container_id: str
    project_id: str
    template: str
    status: str
    ip_address: Optional[str]
    created_at: str
    languages: List[str]
    resource_limits: Dict[str, str]
    ports: Dict[str, int]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContainerInfo':
        """Create from API response dict"""
        return cls(
            container_id=data['container_id'],
            project_id=data['project_id'],
            template=data['template'],
            status=data['status'],
            ip_address=data.get('ip_address'),
            created_at=data['created_at'],
            languages=data['languages'],
            resource_limits=data['resource_limits'],
            ports=data['ports']
        )


@dataclass
class ContainerStats:
    """
    Container statistics - matches backend ContainerStatsResponse.
    
    Real-time resource usage metrics collected from Docker stats.
    """
    container_id: str
    cpu_percent: float
    memory_mb: int
    memory_percent: float
    network_rx_mb: float
    network_tx_mb: float
    disk_read_mb: float
    disk_write_mb: float
    process_count: int
    timestamp: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContainerStats':
        """Create from API response dict"""
        return cls(
            container_id=data['container_id'],
            cpu_percent=data['cpu_percent'],
            memory_mb=data['memory_mb'],
            memory_percent=data['memory_percent'],
            network_rx_mb=data['network_rx_mb'],
            network_tx_mb=data['network_tx_mb'],
            disk_read_mb=data['disk_read_mb'],
            disk_write_mb=data['disk_write_mb'],
            process_count=data['process_count'],
            timestamp=data['timestamp']
        )


@dataclass
class ContainerProcess:
    """
    Container process information.
    
    Single process running inside the container.
    """
    pid: int
    user: str
    command: str
    cpu_percent: float
    memory_mb: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContainerProcess':
        """Create from API response dict"""
        return cls(
            pid=data['pid'],
            user=data['user'],
            command=data['command'],
            cpu_percent=data['cpu_percent'],
            memory_mb=data['memory_mb']
        )


@dataclass
class ContainerProcessList:
    """
    Container process list - matches backend ContainerProcessListResponse.
    """
    container_id: str
    project_id: str
    process_count: int
    processes: List[ContainerProcess]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContainerProcessList':
        """Create from API response dict"""
        processes = [ContainerProcess.from_dict(p) for p in data['processes']]
        return cls(
            container_id=data['container_id'],
            project_id=data['project_id'],
            process_count=data['process_count'],
            processes=processes
        )


@dataclass
class ContainerExecResult:
    """
    Container command execution result - matches backend ContainerExecResponse.
    """
    container_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContainerExecResult':
        """Create from API response dict"""
        return cls(
            container_id=data['container_id'],
            command=data['command'],
            exit_code=data['exit_code'],
            stdout=data['stdout'],
            stderr=data['stderr'],
            execution_time_ms=data['execution_time_ms']
        )


# ============================================================================
# FILE MODELS
# ============================================================================

@dataclass
class FileInfo:
    """
    File information - matches backend FileInfoResponse.
    
    Complete metadata for a file or directory in workspace.
    """
    path: str
    name: str
    type: str  # "file" or "directory"
    size_bytes: int
    permissions: str
    created_at: str
    modified_at: str
    mime_type: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """Create from API response dict"""
        return cls(
            path=data['path'],
            name=data['name'],
            type=data['type'],
            size_bytes=data['size_bytes'],
            permissions=data['permissions'],
            created_at=data['created_at'],
            modified_at=data['modified_at'],
            mime_type=data.get('mime_type')
        )
    
    @property
    def is_file(self) -> bool:
        """Check if this is a file"""
        return self.type == "file"
    
    @property
    def is_directory(self) -> bool:
        """Check if this is a directory"""
        return self.type == "directory"


@dataclass
class DirectoryListing:
    """
    Directory listing - matches backend DirectoryListResponse.
    
    Contains files and subdirectories in a workspace directory.
    """
    project_id: str
    path: str
    total_count: int
    files: List[FileInfo]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DirectoryListing':
        """Create from API response dict"""
        files = [FileInfo.from_dict(f) for f in data['files']]
        return cls(
            project_id=data['project_id'],
            path=data['path'],
            total_count=data['total_count'],
            files=files
        )
    
    def get_files(self) -> List[FileInfo]:
        """Get only files (not directories)"""
        return [f for f in self.files if f.is_file]
    
    def get_directories(self) -> List[FileInfo]:
        """Get only directories"""
        return [f for f in self.files if f.is_directory]


# ============================================================================
# TERMINAL MODELS
# ============================================================================

@dataclass
class TerminalJob:
    """
    Terminal job - matches backend TerminalExecuteResponse.
    
    Represents a command execution (synchronous or background).
    """
    job_id: str
    project_id: str
    command: str
    status: str  # Will be converted to JobStatus enum if needed
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    completed_at: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerminalJob':
        """Create from API response dict"""
        return cls(
            job_id=data['job_id'],
            project_id=data['project_id'],
            command=data['command'],
            status=data['status'],
            exit_code=data.get('exit_code'),
            stdout=data.get('stdout', ''),
            stderr=data.get('stderr', ''),
            started_at=data.get('started_at', ''),
            completed_at=data.get('completed_at'),
            execution_time_ms=data.get('execution_time_ms')
        )
    
    @property
    def is_running(self) -> bool:
        """Check if job is still running"""
        return self.status == "running"
    
    @property
    def is_completed(self) -> bool:
        """Check if job completed successfully"""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed"""
        return self.status == "failed"


@dataclass
class TerminalJobList:
    """
    List of terminal jobs for a workspace.
    """
    project_id: str
    total_count: int
    jobs: List[TerminalJob]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerminalJobList':
        """Create from API response dict"""
        jobs = [TerminalJob.from_dict(j) for j in data['jobs']]
        return cls(
            project_id=data['project_id'],
            total_count=data['total_count'],
            jobs=jobs
        )


# ============================================================================
# AGENT MODELS
# ============================================================================

@dataclass
class AgentExecution:
    """
    Agent execution - matches backend AgentExecuteResponse.
    
    Represents an agent task execution started.
    """
    agent_id: str
    project_id: str
    task: str
    status: str  # Will be converted to AgentStatus enum if needed
    started_at: str
    message: str = "Agent execution started"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentExecution':
        """Create from API response dict"""
        return cls(
            agent_id=data['agent_id'],
            project_id=data['project_id'],
            task=data['task'],
            status=data['status'],
            started_at=data['started_at'],
            message=data.get('message', 'Agent execution started')
        )


@dataclass
class AgentHandoff:
    """
    Agent handoff response - matches backend AgentHandoffResponse.
    
    Represents successful CLI-to-cloud agent handoff.
    """
    agent_id: str
    project_id: str
    status: str
    handoff_id: str
    workspace_synced: bool
    context_preserved: bool
    message: str = "Agent handoff successful"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentHandoff':
        """Create from API response dict"""
        return cls(
            agent_id=data['agent_id'],
            project_id=data['project_id'],
            status=data['status'],
            handoff_id=data['handoff_id'],
            workspace_synced=data['workspace_synced'],
            context_preserved=data['context_preserved'],
            message=data.get('message', 'Agent handoff successful')
        )


@dataclass
class AgentStatusInfo:
    """
    Agent status details - matches backend AgentStatusResponse.
    
    Provides detailed progress and status of running agent.
    """
    agent_id: str
    project_id: str
    task: str
    status: str
    progress: int  # 0-100
    current_step: Optional[str] = None
    iterations_completed: int = 0
    max_iterations: int = 10
    started_at: str = ""
    completed_at: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStatusInfo':
        """Create from API response dict"""
        return cls(
            agent_id=data['agent_id'],
            project_id=data['project_id'],
            task=data['task'],
            status=data['status'],
            progress=data['progress'],
            current_step=data.get('current_step'),
            iterations_completed=data.get('iterations_completed', 0),
            max_iterations=data.get('max_iterations', 10),
            started_at=data.get('started_at', ''),
            completed_at=data.get('completed_at'),
            execution_time_ms=data.get('execution_time_ms')
        )
    
    @property
    def is_running(self) -> bool:
        """Check if agent is still running"""
        return self.status == "running"
    
    @property
    def is_completed(self) -> bool:
        """Check if agent completed successfully"""
        return self.status == "completed"


@dataclass
class AgentOutput:
    """
    Agent execution output - matches backend AgentOutputResponse.
    
    Contains complete results of agent execution.
    """
    agent_id: str
    project_id: str
    task: str
    files_modified: List[str]
    files_created: List[str]
    commands_executed: List[str]
    reasoning: List[str]
    errors: List[str]
    execution_time_ms: float
    iterations_completed: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentOutput':
        """Create from API response dict"""
        return cls(
            agent_id=data['agent_id'],
            project_id=data['project_id'],
            task=data['task'],
            files_modified=data.get('files_modified', []),
            files_created=data.get('files_created', []),
            commands_executed=data.get('commands_executed', []),
            reasoning=data.get('reasoning', []),
            errors=data.get('errors', []),
            execution_time_ms=data.get('execution_time_ms', 0.0),
            iterations_completed=data.get('iterations_completed', 0)
        )
    
    @property
    def has_errors(self) -> bool:
        """Check if agent encountered errors"""
        return len(self.errors) > 0
    
    @property
    def total_files_changed(self) -> int:
        """Get total number of files affected"""
        return len(self.files_modified) + len(self.files_created)


@dataclass
class AgentList:
    """
    List of agents for a workspace.
    """
    project_id: str
    total_count: int
    agents: List[AgentStatusInfo]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentList':
        """Create from API response dict"""
        agents = [AgentStatusInfo.from_dict(a) for a in data['agents']]
        return cls(
            project_id=data['project_id'],
            total_count=data['total_count'],
            agents=agents
        )


# ============================================================================
# BILLING MODELS
# ============================================================================

@dataclass
class UsageInfo:
    """
    Usage information from API response headers.
    
    Extracted from X-SDK-Usage-* headers in API responses.
    """
    requests_hour: int
    requests_day: int
    cost_month_cents: int
    request_cost_cents: int
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> 'UsageInfo':
        """Create from response headers"""
        return cls(
            requests_hour=int(headers.get('X-SDK-Usage-Requests-Hour', 0)),
            requests_day=int(headers.get('X-SDK-Usage-Requests-Day', 0)),
            cost_month_cents=int(headers.get('X-SDK-Usage-Cost-Month-Cents', 0)),
            request_cost_cents=int(headers.get('X-SDK-Request-Cost-Cents', 0))
        )
    
    @property
    def cost_month_dollars(self) -> float:
        """Get monthly cost in dollars"""
        return self.cost_month_cents / 100.0
    
    @property
    def request_cost_dollars(self) -> float:
        """Get request cost in dollars"""
        return self.request_cost_cents / 100.0

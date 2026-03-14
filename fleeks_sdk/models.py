"""
Data models matching backend Pydantic schemas exactly.

All models correspond 1:1 with backend response schemas from:
- app/api/api_v1/endpoints/sdk/workspaces.py
- app/api/api_v1/endpoints/sdk/containers.py
- app/api/api_v1/endpoints/sdk/files.py
- app/api/api_v1/endpoints/sdk/terminal.py
- app/api/api_v1/endpoints/sdk/agents.py
"""

from typing import Optional, List, Dict, Any, Union
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
    db_project_id: Optional[int] = None
    
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
            websocket_url=data.get('websocket_url'),
            db_project_id=data.get('db_project_id'),
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
        if self.db_project_id is not None:
            result['db_project_id'] = self.db_project_id
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
    memory_mb: float
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
    workspace_url: Optional[str] = None
    container_id: Optional[str] = None
    detected_types: List[str] = field(default_factory=list)
    active_skills: List[str] = field(default_factory=list)
    
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
            message=data.get('message', 'Agent handoff successful'),
            workspace_url=data.get('workspace_url'),
            container_id=data.get('container_id'),
            detected_types=data.get('detected_types', []),
            active_skills=data.get('active_skills', []),
        )


@dataclass
class AgentStopResponse:
    """
    Agent stop response - returned when stopping an agent.
    
    The backend clears the agent-active flag, removes project index,
    and updates the handoff record.
    """
    agent_id: str
    status: str
    message: str = "Agent stopped"
    handoff_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStopResponse':
        """Create from API response dict"""
        return cls(
            agent_id=data.get('agent_id', ''),
            status=data.get('status', 'stopped'),
            message=data.get('message', 'Agent stopped'),
            handoff_id=data.get('handoff_id'),
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


# ============================================================================
# DEPLOYMENT MODELS
# ============================================================================

class DeploymentStatusEnum(str, Enum):
    """Deployment status values — matches backend DeploymentStatus."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DeployResponse:
    """
    Response from POST /sdk/deploy — matches backend DeployResponse.
    """
    deployment_id: int
    project_id: Any  # int or str depending on backend version
    status: str
    message: str
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeployResponse':
        """Create from API response dict"""
        return cls(
            deployment_id=data['deployment_id'],
            project_id=data['project_id'],
            status=data['status'],
            message=data.get('message', ''),
            url=data.get('url'),
        )


@dataclass
class DeployStatus:
    """
    Deployment status details — matches backend DeployStatusResponse.
    """
    deployment_id: int
    project_id: Any  # int or str depending on backend version
    status: str
    url: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    health_status: Optional[str] = None
    framework: Optional[str] = None
    duration_seconds: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeployStatus':
        """Create from API response dict"""
        return cls(
            deployment_id=data['deployment_id'],
            project_id=data['project_id'],
            status=data['status'],
            url=data.get('url'),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            error_message=data.get('error_message'),
            health_status=data.get('health_status'),
            framework=data.get('framework'),
            duration_seconds=data.get('duration_seconds'),
        )

    @property
    def is_running(self) -> bool:
        """Check if deployment is still in progress"""
        return self.status in ("pending", "in_progress")

    @property
    def is_succeeded(self) -> bool:
        """Check if deployment succeeded"""
        return self.status == "succeeded"

    @property
    def is_failed(self) -> bool:
        """Check if deployment failed"""
        return self.status == "failed"


@dataclass
class DeployListItem:
    """
    Single item in a deployment list — matches backend list response.
    """
    deployment_id: int
    project_id: Any  # int or str depending on backend version
    deployment_number: int
    environment: str
    status: str
    url: Optional[str] = None
    created_at: Optional[str] = None
    health_status: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeployListItem':
        """Create from API response dict"""
        return cls(
            deployment_id=data['deployment_id'],
            project_id=data['project_id'],
            deployment_number=data.get('deployment_number', 0),
            environment=data.get('environment', 'production'),
            status=data['status'],
            url=data.get('url'),
            created_at=data.get('created_at'),
            health_status=data.get('health_status'),
        )


@dataclass
class DeployLogEvent:
    """
    A single structured log event from the Redis deploy log stream.

    Present when ``DeployLogs.source == "redis"``.
    """
    stage: str
    percent: int
    message: str
    deployment_id: Optional[int] = None
    project_id: Optional[Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeployLogEvent':
        return cls(
            stage=data.get('stage', ''),
            percent=data.get('percent', 0),
            message=data.get('message', ''),
            deployment_id=data.get('deployment_id'),
            project_id=data.get('project_id'),
        )


@dataclass
class DeployLogs:
    """
    Build/runtime log payload — matches backend GET /sdk/deploy/{id}/logs.

    ``logs`` is typed as ``Union[str, List[DeployLogEvent]]`` because the
    backend returns different shapes depending on the log source:

    * ``source == "redis"``        → structured list of DeployLogEvent objects
    * ``source == "cloud_logging"`` → plain string of Cloud Build log lines
    * ``source == "stored"``       → plain string from the DB deployment.logs column
    """
    deployment_id: int
    status: str
    source: str
    logs: Union[str, List['DeployLogEvent']]
    error_message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeployLogs':
        raw_logs = data.get('logs', '')
        source = data.get('source', 'stored')
        # When source is "redis" the API returns a list of event dicts
        if source == 'redis' and isinstance(raw_logs, list):
            parsed_logs: Union[str, List[DeployLogEvent]] = [
                DeployLogEvent.from_dict(e) if isinstance(e, dict) else e
                for e in raw_logs
            ]
        else:
            parsed_logs = raw_logs if isinstance(raw_logs, str) else str(raw_logs)
        return cls(
            deployment_id=data['deployment_id'],
            status=data['status'],
            source=source,
            logs=parsed_logs,
            error_message=data.get('error_message'),
        )

    @property
    def is_structured(self) -> bool:
        """True when ``logs`` is a list of DeployLogEvent objects."""
        return isinstance(self.logs, list)

    def as_text(self) -> str:
        """Return a human-readable string regardless of source type."""
        if isinstance(self.logs, list):
            return '\n'.join(
                f"[{e.stage}] {e.percent}%  {e.message}" for e in self.logs
            )
        return self.logs or ''


@dataclass
class ProvisionDbResult:
    """
    Result from POST /sdk/deploy/provision-db.

    Contains the connection URL and the Cloud Run env-var that was updated.
    Note: ``host`` ends in ``.svc.cluster.local`` — it is an internal address
    reachable only from within the GKE VPC (i.e. from your deployed Cloud Run service).
    """
    db_type: str
    connection_url: str
    env_var_name: str
    cloud_run_service: str
    host: str
    port: int
    message: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvisionDbResult':
        return cls(
            db_type=data.get('db_type', ''),
            connection_url=data.get('connection_url', ''),
            env_var_name=data.get('env_var_name', ''),
            cloud_run_service=data.get('cloud_run_service', ''),
            host=data.get('host', ''),
            port=int(data.get('port', 0)),
            message=data.get('message', ''),
        )


@dataclass
class MobileDistributeResult:
    """
    Result from POST /sdk/deploy/distribute/mobile.

    ``download_url`` is a signed GCS URL valid for 7 days.
    ``qr_code`` is a base64-encoded PNG of the QR code pointing to the same URL.
    """
    download_url: str
    qr_code: str
    platform: str
    gcs_path: str
    expires_in: str
    filename: str
    version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MobileDistributeResult':
        return cls(
            download_url=data.get('download_url', ''),
            qr_code=data.get('qr_code', ''),
            platform=data.get('platform', ''),
            gcs_path=data.get('gcs_path', ''),
            expires_in=data.get('expires_in', '7 days'),
            filename=data.get('filename', ''),
            version=data.get('version', ''),
        )


@dataclass
class DesktopDistributeResult:
    """
    Result from POST /sdk/deploy/distribute/desktop.

    ``download_urls`` maps OS name (``windows``, ``macos``, ``linux``) to a
    signed GCS URL valid for 7 days.  ``landing_page_url`` is the public CDN
    URL of the generated HTML download page (``https://downloads.fleeks.ai/…``).
    """
    download_urls: Dict[str, str]
    gcs_paths: Dict[str, str]
    landing_page_url: str
    expires_in: str
    version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DesktopDistributeResult':
        return cls(
            download_urls=data.get('download_urls', {}),
            gcs_paths=data.get('gcs_paths', {}),
            landing_page_url=data.get('landing_page_url', ''),
            expires_in=data.get('expires_in', '7 days'),
            version=data.get('version', ''),
        )


# ============================================================================
# SUB-AGENT MODELS
# ============================================================================

@dataclass
class SubAgentUsage:
    """Token usage statistics for a sub-agent execution."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubAgentUsage':
        """Create from API response dict."""
        return cls(
            input_tokens=data.get('input_tokens', 0),
            output_tokens=data.get('output_tokens', 0),
            total_tokens=data.get('total_tokens', 0),
            model=data.get('model', ''),
        )


@dataclass
class SubAgentResult:
    """
    Result from a sub-agent execution — matches backend SubAgentResponse.

    Returned by AgentManager.run_subagent().
    """
    sub_agent_id: str
    parent_agent_id: Optional[str]
    status: str
    result: str
    usage: SubAgentUsage
    execution_time_ms: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubAgentResult':
        """Create from API response dict."""
        usage_data = data.get('usage', {})
        return cls(
            sub_agent_id=data.get('sub_agent_id', ''),
            parent_agent_id=data.get('parent_agent_id'),
            status=data.get('status', 'completed'),
            result=data.get('result', ''),
            usage=SubAgentUsage.from_dict(usage_data),
            execution_time_ms=data.get('execution_time_ms', 0.0),
        )


# ============================================================================
# SCHEDULE / ALWAYS-ON AGENT MODELS
# ============================================================================

class ScheduleType(str, Enum):
    """Schedule trigger types — matches backend ScheduleType enum."""
    ALWAYS_ON = "always_on"
    CRON = "cron"
    INTERVAL = "interval"
    WEBHOOK = "webhook"
    EVENT = "event"
    MANUAL = "manual"


class DaemonStatus(str, Enum):
    """Daemon runtime status — matches backend DaemonStatus enum."""
    PROVISIONING = "provisioning"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    CRASHED = "crashed"


class ProjectType(str, Enum):
    """Project types — matches backend ProjectType enum (includes new agent_workspace)."""
    STANDARD = "standard"
    TEMPLATE = "template"
    EMBED = "embed"
    AGENT_WORKSPACE = "agent_workspace"


@dataclass
class Schedule:
    """
    Agent schedule — matches backend ScheduleResponse.

    Represents a configured schedule for always-on agents, cron jobs,
    webhook triggers, or manual executions.
    """
    schedule_id: str
    name: str
    schedule_type: str
    status: str
    agent_type: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    timezone: str = "UTC"
    default_task: Optional[str] = None
    max_iterations: int = 25
    system_prompt: Optional[str] = None
    model_override: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    auto_detect_skills: bool = True
    soul_prompt: Optional[str] = None
    agents_config: Optional[Dict[str, Any]] = None
    container_class: str = "standard"
    container_timeout_hours: float = 24.0
    auto_restart: bool = True
    max_restarts: int = 5
    memory_limit_mb: int = 2048
    cpu_limit_cores: float = 1.0
    tags: List[str] = field(default_factory=list)
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """Create from API response dict."""
        return cls(
            schedule_id=data['schedule_id'],
            name=data['name'],
            schedule_type=data.get('schedule_type', 'manual'),
            status=data.get('status', 'inactive'),
            agent_type=data.get('agent_type', 'auto'),
            created_at=data['created_at'],
            updated_at=data.get('updated_at', data['created_at']),
            description=data.get('description'),
            project_id=data.get('project_id'),
            cron_expression=data.get('cron_expression'),
            interval_seconds=data.get('interval_seconds'),
            timezone=data.get('timezone', 'UTC'),
            default_task=data.get('default_task'),
            max_iterations=data.get('max_iterations', 25),
            system_prompt=data.get('system_prompt'),
            model_override=data.get('model_override'),
            skills=data.get('skills', []),
            auto_detect_skills=data.get('auto_detect_skills', True),
            soul_prompt=data.get('soul_prompt'),
            agents_config=data.get('agents_config'),
            container_class=data.get('container_class', 'standard'),
            container_timeout_hours=data.get('container_timeout_hours', 24.0),
            auto_restart=data.get('auto_restart', True),
            max_restarts=data.get('max_restarts', 5),
            memory_limit_mb=data.get('memory_limit_mb', 2048),
            cpu_limit_cores=data.get('cpu_limit_cores', 1.0),
            tags=data.get('tags', []),
            last_run_at=data.get('last_run_at'),
            next_run_at=data.get('next_run_at'),
            run_count=data.get('run_count', 0),
        )


@dataclass
class ScheduleList:
    """Paginated list of schedules — matches backend ScheduleListResponse."""
    schedules: List[Schedule]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleList':
        """Create from API response dict."""
        schedules = [Schedule.from_dict(s) for s in data.get('schedules', [])]
        return cls(
            schedules=schedules,
            total=data.get('total', len(schedules)),
            limit=data.get('limit', 50),
            offset=data.get('offset', 0),
        )


@dataclass
class ScheduleStartResult:
    """Response from POST /sdk/schedules/{id}/start — daemon provisioning initiated."""
    schedule_id: str
    daemon_id: str
    status: str
    message: str
    project_id: Optional[int] = None
    workspace_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleStartResult':
        """Create from API response dict."""
        return cls(
            schedule_id=data.get('schedule_id', ''),
            daemon_id=data.get('daemon_id', ''),
            status=data.get('status', 'provisioning'),
            message=data.get('message', ''),
            project_id=data.get('project_id'),
            workspace_url=data.get('workspace_url'),
        )


@dataclass
class DaemonStatusInfo:
    """
    Daemon runtime status — matches backend DaemonStatusResponse.

    Now includes ``project_id`` and ``user_id`` (backend 2026-03-10 update).
    """
    schedule_id: str
    daemon_id: str
    status: str
    uptime_seconds: int
    cpu_percent: float
    memory_mb: float
    restart_count: int
    last_heartbeat: Optional[str] = None
    started_at: Optional[str] = None
    error_message: Optional[str] = None
    project_id: Optional[int] = None
    user_id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DaemonStatusInfo':
        """Create from API response dict."""
        return cls(
            schedule_id=data.get('schedule_id', ''),
            daemon_id=data.get('daemon_id', ''),
            status=data.get('status', 'unknown'),
            uptime_seconds=data.get('uptime_seconds', 0),
            cpu_percent=data.get('cpu_percent', 0.0),
            memory_mb=data.get('memory_mb', 0.0),
            restart_count=data.get('restart_count', 0),
            last_heartbeat=data.get('last_heartbeat'),
            started_at=data.get('started_at'),
            error_message=data.get('error_message'),
            project_id=data.get('project_id'),
            user_id=data.get('user_id'),
        )

    @property
    def uptime_display(self) -> str:
        """Human-readable uptime string."""
        secs = self.uptime_seconds
        hours, remainder = divmod(secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    @property
    def is_running(self) -> bool:
        return self.status == "running"


@dataclass
class DaemonLogs:
    """Daemon log output — matches backend DaemonLogsResponse."""
    schedule_id: str
    daemon_id: str
    lines: List[str]
    total_lines: int
    truncated: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DaemonLogs':
        """Create from API response dict."""
        return cls(
            schedule_id=data.get('schedule_id', ''),
            daemon_id=data.get('daemon_id', ''),
            lines=data.get('lines', []),
            total_lines=data.get('total_lines', 0),
            truncated=data.get('truncated', False),
        )


@dataclass
class QuotaMetric:
    """Single quota metric (e.g. agent-hours used vs limit)."""
    used: float
    limit: float
    unit: str = "hours"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuotaMetric':
        return cls(
            used=data.get('used', 0.0),
            limit=data.get('limit', 0.0),
            unit=data.get('unit', 'hours'),
        )

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.used)

    @property
    def percent_used(self) -> float:
        if self.limit <= 0:
            return 0.0
        return min(100.0, (self.used / self.limit) * 100.0)


@dataclass
class QuotaCounter:
    """Counter-type quota (schedules, concurrent daemons)."""
    current: int
    max_allowed: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuotaCounter':
        return cls(
            current=data.get('current', 0),
            max_allowed=data.get('max_allowed', 0),
        )


@dataclass
class QuotaUsage:
    """
    Agent-hours quota — matches backend QuotaUsageResponse.

    Provides billing-period usage, counters, and warning thresholds.
    """
    agent_hours: QuotaMetric
    schedules: QuotaCounter
    concurrent_daemons: QuotaCounter
    billing_period_start: str
    billing_period_end: str
    tier: str = "free"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuotaUsage':
        return cls(
            agent_hours=QuotaMetric.from_dict(data.get('agent_hours', {})),
            schedules=QuotaCounter.from_dict(data.get('schedules', {})),
            concurrent_daemons=QuotaCounter.from_dict(data.get('concurrent_daemons', {})),
            billing_period_start=data.get('billing_period_start', ''),
            billing_period_end=data.get('billing_period_end', ''),
            tier=data.get('tier', 'free'),
        )

    @property
    def is_warning(self) -> bool:
        """True when agent-hours usage exceeds 80%."""
        return self.agent_hours.percent_used >= 80.0

    @property
    def is_exceeded(self) -> bool:
        """True when agent-hours usage exceeds 100%."""
        return self.agent_hours.percent_used >= 100.0


# ============================================================================
# CHANNEL MODELS
# ============================================================================

class ChannelType(str, Enum):
    """Supported messaging channel types."""
    SLACK = "slack"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    TEAMS = "teams"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"
    CUSTOM = "custom"


@dataclass
class ChannelTypeInfo:
    """Information about a supported channel type."""
    channel_type: str
    display_name: str
    description: str
    auth_required: bool = True
    auth_flow: str = "oauth2"
    supported_features: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelTypeInfo':
        return cls(
            channel_type=data['channel_type'],
            display_name=data.get('display_name', ''),
            description=data.get('description', ''),
            auth_required=data.get('auth_required', True),
            auth_flow=data.get('auth_flow', 'oauth2'),
            supported_features=data.get('supported_features', []),
        )


@dataclass
class Channel:
    """
    Messaging channel — matches backend ChannelResponse.

    Represents a connected messaging platform integration.
    """
    channel_id: str
    schedule_id: str
    channel_type: str
    name: str
    status: str
    created_at: str
    updated_at: str
    config: Dict[str, Any] = field(default_factory=dict)
    last_message_at: Optional[str] = None
    message_count: int = 0
    error_message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Channel':
        return cls(
            channel_id=data['channel_id'],
            schedule_id=data['schedule_id'],
            channel_type=data['channel_type'],
            name=data.get('name', ''),
            status=data.get('status', 'inactive'),
            created_at=data['created_at'],
            updated_at=data.get('updated_at', data['created_at']),
            config=data.get('config', {}),
            last_message_at=data.get('last_message_at'),
            message_count=data.get('message_count', 0),
            error_message=data.get('error_message'),
        )


@dataclass
class ChannelList:
    """Paginated list of channels."""
    channels: List[Channel]
    total: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelList':
        channels = [Channel.from_dict(c) for c in data.get('channels', [])]
        return cls(
            channels=channels,
            total=data.get('total', len(channels)),
        )


@dataclass
class AuthFlowResult:
    """Result of initiating an OAuth/auth flow for a channel."""
    channel_id: str
    auth_url: str
    expires_in: int = 600
    state: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthFlowResult':
        return cls(
            channel_id=data.get('channel_id', ''),
            auth_url=data['auth_url'],
            expires_in=data.get('expires_in', 600),
            state=data.get('state', ''),
        )


# ============================================================================
# AUTOMATION MODELS
# ============================================================================

class TriggerType(str, Enum):
    """Automation trigger types."""
    WEBHOOK = "webhook"
    GITHUB_PR = "github_pr"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PUSH = "github_push"
    SLACK_MESSAGE = "slack_message"
    CRON = "cron"
    EVENT = "event"
    CUSTOM = "custom"


@dataclass
class Automation:
    """
    Automation trigger — matches backend AutomationResponse.

    Represents an event-driven trigger that fires agent tasks.
    """
    automation_id: str
    schedule_id: str
    name: str
    trigger_type: str
    status: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    filter_rules: Dict[str, Any] = field(default_factory=dict)
    last_triggered_at: Optional[str] = None
    trigger_count: int = 0
    error_message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Automation':
        return cls(
            automation_id=data['automation_id'],
            schedule_id=data['schedule_id'],
            name=data['name'],
            trigger_type=data.get('trigger_type', 'webhook'),
            status=data.get('status', 'inactive'),
            created_at=data['created_at'],
            updated_at=data.get('updated_at', data['created_at']),
            description=data.get('description'),
            trigger_config=data.get('trigger_config', {}),
            filter_rules=data.get('filter_rules', {}),
            last_triggered_at=data.get('last_triggered_at'),
            trigger_count=data.get('trigger_count', 0),
            error_message=data.get('error_message'),
        )


@dataclass
class AutomationList:
    """Paginated list of automations."""
    automations: List[Automation]
    total: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationList':
        automations = [Automation.from_dict(a) for a in data.get('automations', [])]
        return cls(
            automations=automations,
            total=data.get('total', len(automations)),
        )


@dataclass
class AutomationTestResult:
    """Result of testing an automation trigger."""
    automation_id: str
    success: bool
    trigger_type: str
    message: str
    agent_id: Optional[str] = None
    execution_time_ms: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationTestResult':
        return cls(
            automation_id=data.get('automation_id', ''),
            success=data.get('success', False),
            trigger_type=data.get('trigger_type', ''),
            message=data.get('message', ''),
            agent_id=data.get('agent_id'),
            execution_time_ms=data.get('execution_time_ms', 0.0),
        )


# ============================================================================
# PREVIEW SESSION MODELS (NEW — backend 2026-03-10)
# ============================================================================

class PreviewStatus(str, Enum):
    """Preview session lifecycle status — matches backend PreviewSessionStatus."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNHEALTHY = "unhealthy"


class PreviewFramework(str, Enum):
    """Detected or configured web framework for preview sessions."""
    REACT_VITE = "react_vite"
    REACT_CRA = "react_cra"
    NEXTJS = "nextjs"
    NUXT = "nuxt"
    VUE_VITE = "vue_vite"
    SVELTE = "svelte"
    SVELTEKIT = "sveltekit"
    ANGULAR = "angular"
    REMIX = "remix"
    ASTRO = "astro"
    FLASK = "flask"
    DJANGO = "django"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    STATIC = "static"
    CUSTOM = "custom"


@dataclass
class PreviewSession:
    """
    Preview session — matches backend PreviewSessionResponse.

    Represents a running preview environment for a project with
    instant HTTPS access and live-reload capabilities.
    """
    session_id: str
    project_id: int
    status: str
    preview_url: str
    port: int
    framework: str
    created_at: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    error_message: Optional[str] = None
    container_id: Optional[str] = None
    health_check_url: Optional[str] = None
    websocket_url: Optional[str] = None
    auto_detected: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreviewSession':
        """Create from API response dict."""
        return cls(
            session_id=data['session_id'],
            project_id=data['project_id'],
            status=data.get('status', 'starting'),
            preview_url=data.get('preview_url', ''),
            port=data.get('port', 3000),
            framework=data.get('framework', 'custom'),
            created_at=data['created_at'],
            started_at=data.get('started_at'),
            stopped_at=data.get('stopped_at'),
            last_activity_at=data.get('last_activity_at'),
            error_message=data.get('error_message'),
            container_id=data.get('container_id'),
            health_check_url=data.get('health_check_url'),
            websocket_url=data.get('websocket_url'),
            auto_detected=data.get('auto_detected', False),
        )

    @property
    def is_running(self) -> bool:
        return self.status == "running"

    @property
    def is_healthy(self) -> bool:
        return self.status in ("running",)


@dataclass
class PreviewSessionList:
    """Paginated list of preview sessions for a project."""
    sessions: List[PreviewSession]
    total: int
    project_id: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreviewSessionList':
        sessions = [PreviewSession.from_dict(s) for s in data.get('sessions', [])]
        return cls(
            sessions=sessions,
            total=data.get('total', len(sessions)),
            project_id=data.get('project_id', 0),
        )


@dataclass
class PreviewHealth:
    """Health check result for a preview session."""
    session_id: str
    healthy: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    checked_at: str = ""
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreviewHealth':
        return cls(
            session_id=data.get('session_id', ''),
            healthy=data.get('healthy', False),
            status_code=data.get('status_code'),
            response_time_ms=data.get('response_time_ms'),
            checked_at=data.get('checked_at', ''),
            error=data.get('error'),
        )


@dataclass
class PreviewDetectResult:
    """Result of auto-detecting the framework for preview configuration."""
    project_id: int
    detected_framework: str
    confidence: float
    suggested_port: int
    suggested_command: str
    config_files_found: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreviewDetectResult':
        return cls(
            project_id=data.get('project_id', 0),
            detected_framework=data.get('detected_framework', 'custom'),
            confidence=data.get('confidence', 0.0),
            suggested_port=data.get('suggested_port', 3000),
            suggested_command=data.get('suggested_command', ''),
            config_files_found=data.get('config_files_found', []),
        )

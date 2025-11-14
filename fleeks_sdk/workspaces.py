"""
Workspace management for the Fleeks SDK.

Matches backend endpoints in app/api/api_v1/endpoints/sdk/workspaces.py
"""

from typing import Dict, Any, List, Optional
from .models import WorkspaceInfo, WorkspaceHealth, PreviewURLInfo
from .exceptions import FleeksAPIError, FleeksResourceNotFoundError
from .containers import ContainerManager
from .files import FileManager
from .terminal import TerminalManager
from .agents import AgentManager


class Workspace:
    """
    Represents a single workspace with full access to its resources.
    
    A workspace includes:
    - Container (polyglot environment with 11+ languages)
    - File system (all workspace files)
    - Terminal (command execution)
    - Agents (AI assistants)
    
    Attributes:
        client: FleeksClient instance
        project_id: Unique project identifier
        container_id: Associated container ID
        containers: ContainerManager for container operations
        files: FileManager for file operations
        terminal: TerminalManager for command execution
        agents: AgentManager for agent operations
    """
    
    def __init__(self, client, workspace_info: WorkspaceInfo):
        """
        Initialize workspace instance.
        
        Args:
            client: FleeksClient instance
            workspace_info: WorkspaceInfo from API response
        """
        self.client = client
        self.project_id = workspace_info.project_id
        self.container_id = workspace_info.container_id
        self._info = workspace_info
        
        # Initialize resource managers
        self.containers = ContainerManager(client, self.project_id, self.container_id)
        self.files = FileManager(client, self.project_id)
        self.terminal = TerminalManager(client, self.project_id)
        self.agents = AgentManager(client, self.project_id)
    
    async def get_info(self) -> WorkspaceInfo:
        """
        Get current workspace information.
        
        GET /api/v1/sdk/workspaces/{project_id}
        
        Returns:
            WorkspaceInfo: Updated workspace information
        
        Example:
            >>> info = await workspace.get_info()
            >>> print(f"Status: {info.status}")
            >>> print(f"Languages: {', '.join(info.languages)}")
        """
        response = await self.client.get(f'workspaces/{self.project_id}')
        self._info = WorkspaceInfo.from_dict(response)
        return self._info
    
    async def get_health(self) -> WorkspaceHealth:
        """
        Get comprehensive health status.
        
        GET /api/v1/sdk/workspaces/{project_id}/health
        
        Returns:
            WorkspaceHealth: Health status including:
                - project_id: str
                - status: str
                - container: dict (id, status, cpu, memory)
                - agents: dict (active_count, total_count)
                - last_activity: str
                - uptime_seconds: int
        
        Example:
            >>> health = await workspace.get_health()
            >>> print(f"Container CPU: {health.container['cpu_percent']}%")
            >>> print(f"Active agents: {health.agents['active_count']}")
            >>> print(f"Uptime: {health.uptime_seconds}s")
        """
        response = await self.client.get(f'workspaces/{self.project_id}/health')
        return WorkspaceHealth.from_dict(response)
    
    async def get_preview_url(self) -> PreviewURLInfo:
        """
        Get preview URL for instant HTTPS access to workspace applications.
        
        GET /api/v1/sdk/workspaces/{project_id}/preview-url
        
        Preview URLs provide:
        - Zero-configuration HTTPS access
        - WebSocket support for real-time features
        - SSL certificates (auto-renewing)
        - Global CDN distribution
        
        Returns:
            PreviewURLInfo: Preview URL information including:
                - project_id: str
                - preview_url: str (HTTPS URL)
                - websocket_url: str (WSS URL)
                - status: str
                - container_id: str
        
        Example:
            >>> # Get preview URL
            >>> preview = await workspace.get_preview_url()
            >>> print(f"🌐 Preview URL: {preview.preview_url}")
            >>> print(f"🔌 WebSocket: {preview.websocket_url}")
            >>> 
            >>> # Start your application
            >>> await workspace.terminal.execute("python -m http.server 8080")
            >>> 
            >>> # Access at: https://preview.fleeks.ai/my-project/
        
        Note:
            Your application must be running in the workspace to be accessible
            via the preview URL. Common ports: 3000 (React), 8080 (Python),
            8000 (Django), 4200 (Angular).
        """
        response = await self.client.get(f'workspaces/{self.project_id}/preview-url')
        return PreviewURLInfo.from_dict(response)
    
    @property
    def preview_url(self) -> Optional[str]:
        """
        Get cached preview URL from workspace info.
        
        Note: This returns cached data from workspace creation.
              Use get_preview_url() for fresh data and full details.
        
        Returns:
            Optional[str]: Preview URL if available, None otherwise
        
        Example:
            >>> workspace = await client.workspaces.create("my-app", "python")
            >>> print(f"Preview URL: {workspace.preview_url}")
        """
        return self._info.preview_url
    
    @property
    def websocket_url(self) -> Optional[str]:
        """
        Get cached WebSocket URL from workspace info.
        
        Note: This returns cached data from workspace creation.
              Use get_preview_url() for fresh data and full details.
        
        Returns:
            Optional[str]: WebSocket URL if available, None otherwise
        
        Example:
            >>> workspace = await client.workspaces.create("my-app", "python")
            >>> print(f"WebSocket URL: {workspace.websocket_url}")
        """
        return self._info.websocket_url
    
    async def delete(self) -> None:
        """
        Delete this workspace permanently.
        
        DELETE /api/v1/sdk/workspaces/{project_id}
        
        Warning: This permanently deletes the workspace and all data.
                Cannot be undone!
        
        Example:
            >>> await workspace.delete()
            >>> # Workspace is now deleted
        """
        await self.client.delete(f'workspaces/{self.project_id}')
    
    @property
    def info(self) -> WorkspaceInfo:
        """
        Get cached workspace info.
        
        Note: This returns cached data. Use get_info() for fresh data.
        """
        return self._info
    
    def __repr__(self) -> str:
        return f"<Workspace project_id='{self.project_id}' status='{self._info.status}'>"


class WorkspaceManager:
    """
    Manager for workspace operations.
    
    Handles:
    - Creating new workspaces with templates
    - Listing user workspaces
    - Getting specific workspaces
    - Deleting workspaces
    
    Example:
        >>> async with FleeksClient(api_key="fleeks_sk_...") as client:
        ...     # Create workspace
        ...     workspace = await client.workspaces.create(
        ...         project_id="my-api",
        ...         template="python"
        ...     )
        ...     
        ...     # List workspaces
        ...     workspaces = await client.workspaces.list()
        ...     
        ...     # Get specific workspace
        ...     ws = await client.workspaces.get("my-api")
        ...     
        ...     # Delete workspace
        ...     await client.workspaces.delete("my-api")
    """
    
    def __init__(self, client):
        """
        Initialize workspace manager.
        
        Args:
            client: FleeksClient instance
        """
        self.client = client
    
    async def create(
        self,
        project_id: str,
        template: str = "default",
        pinned_versions: Optional[Dict[str, str]] = None
    ) -> Workspace:
        """
        Create new workspace with pre-warmed container.
        
        POST /api/v1/sdk/workspaces
        
        Backend uses ready container pool for sub-200ms startup time.
        Container includes 11+ languages: Python, Node, Go, Rust, Java, etc.
        
        Args:
            project_id: Unique project identifier (alphanumeric + hyphens/underscores)
            template: Container template, one of:
                - "default": All languages (recommended)
                - "python": Python-optimized
                - "node": Node.js-optimized
                - "go": Go-optimized
                - "rust": Rust-optimized
                - "java": Java-optimized
            pinned_versions: Optional language version pins
                Example: {"python": "3.11", "node": "20"}
        
        Returns:
            Workspace: New workspace instance with attached resources
        
        Raises:
            FleeksValidationError: If project_id invalid or already exists
            FleeksAPIError: For other API errors
        
        Performance: <200ms (sub-second startup via ready pool)
        
        Example:
            >>> # Create with defaults
            >>> workspace = await client.workspaces.create("my-project")
            >>> 
            >>> # Create with specific template
            >>> workspace = await client.workspaces.create(
            ...     project_id="python-api",
            ...     template="python",
            ...     pinned_versions={"python": "3.11"}
            ... )
            >>> 
            >>> # Access workspace resources
            >>> files = await workspace.files.list("/")
            >>> result = await workspace.terminal.execute("python --version")
            >>> agent = await workspace.agents.execute("Create a FastAPI hello world")
        """
        data = {
            'project_id': project_id,
            'template': template
        }
        if pinned_versions:
            data['pinned_versions'] = pinned_versions
        
        response = await self.client.post('workspaces', json=data)
        workspace_info = WorkspaceInfo.from_dict(response)
        return Workspace(self.client, workspace_info)
    
    async def get(self, project_id: str) -> Workspace:
        """
        Get existing workspace by project ID.
        
        GET /api/v1/sdk/workspaces/{project_id}
        
        Args:
            project_id: Project identifier
        
        Returns:
            Workspace: Workspace instance
        
        Raises:
            FleeksResourceNotFoundError: If workspace not found (404)
            FleeksPermissionError: If no access to workspace (403)
        
        Example:
            >>> workspace = await client.workspaces.get("my-project")
            >>> print(f"Status: {workspace.info.status}")
            >>> print(f"Container: {workspace.container_id}")
        """
        try:
            response = await self.client.get(f'workspaces/{project_id}')
            workspace_info = WorkspaceInfo.from_dict(response)
            return Workspace(self.client, workspace_info)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Workspace '{project_id}' not found"
                )
            raise
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> List[Workspace]:
        """
        List all workspaces for authenticated user.
        
        GET /api/v1/sdk/workspaces
        
        Args:
            page: Page number (1-indexed, default: 1)
            page_size: Items per page (max 100, default: 20)
            status_filter: Filter by status, one of:
                - "ready": Running and ready
                - "starting": Currently starting up
                - "stopped": Stopped/hibernated
                - None: All statuses
        
        Returns:
            list: List of Workspace instances
        
        Example:
            >>> # List all workspaces
            >>> workspaces = await client.workspaces.list()
            >>> for ws in workspaces:
            ...     print(f"{ws.project_id}: {ws.info.status}")
            >>> 
            >>> # List only ready workspaces
            >>> ready_workspaces = await client.workspaces.list(
            ...     status_filter="ready"
            ... )
            >>> 
            >>> # Paginate through workspaces
            >>> page_1 = await client.workspaces.list(page=1, page_size=10)
            >>> page_2 = await client.workspaces.list(page=2, page_size=10)
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        if status_filter:
            params['status_filter'] = status_filter
        
        response = await self.client.get('workspaces', params=params)
        
        workspaces = []
        for ws_data in response.get('workspaces', []):
            workspace_info = WorkspaceInfo.from_dict(ws_data)
            workspaces.append(Workspace(self.client, workspace_info))
        
        return workspaces
    
    async def delete(self, project_id: str) -> None:
        """
        Delete workspace by project ID.
        
        DELETE /api/v1/sdk/workspaces/{project_id}
        
        Warning: This permanently deletes the workspace and all data.
                Cannot be undone!
        
        Args:
            project_id: Project identifier
        
        Raises:
            FleeksResourceNotFoundError: If workspace not found
            FleeksPermissionError: If no access to workspace
        
        Example:
            >>> await client.workspaces.delete("old-project")
        """
        await self.client.delete(f'workspaces/{project_id}')

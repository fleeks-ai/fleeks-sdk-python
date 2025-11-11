"""
Agent management for the Fleeks SDK.

Matches backend endpoints in app/api/api_v1/endpoints/sdk/agents.py
"""

from typing import Dict, Any, List, Optional
from .models import (
    AgentType,
    AgentExecution,
    AgentHandoff,
    AgentStatusInfo,
    AgentOutput,
    AgentList
)
from .exceptions import FleeksAPIError, FleeksResourceNotFoundError


class AgentManager:
    """
    Manager for agent operations within a workspace.
    
    Handles:
    - Agent execution (auto, code, research, debug, test)
    - CLI-to-cloud handoff (revolutionary feature!)
    - Agent status monitoring
    - Agent output retrieval
    - Background agent management
    
    Example:
        >>> # Execute agent task
        >>> agent = await workspace.agents.execute(
        ...     task="Create a FastAPI hello world endpoint",
        ...     agent_type=AgentType.CODE
        ... )
        >>> 
        >>> # Check status
        >>> status = await workspace.agents.get_status(agent.agent_id)
        >>> print(f"Progress: {status.progress}%")
        >>> 
        >>> # Get output
        >>> output = await workspace.agents.get_output(agent.agent_id)
        >>> print(f"Files created: {output.files_created}")
    """
    
    def __init__(self, client, project_id: str):
        """
        Initialize agent manager for a workspace.
        
        Args:
            client: FleeksClient instance
            project_id: Project identifier
        """
        self.client = client
        self.project_id = project_id
    
    async def execute(
        self,
        task: str,
        agent_type: AgentType = AgentType.AUTO,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        auto_approve: bool = False
    ) -> AgentExecution:
        """
        Execute agent task in workspace.
        
        POST /api/v1/sdk/agents
        
        Agent runs in background and executes task autonomously.
        Use get_status() to monitor progress, get_output() for results.
        
        Args:
            task: Natural language task description
                Example: "Create a REST API with user authentication"
            agent_type: Type of agent to use:
                - AUTO: Automatically selects best agent
                - CODE: Code generation/modification
                - RESEARCH: Research and planning
                - DEBUG: Debugging and fixing issues
                - TEST: Test creation and execution
            context: Optional context dictionary
                Example: {"framework": "fastapi", "database": "postgresql"}
            max_iterations: Maximum reasoning iterations (1-50, default: 10)
            auto_approve: Auto-approve agent actions (default: False)
        
        Returns:
            AgentExecution: Started agent execution with:
                - agent_id: Unique agent identifier
                - project_id: Workspace project ID
                - task: Task description
                - status: Execution status
                - started_at: ISO timestamp
                - message: Status message
        
        Raises:
            FleeksValidationError: If task invalid or max_iterations out of range
            FleeksPermissionError: If no access to workspace
        
        Example:
            >>> # Simple code generation
            >>> agent = await workspace.agents.execute(
            ...     task="Create a user authentication module",
            ...     agent_type=AgentType.CODE
            ... )
            >>> 
            >>> # Research with context
            >>> agent = await workspace.agents.execute(
            ...     task="Research best practices for microservices",
            ...     agent_type=AgentType.RESEARCH,
            ...     context={"language": "python", "scale": "enterprise"}
            ... )
            >>> 
            >>> # Debugging with more iterations
            >>> agent = await workspace.agents.execute(
            ...     task="Fix the memory leak in user_service.py",
            ...     agent_type=AgentType.DEBUG,
            ...     max_iterations=20
            ... )
        """
        data = {
            'project_id': self.project_id,
            'task': task,
            'agent_type': agent_type.value,
            'max_iterations': max_iterations,
            'auto_approve': auto_approve
        }
        if context:
            data['context'] = context
        
        response = await self.client.post('agents', json=data)
        return AgentExecution.from_dict(response)
    
    async def handoff(
        self,
        task: str,
        local_context: Optional[Dict[str, Any]] = None,
        workspace_snapshot: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        agent_type: AgentType = AgentType.AUTO
    ) -> AgentHandoff:
        """
        CLI-to-cloud agent handoff (REVOLUTIONARY FEATURE!).
        
        POST /api/v1/sdk/agents/handoff
        
        Seamlessly transfers task from local CLI agent to cloud execution.
        Preserves full context: files, conversation history, workspace state.
        
        This enables:
        - Start task locally, finish in cloud
        - Offload heavy tasks to cloud compute
        - Collaborate between local and cloud agents
        - Context preservation across environments
        
        Args:
            task: Task to continue in cloud
            local_context: Local execution context
                Example: {
                    "current_file": "api.py",
                    "cursor_position": {"line": 42, "column": 10},
                    "recent_changes": [...]
                }
            workspace_snapshot: Current workspace state
                Example: {
                    "files": [...],
                    "git_status": {...},
                    "running_processes": [...]
                }
            conversation_history: Agent conversation history
                Example: [
                    {"role": "user", "content": "Create API"},
                    {"role": "assistant", "content": "I'll create..."},
                    ...
                ]
            agent_type: Agent type to use in cloud
        
        Returns:
            AgentHandoff: Handoff result with:
                - agent_id: Cloud agent ID
                - project_id: Workspace project ID
                - status: Handoff status
                - handoff_id: Unique handoff identifier
                - workspace_synced: Whether workspace synced
                - context_preserved: Whether context preserved
                - message: Status message
        
        Raises:
            FleeksValidationError: If handoff data invalid
            FleeksPermissionError: If no access to workspace
        
        Example:
            >>> # Basic handoff
            >>> handoff = await workspace.agents.handoff(
            ...     task="Continue implementing the user service",
            ...     local_context={
            ...         "current_file": "services/user.py",
            ...         "last_action": "Added authentication"
            ...     }
            ... )
            >>> 
            >>> # Full context handoff
            >>> handoff = await workspace.agents.handoff(
            ...     task="Complete the API implementation",
            ...     local_context={
            ...         "current_file": "api.py",
            ...         "cursor_position": {"line": 42, "column": 10}
            ...     },
            ...     workspace_snapshot={
            ...         "modified_files": ["api.py", "models.py"],
            ...         "git_branch": "feature/api"
            ...     },
            ...     conversation_history=[
            ...         {"role": "user", "content": "Create user API"},
            ...         {"role": "assistant", "content": "I created the endpoints..."}
            ...     ]
            ... )
            >>> 
            >>> print(f"Handoff ID: {handoff.handoff_id}")
            >>> print(f"Synced: {handoff.workspace_synced}")
            >>> print(f"Context preserved: {handoff.context_preserved}")
        """
        data = {
            'project_id': self.project_id,
            'task': task,
            'agent_type': agent_type.value
        }
        if local_context:
            data['local_context'] = local_context
        if workspace_snapshot:
            data['workspace_snapshot'] = workspace_snapshot
        if conversation_history:
            data['conversation_history'] = conversation_history
        
        response = await self.client.post('agents/handoff', json=data)
        return AgentHandoff.from_dict(response)
    
    async def get_status(self, agent_id: str) -> AgentStatusInfo:
        """
        Get agent execution status.
        
        GET /api/v1/sdk/agents/{agent_id}
        
        Returns detailed status including progress percentage (0-100),
        current step, iterations completed, and execution time.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            AgentStatusInfo: Status with:
                - agent_id: Agent identifier
                - project_id: Workspace project ID
                - task: Task description
                - status: Current status (running/completed/failed)
                - progress: Progress percentage (0-100)
                - current_step: Current execution step
                - iterations_completed: Completed iterations
                - max_iterations: Maximum iterations
                - started_at: Start timestamp
                - completed_at: Completion timestamp (if done)
                - execution_time_ms: Execution time in milliseconds
        
        Raises:
            FleeksResourceNotFoundError: If agent not found
        
        Example:
            >>> status = await workspace.agents.get_status(agent.agent_id)
            >>> print(f"Progress: {status.progress}%")
            >>> print(f"Step: {status.current_step}")
            >>> print(f"Status: {status.status}")
            >>> 
            >>> if status.is_completed:
            ...     print("Agent finished!")
            >>> elif status.is_running:
            ...     print(f"Still running... {status.progress}% done")
        """
        try:
            response = await self.client.get(f'agents/{agent_id}')
            return AgentStatusInfo.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Agent '{agent_id}' not found"
                )
            raise
    
    async def get_output(self, agent_id: str) -> AgentOutput:
        """
        Get agent execution output.
        
        GET /api/v1/sdk/agents/{agent_id}/output
        
        Returns complete results including files modified, commands executed,
        reasoning steps, and any errors encountered.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            AgentOutput: Complete output with:
                - agent_id: Agent identifier
                - project_id: Workspace project ID
                - task: Task description
                - files_modified: List of modified file paths
                - files_created: List of created file paths
                - commands_executed: List of executed commands
                - reasoning: List of reasoning steps
                - errors: List of errors (if any)
                - execution_time_ms: Total execution time
                - iterations_completed: Completed iterations
        
        Raises:
            FleeksResourceNotFoundError: If agent not found
        
        Example:
            >>> output = await workspace.agents.get_output(agent.agent_id)
            >>> 
            >>> print(f"Files created: {len(output.files_created)}")
            >>> for file in output.files_created:
            ...     print(f"  - {file}")
            >>> 
            >>> print(f"\\nFiles modified: {len(output.files_modified)}")
            >>> for file in output.files_modified:
            ...     print(f"  - {file}")
            >>> 
            >>> print(f"\\nCommands executed:")
            >>> for cmd in output.commands_executed:
            ...     print(f"  $ {cmd}")
            >>> 
            >>> if output.has_errors:
            ...     print(f"\\n⚠️ Errors encountered:")
            ...     for error in output.errors:
            ...         print(f"  - {error}")
        """
        try:
            response = await self.client.get(f'agents/{agent_id}/output')
            return AgentOutput.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Agent '{agent_id}' not found"
                )
            raise
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> AgentList:
        """
        List agents for this workspace.
        
        GET /api/v1/sdk/agents
        
        Args:
            page: Page number (1-indexed, default: 1)
            page_size: Items per page (max 100, default: 20)
            status_filter: Filter by status (running/completed/failed)
        
        Returns:
            AgentList: List of agents with:
                - project_id: Workspace project ID
                - total_count: Total number of agents
                - agents: List of AgentStatusInfo objects
        
        Example:
            >>> agents = await workspace.agents.list()
            >>> print(f"Total agents: {agents.total_count}")
            >>> 
            >>> for agent in agents.agents:
            ...     print(f"{agent.agent_id}: {agent.status} ({agent.progress}%)")
            >>> 
            >>> # Filter by status
            >>> running_agents = await workspace.agents.list(
            ...     status_filter="running"
            ... )
        """
        params = {
            'project_id': self.project_id,
            'page': page,
            'page_size': page_size
        }
        if status_filter:
            params['status_filter'] = status_filter
        
        response = await self.client.get('agents', params=params)
        return AgentList.from_dict(response)
    
    async def stop(self, agent_id: str) -> None:
        """
        Stop running agent.
        
        DELETE /api/v1/sdk/agents/{agent_id}
        
        Gracefully stops agent execution. Agent can be checked later
        for partial results.
        
        Args:
            agent_id: Agent identifier
        
        Raises:
            FleeksResourceNotFoundError: If agent not found
        
        Example:
            >>> # Stop long-running agent
            >>> await workspace.agents.stop(agent.agent_id)
            >>> 
            >>> # Check what it completed
            >>> output = await workspace.agents.get_output(agent.agent_id)
            >>> print(f"Completed {output.iterations_completed} iterations")
        """
        await self.client.delete(f'agents/{agent_id}')

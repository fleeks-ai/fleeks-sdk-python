"""
Terminal management - matches backend /api/v1/sdk/terminal endpoints exactly.

Backend endpoints:
- POST /api/v1/sdk/terminal/execute
- POST /api/v1/sdk/terminal/background
- GET /api/v1/sdk/terminal/jobs/{job_id}
- GET /api/v1/sdk/terminal/jobs
- DELETE /api/v1/sdk/terminal/jobs/{job_id}
- GET /api/v1/sdk/terminal/jobs/{job_id}/output
"""

from typing import Dict, Any, List, Optional
from .models import TerminalJob, TerminalJobList
from .exceptions import FleeksResourceNotFoundError, FleeksAPIError, FleeksTimeoutError


class TerminalManager:
    """
    Manager for terminal operations.
    
    Provides command execution capabilities:
    - Synchronous execution (wait for completion)
    - Background jobs (long-running processes)
    - Job status monitoring
    - Output retrieval
    """
    
    def __init__(self, client, project_id: str):
        """
        Initialize terminal manager.
        
        Args:
            client: FleeksClient instance
            project_id: Project/workspace ID
        """
        self.client = client
        self.project_id = project_id
    
    async def execute(
        self,
        command: str,
        working_dir: str = "/workspace",
        environment: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 30
    ) -> TerminalJob:
        """
        Execute command synchronously (waits for completion).
        
        POST /api/v1/sdk/terminal/execute
        
        Args:
            command: Command to execute
            working_dir: Working directory (default: /workspace)
            environment: Additional environment variables
            timeout_seconds: Maximum execution time (1-3600 seconds)
        
        Returns:
            TerminalJob: Completed job with stdout/stderr/exit_code
        
        Raises:
            FleeksTimeoutError: If command exceeds timeout
        
        Example:
            >>> job = await workspace.terminal.execute("python --version")
            >>> print(job.stdout)  # Python 3.11.5
            >>> print(f"Exit code: {job.exit_code}")
            >>> 
            >>> # With environment variables
            >>> job = await workspace.terminal.execute(
            ...     "echo $MY_VAR",
            ...     environment={"MY_VAR": "Hello"}
            ... )
        """
        data = {
            'project_id': self.project_id,
            'command': command,
            'working_dir': working_dir,
            'timeout_seconds': timeout_seconds
        }
        if environment:
            data['environment'] = environment
        
        try:
            response = await self.client._make_request(
                'POST',
                '/api/v1/sdk/terminal/execute',
                json=data
            )
            return TerminalJob.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 408:  # Request Timeout
                raise FleeksTimeoutError(
                    f"Command exceeded timeout of {timeout_seconds} seconds"
                )
            raise
    
    async def start_background_job(
        self,
        command: str,
        working_dir: str = "/workspace",
        environment: Optional[Dict[str, str]] = None
    ) -> TerminalJob:
        """
        Start command as background job (doesn't wait for completion).
        
        POST /api/v1/sdk/terminal/background
        
        Args:
            command: Command to execute
            working_dir: Working directory (default: /workspace)
            environment: Additional environment variables
        
        Returns:
            TerminalJob: Job information (status will be "running")
        
        Example:
            >>> # Start development server
            >>> job = await workspace.terminal.start_background_job(
            ...     "npm run dev",
            ...     working_dir="/workspace/frontend"
            ... )
            >>> print(f"Job ID: {job.job_id}")
            >>> 
            >>> # Check status later
            >>> status = await workspace.terminal.get_job(job.job_id)
            >>> print(f"Status: {status.status}")
        """
        data = {
            'project_id': self.project_id,
            'command': command,
            'working_dir': working_dir
        }
        if environment:
            data['environment'] = environment
        
        response = await self.client._make_request(
            'POST',
            '/api/v1/sdk/terminal/background',
            json=data
        )
        return TerminalJob.from_dict(response)
    
    async def get_job(self, job_id: str) -> TerminalJob:
        """
        Get job status and information.
        
        GET /api/v1/sdk/terminal/jobs/{job_id}
        
        Args:
            job_id: Job identifier
        
        Returns:
            TerminalJob: Current job status
        
        Raises:
            FleeksResourceNotFoundError: If job not found
        
        Example:
            >>> job = await workspace.terminal.get_job("550e8400-e29b-41d4-a716-446655440000")
            >>> if job.is_running:
            ...     print("Still running...")
            >>> elif job.is_completed:
            ...     print(f"Completed with exit code {job.exit_code}")
        """
        try:
            response = await self.client._make_request(
                'GET',
                f'/api/v1/sdk/terminal/jobs/{job_id}',
                params={'project_id': self.project_id}
            )
            return TerminalJob.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(f"Job not found: {job_id}")
            raise
    
    async def list_jobs(
        self,
        status_filter: Optional[str] = None
    ) -> TerminalJobList:
        """
        List all jobs for this workspace.
        
        GET /api/v1/sdk/terminal/jobs
        
        Args:
            status_filter: Filter by status (running, completed, failed, timeout)
        
        Returns:
            TerminalJobList: List of jobs
        
        Example:
            >>> jobs = await workspace.terminal.list_jobs(status_filter="running")
            >>> print(f"Running jobs: {jobs.total_count}")
            >>> for job in jobs.jobs:
            ...     print(f"  {job.job_id}: {job.command}")
        """
        params = {'project_id': self.project_id}
        if status_filter:
            params['status'] = status_filter
        
        response = await self.client._make_request(
            'GET',
            '/api/v1/sdk/terminal/jobs',
            params=params
        )
        return TerminalJobList.from_dict(response)
    
    async def stop_job(self, job_id: str) -> Dict[str, Any]:
        """
        Stop a running background job.
        
        DELETE /api/v1/sdk/terminal/jobs/{job_id}
        
        Args:
            job_id: Job identifier
        
        Returns:
            dict: Stop confirmation
        
        Example:
            >>> result = await workspace.terminal.stop_job(job_id)
            >>> print(result['message'])  # Job stopped successfully
        """
        response = await self.client._make_request(
            'DELETE',
            f'/api/v1/sdk/terminal/jobs/{job_id}',
            params={'project_id': self.project_id}
        )
        return response
    
    async def get_job_output(
        self,
        job_id: str,
        tail_lines: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Get job output (stdout/stderr).
        
        GET /api/v1/sdk/terminal/jobs/{job_id}/output
        
        Args:
            job_id: Job identifier
            tail_lines: Only return last N lines (optional)
        
        Returns:
            dict: Contains 'stdout' and 'stderr' keys
        
        Example:
            >>> output = await workspace.terminal.get_job_output(job_id, tail_lines=50)
            >>> print("Last 50 lines of stdout:")
            >>> print(output['stdout'])
        """
        params = {'project_id': self.project_id}
        if tail_lines:
            params['tail_lines'] = tail_lines
        
        response = await self.client._make_request(
            'GET',
            f'/api/v1/sdk/terminal/jobs/{job_id}/output',
            params=params
        )
        return response
    
    async def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 1.0,
        timeout: Optional[float] = None
    ) -> TerminalJob:
        """
        Wait for background job to complete.
        
        Polls job status until completion or timeout.
        
        Args:
            job_id: Job identifier
            poll_interval: Seconds between status checks (default: 1.0)
            timeout: Maximum wait time in seconds (None = wait forever)
        
        Returns:
            TerminalJob: Completed job
        
        Raises:
            FleeksTimeoutError: If timeout exceeded
        
        Example:
            >>> job = await workspace.terminal.start_background_job("npm test")
            >>> completed_job = await workspace.terminal.wait_for_job(
            ...     job.job_id,
            ...     timeout=300  # Wait up to 5 minutes
            ... )
            >>> print(f"Tests {'passed' if completed_job.exit_code == 0 else 'failed'}")
        """
        import asyncio
        import time
        
        start_time = time.time()
        
        while True:
            job = await self.get_job(job_id)
            
            if not job.is_running:
                return job
            
            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                raise FleeksTimeoutError(
                    f"Job did not complete within {timeout} seconds"
                )
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)

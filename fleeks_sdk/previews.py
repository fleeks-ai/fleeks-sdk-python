"""
Preview session management for the Fleeks SDK.

Manages preview environments that provide instant HTTPS access to running
applications inside workspace containers.

Backend endpoints:
    POST   /api/v1/preview/sessions/{project_id}/start   — Start preview session
    GET    /api/v1/preview/sessions/project/{project_id}  — List sessions for project
    GET    /api/v1/preview/sessions/{session_id}          — Get session details
    DELETE /api/v1/preview/sessions/{session_id}          — Stop/delete session
    POST   /api/v1/preview/sessions/{session_id}/refresh  — Refresh session
    GET    /api/v1/preview/sessions/{session_id}/health   — Health check
    POST   /api/v1/preview/sessions/{project_id}/detect   — Auto-detect framework

Note:
    The backend Celery beat task ``cleanup_stale_preview_sessions`` runs every
    30 minutes and may move sessions from RUNNING → STOPPED.  SDK consumers
    should handle this gracefully (e.g. re-start on 404 or STOPPED status).
"""

from typing import Dict, Any, List, Optional

from .models import (
    PreviewSession,
    PreviewSessionList,
    PreviewHealth,
    PreviewDetectResult,
    PreviewStatus,
    PreviewFramework,
)
from .exceptions import (
    FleeksAPIError,
    FleeksResourceNotFoundError,
    FleeksValidationError,
)


class PreviewManager:
    """
    Manage preview sessions for projects.

    Preview sessions provide instant HTTPS URLs for running web applications
    inside workspace containers — zero configuration, live-reload, and
    framework auto-detection.

    Example:
        >>> async with create_client() as client:
        ...     # Auto-detect framework and start preview
        ...     detection = await client.previews.detect(project_id=42)
        ...     session = await client.previews.start(
        ...         project_id=42,
        ...         framework=detection.detected_framework,
        ...         port=detection.suggested_port,
        ...     )
        ...     print(f"Preview live at {session.preview_url}")
        ...
        ...     # List all running sessions
        ...     sessions = await client.previews.list(project_id=42)
        ...     for s in sessions.sessions:
        ...         print(f"  {s.session_id}: {s.status}")
        ...
        ...     # Stop when done
        ...     await client.previews.stop(session.session_id)
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Preview CRUD / lifecycle
    # ------------------------------------------------------------------

    async def start(
        self,
        project_id: int,
        *,
        framework: str = "custom",
        port: int = 3000,
        command: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        health_check_path: str = "/",
        auto_detect: bool = True,
    ) -> PreviewSession:
        """
        Start a new preview session for a project.

        POST /api/v1/preview/sessions/{project_id}/start

        If ``auto_detect`` is True the backend will attempt to identify the
        framework from the project files and override ``framework`` / ``port``
        if a higher-confidence match is found.

        Args:
            project_id: Target project ID.
            framework: Web framework hint (see :class:`PreviewFramework`).
            port: Application port to expose (default 3000).
            command: Optional start command override (e.g. ``"npm run dev"``).
            env_vars: Additional environment variables injected into the
                preview container.
            health_check_path: HTTP path used for health probes (default ``"/"``).
            auto_detect: Let the backend auto-detect framework (default True).

        Returns:
            PreviewSession: The newly created session with ``preview_url``.

        Raises:
            FleeksValidationError: Invalid port or framework value.
            FleeksAPIError: On 409 (session already running) or server error.

        Example:
            >>> session = await client.previews.start(
            ...     project_id=42,
            ...     framework="react_vite",
            ...     port=5173,
            ... )
            >>> print(session.preview_url)
        """
        body: Dict[str, Any] = {
            "framework": framework,
            "port": port,
            "health_check_path": health_check_path,
            "auto_detect": auto_detect,
        }
        if command is not None:
            body["command"] = command
        if env_vars is not None:
            body["env_vars"] = env_vars

        response = await self._client._make_request(
            "POST",
            f"preview/sessions/{project_id}/start",
            json=body,
        )
        return PreviewSession.from_dict(response)

    async def get(self, session_id: str) -> PreviewSession:
        """
        Get details of a single preview session.

        GET /api/v1/preview/sessions/{session_id}

        Args:
            session_id: Preview session identifier.

        Returns:
            PreviewSession: Full session details.

        Raises:
            FleeksResourceNotFoundError: Session not found.
        """
        try:
            response = await self._client._make_request(
                "GET",
                f"preview/sessions/{session_id}",
            )
            return PreviewSession.from_dict(response)
        except FleeksAPIError as exc:
            if exc.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Preview session '{session_id}' not found"
                ) from exc
            raise

    async def list(
        self,
        project_id: int,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PreviewSessionList:
        """
        List preview sessions for a project.

        GET /api/v1/preview/sessions/project/{project_id}

        Args:
            project_id: Target project ID.
            status: Optional status filter (``"running"``, ``"stopped"``,
                ``"all"``).  Default is backend-defined (usually ``"running"``).
            limit: Maximum results to return (default 50).
            offset: Pagination offset.

        Returns:
            PreviewSessionList: Paginated list of sessions.

        Example:
            >>> running = await client.previews.list(42, status="running")
            >>> print(f"{running.total} active preview(s)")
        """
        params: Dict[str, Any] = {
            "limit": str(limit),
            "offset": str(offset),
        }
        if status is not None:
            params["status"] = status

        response = await self._client._make_request(
            "GET",
            f"preview/sessions/project/{project_id}",
            params=params,
        )
        return PreviewSessionList.from_dict(response)

    async def stop(self, session_id: str) -> Dict[str, Any]:
        """
        Stop and delete a preview session.

        DELETE /api/v1/preview/sessions/{session_id}

        The backend tears down the preview proxy, releases the port, and
        cleans up activity logs.

        Args:
            session_id: Preview session identifier.

        Returns:
            dict: Confirmation with ``{"status": "stopped", ...}``.

        Raises:
            FleeksResourceNotFoundError: Session not found.

        Example:
            >>> await client.previews.stop("prev_abc123")
        """
        try:
            return await self._client._make_request(
                "DELETE",
                f"preview/sessions/{session_id}",
            )
        except FleeksAPIError as exc:
            if exc.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Preview session '{session_id}' not found"
                ) from exc
            raise

    async def refresh(self, session_id: str) -> PreviewSession:
        """
        Refresh a preview session (restart the dev-server process).

        POST /api/v1/preview/sessions/{session_id}/refresh

        Useful after dependency installs, config changes, or when the
        dev-server enters an unhealthy state.

        Args:
            session_id: Preview session identifier.

        Returns:
            PreviewSession: Updated session with new timestamps.

        Raises:
            FleeksResourceNotFoundError: Session not found.

        Example:
            >>> refreshed = await client.previews.refresh("prev_abc123")
            >>> print(f"Status after refresh: {refreshed.status}")
        """
        try:
            response = await self._client._make_request(
                "POST",
                f"preview/sessions/{session_id}/refresh",
            )
            return PreviewSession.from_dict(response)
        except FleeksAPIError as exc:
            if exc.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Preview session '{session_id}' not found"
                ) from exc
            raise

    # ------------------------------------------------------------------
    # Health & detection
    # ------------------------------------------------------------------

    async def health(self, session_id: str) -> PreviewHealth:
        """
        Run a health check against a preview session.

        GET /api/v1/preview/sessions/{session_id}/health

        Args:
            session_id: Preview session identifier.

        Returns:
            PreviewHealth: Health probe result.

        Example:
            >>> h = await client.previews.health("prev_abc123")
            >>> if not h.healthy:
            ...     print(f"Unhealthy: {h.error}")
            ...     await client.previews.refresh("prev_abc123")
        """
        response = await self._client._make_request(
            "GET",
            f"preview/sessions/{session_id}/health",
        )
        return PreviewHealth.from_dict(response)

    async def detect(self, project_id: int) -> PreviewDetectResult:
        """
        Auto-detect the web framework for a project.

        POST /api/v1/preview/sessions/{project_id}/detect

        Inspects the project file tree (package.json, requirements.txt,
        pyproject.toml, etc.) to determine framework, ideal port, and
        start command.

        Args:
            project_id: Target project ID.

        Returns:
            PreviewDetectResult: Detection result with confidence score
                and suggested configuration.

        Example:
            >>> det = await client.previews.detect(42)
            >>> print(f"Framework: {det.detected_framework} "
            ...       f"(confidence {det.confidence:.0%})")
            >>> print(f"Suggested command: {det.suggested_command}")
        """
        response = await self._client._make_request(
            "POST",
            f"preview/sessions/{project_id}/detect",
        )
        return PreviewDetectResult.from_dict(response)

    # ------------------------------------------------------------------
    # Batch / convenience
    # ------------------------------------------------------------------

    async def cleanup(
        self,
        project_id: int,
        *,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Stop all stale or stopped preview sessions for a project.

        This is a client-side convenience that lists sessions, filters
        stale ones, and batch-stops them.

        Args:
            project_id: Target project ID.
            force: If True, stop *all* sessions including healthy ones.

        Returns:
            dict: Summary with ``stopped_count`` and ``session_ids``.

        Example:
            >>> result = await client.previews.cleanup(42)
            >>> print(f"Cleaned up {result['stopped_count']} session(s)")
        """
        sessions = await self.list(project_id, status="all")
        stopped_ids: List[str] = []

        for session in sessions.sessions:
            should_stop = force or session.status in (
                PreviewStatus.STOPPED.value,
                PreviewStatus.FAILED.value,
                PreviewStatus.UNHEALTHY.value,
            )
            if should_stop and session.status != PreviewStatus.STOPPED.value:
                try:
                    await self.stop(session.session_id)
                    stopped_ids.append(session.session_id)
                except FleeksResourceNotFoundError:
                    # Already cleaned up by Celery beat task — safe to ignore.
                    pass
            elif session.status == PreviewStatus.STOPPED.value:
                stopped_ids.append(session.session_id)

        return {
            "project_id": project_id,
            "stopped_count": len(stopped_ids),
            "session_ids": stopped_ids,
        }

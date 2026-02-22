"""
Fleeks Deploy Manager — programmatic deployment via SDK.

Provides full lifecycle management for project deployments:
  - Create (trigger a new deployment)
  - Status (check deployment progress)
  - Logs (retrieve build logs)
  - Rollback (revert to previous revision)
  - Delete (tear down infrastructure)
  - List (enumerate all deployments for a project)

All methods are async and route through the parent FleeksClient,
which prepends ``/api/v1/sdk/`` to each endpoint automatically.
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import FleeksClient

from .models import (
    DeployResponse,
    DeployStatus,
    DeployListItem,
)


class DeployManager:
    """Manage project deployments via the Fleeks SDK."""

    def __init__(self, client: "FleeksClient"):
        self._client = client

    # ── Create ───────────────────────────────────────────────

    async def create(
        self,
        project_id: Union[int, str],
        environment: str = "production",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> DeployResponse:
        """
        Initiate a new deployment.

        Args:
            project_id: The Fleeks project ID to deploy (numeric or string).
            environment: Target environment (``production``, ``staging``, ``development``).
            env_vars: Optional environment variables to inject into the deployment.

        Returns:
            DeployResponse with deployment_id, status, and URL once available.
        """
        body: Dict[str, Any] = {
            "project_id": project_id,
            "environment": environment,
        }
        if env_vars:
            body["env_vars"] = env_vars

        data = await self._client.post("deploy", json=body)
        return DeployResponse.from_dict(data)

    # ── Status ───────────────────────────────────────────────

    async def status(self, deployment_id: int) -> DeployStatus:
        """
        Get the current status of a deployment.

        Args:
            deployment_id: The deployment ID returned by ``create()``.

        Returns:
            DeployStatus with full deployment details.
        """
        data = await self._client.get(f"deploy/{deployment_id}")
        return DeployStatus.from_dict(data)

    # ── Logs ─────────────────────────────────────────────────

    async def logs(self, deployment_id: int) -> Dict[str, Any]:
        """
        Get deployment build/runtime logs.

        Args:
            deployment_id: The deployment ID.

        Returns:
            Dict with ``logs`` (str), ``status``, and ``source`` fields.
        """
        return await self._client.get(f"deploy/{deployment_id}/logs")

    async def stream_logs(self, deployment_id: int):
        """
        Stream real-time deployment logs via Server-Sent Events.

        Yields each SSE ``data:`` payload as a parsed dict. The stream
        ends when the deployment reaches a terminal status or the server
        closes the connection.

        Args:
            deployment_id: The deployment ID.

        Yields:
            Dict payloads from the SSE stream (stage, percent, message, etc.).

        Example::

            async for event in client.deploy.stream_logs(42):
                print(f"[{event.get('stage')}] {event.get('message')}")
        """
        import json as _json

        await self._client._ensure_client()
        url = f"/api/v1/sdk/deploy/{deployment_id}/logs/stream"
        async with self._client._client.stream("GET", url) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    raw = line[6:]
                    try:
                        yield _json.loads(raw)
                    except _json.JSONDecodeError:
                        yield {"raw": raw}

    # ── Rollback ─────────────────────────────────────────────

    async def rollback(self, deployment_id: int) -> Dict[str, Any]:
        """
        Rollback a deployment to the previous Cloud Run revision.

        Args:
            deployment_id: The deployment ID to rollback.

        Returns:
            Dict with ``success``, ``revision``, and ``message``.
        """
        return await self._client.post(f"deploy/{deployment_id}/rollback")

    # ── Delete ───────────────────────────────────────────────

    async def delete(self, deployment_id: int) -> Dict[str, Any]:
        """
        Delete a deployment and tear down all associated infrastructure
        (Cloud Run service, NEG, backend service, URL-map host rule).

        Args:
            deployment_id: The deployment ID to delete.

        Returns:
            Dict with ``success``, ``message``, ``service_name``.
        """
        return await self._client.delete(f"deploy/{deployment_id}")

    # ── List ─────────────────────────────────────────────────

    async def list(
        self,
        project_id: Union[int, str],
        limit: int = 20,
    ) -> List[DeployListItem]:
        """
        List deployments for a project.

        Args:
            project_id: The project ID to list deployments for (numeric or string).
            limit: Maximum number of results (default 20).

        Returns:
            List of DeployListItem objects.
        """
        data = await self._client.get(
            "deploy/list",
            params={"project_id": str(project_id), "limit": str(limit)},
        )
        # Backend returns a list directly or wrapped in an object
        items = data if isinstance(data, list) else data.get("deployments", data)
        if isinstance(items, list):
            return [DeployListItem.from_dict(d) for d in items]
        return []

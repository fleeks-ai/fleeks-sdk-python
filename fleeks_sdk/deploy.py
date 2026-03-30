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
    DeployLogs,
    ProvisionDbResult,
    MobileDistributeResult,
    DesktopDistributeResult,
    DiagnoseResult,
    HealthCheckResult,
    RuntimeLogsResult,
    MetricsResult,
    MultiDeployResult,
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

    async def logs(self, deployment_id: int) -> DeployLogs:
        """
        Get deployment build/runtime logs.

        The ``logs`` field of the returned object is either:

        * A ``List[DeployLogEvent]`` when ``source == "redis"`` (structured events
          with ``stage``, ``percent``, and ``message`` fields), or
        * A plain ``str`` for ``source == "cloud_logging"`` or ``"stored"``.

        Use ``result.as_text()`` to get a human-readable string in both cases.

        Args:
            deployment_id: The deployment ID.

        Returns:
            DeployLogs with ``deployment_id``, ``status``, ``source``, and ``logs``.
        """
        data = await self._client.get(f"deploy/{deployment_id}/logs")
        return DeployLogs.from_dict(data)

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

    # ── Provision Database ────────────────────────────────────

    async def provision_db(
        self,
        project_id: Union[int, str],
        db_type: str = "postgresql",
        environment: str = "production",
        env_var_name: Optional[str] = None,
    ) -> ProvisionDbResult:
        """
        Provision a database for a deployed Cloud Run service.

        Creates a logical database on the in-cluster DB server matching
        ``db_type``, injects the connection URL as an environment variable
        on the target Cloud Run service, and ensures the VPC connector is set.

        Supported ``db_type`` values: ``postgresql``, ``mysql``, ``mongodb``,
        ``redis``, ``qdrant``, ``neo4j``, ``kafka``, ``mariadb``.

        Args:
            project_id: The Fleeks project ID.
            db_type: Database engine to provision (default ``"postgresql"``).
            environment: Deployment environment (default ``"production"``).
            env_var_name: Custom env-var name injected into Cloud Run.  Defaults
                to ``DATABASE_URL`` for most engines.

        Returns:
            ProvisionDbResult with ``connection_url``, ``env_var_name``,
            ``cloud_run_service``, ``host``, ``port``, and ``message``.
        """
        body: Dict[str, Any] = {
            "project_id": project_id,
            "db_type": db_type,
            "environment": environment,
        }
        if env_var_name:
            body["env_var_name"] = env_var_name
        data = await self._client.post("deploy/provision-db", json=body)
        return ProvisionDbResult.from_dict(data)

    # ── Mobile Distribution ───────────────────────────────────

    async def distribute_mobile(
        self,
        artifact_path: str,
        project_id: Union[int, str],
        platform: str = "android",
        version: str = "1.0.0",
    ) -> MobileDistributeResult:
        """
        Upload a mobile build artifact to GCS and generate a download link + QR code.

        The artifact is uploaded to ``gs://fleeks-artifacts`` and a signed URL
        valid for 7 days is generated along with a base64-encoded QR code PNG.

        Args:
            artifact_path: Local path to the ``.apk`` / ``.ipa`` / ``.aab`` file.
            project_id: The Fleeks project ID.
            platform: Target platform — ``"android"`` or ``"ios"``.
            version: Build version string (e.g. ``"1.2.3"``).

        Returns:
            MobileDistributeResult with ``download_url``, ``qr_code`` (base64 PNG),
            ``platform``, ``gcs_path``, ``expires_in``, ``filename``, and ``version``.
        """
        import aiofiles  # soft dependency — installed with SDK extras

        params = {
            "project_id": str(project_id),
            "platform": platform,
            "version": version,
        }
        async with aiofiles.open(artifact_path, "rb") as fh:
            content = await fh.read()

        import os
        filename = os.path.basename(artifact_path)
        files = {"artifact": (filename, content, "application/octet-stream")}
        data = await self._client.post(
            "deploy/distribute/mobile",
            files=files,
            params=params,
        )
        return MobileDistributeResult.from_dict(data)

    # ── Desktop Distribution ──────────────────────────────────

    async def distribute_desktop(
        self,
        project_id: Union[int, str],
        version: str = "1.0.0",
        windows: Optional[str] = None,
        macos: Optional[str] = None,
        linux: Optional[str] = None,
    ) -> DesktopDistributeResult:
        """
        Upload desktop build artifacts to GCS and generate per-OS download links
        plus a public HTML landing page at ``https://downloads.fleeks.ai/{project_id}``.

        At least one of ``windows``, ``macos``, or ``linux`` must be provided.

        Args:
            project_id: The Fleeks project ID.
            version: Release version string.
            windows: Local path to the Windows installer (``.exe`` / ``.msi``).
            macos: Local path to the macOS package (``.dmg`` / ``.pkg``).
            linux: Local path to the Linux package (``.AppImage`` / ``.deb`` / ``.rpm``).

        Returns:
            DesktopDistributeResult with ``download_urls`` (per-OS), ``gcs_paths``,
            ``landing_page_url``, ``expires_in``, and ``version``.
        """
        import os
        import aiofiles  # soft dependency

        if not any([windows, macos, linux]):
            raise ValueError(
                "At least one platform artifact (windows, macos, linux) must be provided."
            )

        params = {"project_id": str(project_id), "version": version}
        files: Dict[str, Any] = {}

        for platform_key, path in [("windows", windows), ("macos", macos), ("linux", linux)]:
            if path:
                async with aiofiles.open(path, "rb") as fh:
                    content = await fh.read()
                files[platform_key] = (os.path.basename(path), content, "application/octet-stream")

        data = await self._client.post(
            "deploy/distribute/desktop",
            files=files,
            params=params,
        )
        return DesktopDistributeResult.from_dict(data)

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

    # ── Diagnose ─────────────────────────────────────────────

    async def diagnose(self, deployment_id: int) -> DiagnoseResult:
        """
        Diagnose a failed deployment.

        Pattern-matches against 13 known failure signatures (npm errors,
        missing modules, OOM kills, port conflicts, etc.) and returns an
        actionable diagnosis with suggested fixes.

        Args:
            deployment_id: The deployment ID to diagnose.

        Returns:
            DiagnoseResult with patterns_found, diagnosis, suggested_fixes.
        """
        data = await self._client.post(f"deploy/{deployment_id}/diagnose")
        return DiagnoseResult.from_dict(data)

    # ── Health ───────────────────────────────────────────────

    async def health(self, deployment_id: int) -> HealthCheckResult:
        """
        Check the health of a deployed Cloud Run service.

        Inspects revision conditions, traffic split, and URL reachability.
        Returns HEALTHY, DEGRADED, or UNHEALTHY.

        Args:
            deployment_id: The deployment ID to check.

        Returns:
            HealthCheckResult with status, revisions, traffic, url_check.
        """
        data = await self._client.get(f"deploy/{deployment_id}/health")
        return HealthCheckResult.from_dict(data)

    # ── Runtime Logs ─────────────────────────────────────────

    async def runtime_logs(
        self,
        deployment_id: int,
        severity: str = "DEFAULT",
        limit: int = 50,
    ) -> RuntimeLogsResult:
        """
        Fetch live runtime (container) logs from Cloud Logging.

        Different from ``logs()`` which returns build-time logs. Use this
        when the app is deployed but crashing or returning errors.

        Args:
            deployment_id: The deployment ID.
            severity: Minimum severity filter (DEFAULT, INFO, WARNING, ERROR, CRITICAL).
            limit: Maximum number of log entries (1–200, default 50).

        Returns:
            RuntimeLogsResult with log entries, count, and error_count.
        """
        data = await self._client.get(
            f"deploy/{deployment_id}/runtime-logs",
            params={"severity": severity, "limit": str(limit)},
        )
        return RuntimeLogsResult.from_dict(data)

    # ── Metrics ──────────────────────────────────────────────

    async def metrics(
        self,
        deployment_id: int,
        window_minutes: int = 60,
    ) -> MetricsResult:
        """
        Fetch performance metrics for a deployed Cloud Run service.

        Returns request count, latency percentiles (p50/p95/p99), error
        rate, and active instance count over the specified time window.

        Args:
            deployment_id: The deployment ID.
            window_minutes: Lookback window in minutes (1–1440, default 60).

        Returns:
            MetricsResult with request_count, error_rate, latency_ms, instance_count.
        """
        data = await self._client.get(
            f"deploy/{deployment_id}/metrics",
            params={"window_minutes": str(window_minutes)},
        )
        return MetricsResult.from_dict(data)

    # ── Multi-Service Deploy ─────────────────────────────────

    async def multi_deploy(
        self,
        project_id: Union[int, str],
        environment: str = "staging",
        manifest_yaml: Optional[str] = None,
    ) -> MultiDeployResult:
        """
        Deploy a multi-service project from a fleeks.yaml manifest.

        Each service in the manifest gets its own Cloud Run instance with
        auto-injected service-to-service URLs. If ``manifest_yaml`` is
        omitted the manifest is read from the project's GCS workspace.

        Tier limits apply: FREE/BASIC=1 service, PRO=3, ULTIMATE=10.

        Args:
            project_id: The Fleeks project ID.
            environment: Target environment (default ``"staging"``).
            manifest_yaml: Optional fleeks.yaml content as a string.

        Returns:
            MultiDeployResult with group_id, per-service results, and totals.
        """
        body: Dict[str, Any] = {
            "project_id": project_id,
            "environment": environment,
        }
        if manifest_yaml:
            body["manifest_yaml"] = manifest_yaml
        data = await self._client.post("deploy/multi", json=body)
        return MultiDeployResult.from_dict(data)

    # ── Secrets ──────────────────────────────────────────────

    async def set_secrets(
        self,
        project_id: Union[int, str],
        secrets: Dict[str, str],
        environment: str = "production",
    ) -> Dict[str, Any]:
        """
        Set environment secrets for a project.

        Secrets are stored in GCP Secret Manager and auto-injected into
        the project's Cloud Run service on the next deploy.

        Args:
            project_id: The Fleeks project ID.
            secrets: Dict of key-value pairs to store.
            environment: Target environment (default ``"production"``).

        Returns:
            Dict with ``success`` and ``message``.
        """
        body: Dict[str, Any] = {
            "project_id": project_id,
            "secrets": secrets,
            "environment": environment,
        }
        return await self._client.post("deploy/secrets", json=body)

    async def list_secrets(self, project_id: Union[int, str]) -> Dict[str, Any]:
        """
        List secret keys for a project (values are never exposed).

        Args:
            project_id: The Fleeks project ID.

        Returns:
            Dict with ``project_id``, ``secrets`` (list of key entries), ``count``.
        """
        return await self._client.get(f"deploy/secrets/{project_id}")

    async def delete_secrets(self, project_id: Union[int, str]) -> Dict[str, Any]:
        """
        Delete all secrets for a project.

        Args:
            project_id: The Fleeks project ID.

        Returns:
            Dict with ``success`` and ``message``.
        """
        return await self._client.delete(f"deploy/secrets/{project_id}")

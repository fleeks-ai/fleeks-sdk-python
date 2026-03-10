"""
Schedule management for the Fleeks SDK.

Matches backend endpoints in app/api/api_v1/endpoints/sdk/agent_schedules.py

Endpoints:
    POST   /sdk/schedules/              — Create agent schedule
    GET    /sdk/schedules/              — List user's schedules
    GET    /sdk/schedules/{id}          — Get schedule details
    PUT    /sdk/schedules/{id}          — Update schedule
    DELETE /sdk/schedules/{id}          — Delete schedule
    POST   /sdk/schedules/{id}/start    — Start schedule (provision daemon)
    POST   /sdk/schedules/{id}/stop     — Stop schedule (teardown daemon)
    POST   /sdk/schedules/{id}/pause    — Pause schedule
    POST   /sdk/schedules/{id}/resume   — Resume schedule
    GET    /sdk/schedules/{id}/status   — Get daemon runtime status
    GET    /sdk/schedules/{id}/logs     — Get daemon logs
    GET    /sdk/schedules/quota         — Get agent-hours quota usage
"""

from typing import Dict, Any, List, Optional
from .models import (
    Schedule,
    ScheduleList,
    ScheduleStartResult,
    DaemonStatusInfo,
    DaemonLogs,
    QuotaUsage,
)
from .exceptions import FleeksAPIError, FleeksResourceNotFoundError


class ScheduleManager:
    """
    Manager for agent schedule operations.

    Handles always-on agents, cron schedules, webhook triggers,
    daemon lifecycle, quota tracking, and log retrieval.

    Example:
        >>> async with create_client() as client:
        ...     # Create always-on schedule
        ...     sched = await client.schedules.create(
        ...         name="PR Review Bot",
        ...         schedule_type="always_on",
        ...         agent_type="code",
        ...     )
        ...     await client.schedules.start(sched.schedule_id)
        ...     status = await client.schedules.status(sched.schedule_id)
        ...     print(f"Daemon: {status.status} — uptime {status.uptime_display}")
    """

    def __init__(self, client):
        self.client = client

    # ── CRUD ────────────────────────────────────────────────

    async def create(
        self,
        name: str,
        schedule_type: str = "manual",
        *,
        description: Optional[str] = None,
        project_id: Optional[int] = None,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        timezone: str = "UTC",
        agent_type: str = "auto",
        default_task: Optional[str] = None,
        max_iterations: int = 25,
        system_prompt: Optional[str] = None,
        model_override: Optional[str] = None,
        skills: Optional[List[str]] = None,
        auto_detect_skills: bool = True,
        soul_prompt: Optional[str] = None,
        agents_config: Optional[Dict[str, Any]] = None,
        container_class: str = "standard",
        container_timeout_hours: float = 24.0,
        auto_restart: bool = True,
        max_restarts: int = 5,
        memory_limit_mb: int = 2048,
        cpu_limit_cores: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> Schedule:
        """
        Create a new agent schedule.

        Args:
            name: Schedule name (required, 1-255 chars).
            schedule_type: One of "always_on", "cron", "webhook",
                "event", "manual", "interval".
            description: Optional description.
            project_id: Link to an existing project.
            cron_expression: Required for "cron" type (e.g., "0 9 * * MON-FRI").
            interval_seconds: Required for "interval" type (60-86400).
            timezone: IANA timezone (default: "UTC").
            agent_type: "auto", "code", "research", "debug", "assistant".
            default_task: Default task prompt for the agent.
            max_iterations: Max reasoning iterations per run (1-100).
            system_prompt: Custom system prompt override.
            model_override: LLM model override (e.g., "claude-sonnet-4-20250514").
            skills: Skills to load (list of skill names).
            auto_detect_skills: Auto-detect skills from context.
            soul_prompt: Custom SOUL.md personality content.
            agents_config: Multi-agent routing rules.
            container_class: "standard", "persistent", or "gpu".
            container_timeout_hours: Max container lifetime (1-720 hours).
            auto_restart: Auto-restart daemon on crash.
            max_restarts: Max restart attempts (0-50).
            memory_limit_mb: Memory limit in MB (512-16384).
            cpu_limit_cores: CPU limit (0.25-8.0).
            tags: User-defined tags.

        Returns:
            Schedule: Created schedule.

        Raises:
            FleeksValidationError: Invalid params (bad cron, out-of-range values).
            FleeksAPIError: On 402 (quota exceeded) or server error.
        """
        body: Dict[str, Any] = {
            "name": name,
            "schedule_type": schedule_type,
            "timezone": timezone,
            "agent_type": agent_type,
            "max_iterations": max_iterations,
            "auto_detect_skills": auto_detect_skills,
            "container_class": container_class,
            "container_timeout_hours": container_timeout_hours,
            "auto_restart": auto_restart,
            "max_restarts": max_restarts,
            "memory_limit_mb": memory_limit_mb,
            "cpu_limit_cores": cpu_limit_cores,
        }
        if description is not None:
            body["description"] = description
        if project_id is not None:
            body["project_id"] = project_id
        if cron_expression is not None:
            body["cron_expression"] = cron_expression
        if interval_seconds is not None:
            body["interval_seconds"] = interval_seconds
        if default_task is not None:
            body["default_task"] = default_task
        if system_prompt is not None:
            body["system_prompt"] = system_prompt
        if model_override is not None:
            body["model_override"] = model_override
        if skills is not None:
            body["skills"] = skills
        if soul_prompt is not None:
            body["soul_prompt"] = soul_prompt
        if agents_config is not None:
            body["agents_config"] = agents_config
        if tags is not None:
            body["tags"] = tags

        response = await self.client.post("schedules", json=body)
        return Schedule.from_dict(response)

    async def list(
        self,
        *,
        active_only: bool = True,
        schedule_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ScheduleList:
        """
        List agent schedules.

        Args:
            active_only: Only return active schedules (default: True).
            schedule_type: Filter by type (e.g., "always_on", "cron").
            limit: Max results (default: 50).
            offset: Pagination offset.

        Returns:
            ScheduleList: Paginated schedule list with total count.
        """
        params: Dict[str, Any] = {
            "active_only": str(active_only).lower(),
            "limit": str(limit),
            "offset": str(offset),
        }
        if schedule_type:
            params["schedule_type"] = schedule_type

        response = await self.client.get("schedules", params=params)
        return ScheduleList.from_dict(response)

    async def get(self, schedule_id: str) -> Schedule:
        """
        Get schedule details.

        Args:
            schedule_id: Schedule identifier (e.g., "sched_a1b2c3d4").

        Returns:
            Schedule: Full schedule details.

        Raises:
            FleeksResourceNotFoundError: Schedule not found.
        """
        try:
            response = await self.client.get(f"schedules/{schedule_id}")
            return Schedule.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Schedule '{schedule_id}' not found"
                )
            raise

    async def update(
        self,
        schedule_id: str,
        **kwargs,
    ) -> Schedule:
        """
        Update a schedule. Pass only the fields you want to change.

        Args:
            schedule_id: Schedule identifier.
            **kwargs: Fields to update. Accepted keys:
                name, description, cron_expression, interval_seconds,
                timezone, agent_type, default_task, max_iterations,
                system_prompt, model_override, skills, auto_detect_skills,
                soul_prompt, agents_config, auto_restart, max_restarts,
                memory_limit_mb, tags.

        Returns:
            Schedule: Updated schedule.
        """
        body = {k: v for k, v in kwargs.items() if v is not None}
        response = await self.client.put(f"schedules/{schedule_id}", json=body)
        return Schedule.from_dict(response)

    async def delete(self, schedule_id: str) -> None:
        """
        Delete a schedule. Stops any running daemons in the background.

        Args:
            schedule_id: Schedule identifier.

        Raises:
            FleeksResourceNotFoundError: Schedule not found.
        """
        try:
            await self.client.delete(f"schedules/{schedule_id}")
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Schedule '{schedule_id}' not found"
                )
            raise

    # ── DAEMON LIFECYCLE ────────────────────────────────────

    async def start(self, schedule_id: str) -> ScheduleStartResult:
        """
        Start a schedule / provision its daemon.

        For always_on: provisions a container + starts OpenClaw Gateway.
        For cron/interval: activates the schedule in Celery Beat.
        For manual: triggers immediate one-shot execution.

        Returns immediately — use ``status()`` to poll for readiness.

        Args:
            schedule_id: Schedule identifier.

        Returns:
            ScheduleStartResult: Contains daemon_id and initial status.

        Raises:
            FleeksAPIError: On 402 (quota exceeded) or 409 (already running).
        """
        response = await self.client.post(f"schedules/{schedule_id}/start")
        return ScheduleStartResult.from_dict(response)

    async def stop(
        self,
        schedule_id: str,
        graceful: bool = True,
    ) -> Dict[str, Any]:
        """
        Stop a running schedule / teardown daemon.

        Args:
            schedule_id: Schedule identifier.
            graceful: Attempt graceful shutdown (default: True).

        Returns:
            dict: Stop confirmation with status.
        """
        params = {"graceful": str(graceful).lower()}
        return await self.client.post(
            f"schedules/{schedule_id}/stop",
            json={"graceful": graceful},
        )

    async def pause(self, schedule_id: str) -> Dict[str, Any]:
        """
        Pause a schedule. The daemon stays alive but stops processing.

        Returns:
            dict: ``{"status": "paused", "schedule_id": "..."}``
        """
        return await self.client.post(f"schedules/{schedule_id}/pause")

    async def resume(self, schedule_id: str) -> Dict[str, Any]:
        """
        Resume a paused schedule.

        Returns:
            dict: ``{"status": "active", "schedule_id": "..."}``
        """
        return await self.client.post(f"schedules/{schedule_id}/resume")

    # ── OBSERVABILITY ───────────────────────────────────────

    async def status(self, schedule_id: str) -> DaemonStatusInfo:
        """
        Get daemon runtime status (health, uptime, resource usage).

        Args:
            schedule_id: Schedule identifier.

        Returns:
            DaemonStatusInfo: Full runtime info including ``project_id``
                and ``user_id`` (added in backend 2026-03-10 update).

        Note:
            The ``start()`` method now provisions a full workspace via
            ``EnvironmentManager`` and auto-creates an ``agent_workspace``
            project if none is linked.  The ``project_id`` returned here
            corresponds to that workspace.
        """
        response = await self.client.get(f"schedules/{schedule_id}/status")
        return DaemonStatusInfo.from_dict(response)

    async def logs(
        self,
        schedule_id: str,
        tail: int = 100,
    ) -> DaemonLogs:
        """
        Get daemon logs.

        Args:
            schedule_id: Schedule identifier.
            tail: Number of log lines to retrieve (default: 100).

        Returns:
            DaemonLogs: Log output.
        """
        params = {"tail": str(tail)}
        response = await self.client.get(
            f"schedules/{schedule_id}/logs", params=params
        )
        return DaemonLogs.from_dict(response)

    # ── QUOTA ───────────────────────────────────────────────

    async def quota(self) -> QuotaUsage:
        """
        Get agent-hours quota usage for the current billing period.

        Returns:
            QuotaUsage: Usage metrics, counters, and billing period.

        Example:
            >>> quota = await client.schedules.quota()
            >>> print(f"Used: {quota.agent_hours.used}h / {quota.agent_hours.limit}h")
            >>> if quota.is_warning:
            ...     print("⚠ Approaching limit!")
        """
        response = await self.client.get("schedules/quota")
        return QuotaUsage.from_dict(response)

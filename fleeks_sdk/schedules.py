"""
Schedule management for the Fleeks SDK.

Matches backend endpoints in app/api/api_v1/endpoints/sdk/agent_schedules.py

Endpoints:
    POST   /sdk/schedules/                  — Create agent schedule
    GET    /sdk/schedules/                  — List user's schedules
    GET    /sdk/schedules/{id}              — Get schedule details
    PUT    /sdk/schedules/{id}              — Update schedule
    DELETE /sdk/schedules/{id}              — Delete schedule
    POST   /sdk/schedules/{id}/start        — Start schedule (provision daemon)
    POST   /sdk/schedules/{id}/stop         — Stop schedule (teardown daemon)
    POST   /sdk/schedules/{id}/pause        — Pause schedule
    POST   /sdk/schedules/{id}/resume       — Resume schedule
    GET    /sdk/schedules/{id}/status       — Get daemon runtime status
    GET    /sdk/schedules/{id}/logs         — Get daemon logs
    GET    /sdk/schedules/quota             — Get agent-hours quota usage

Always-On Dashboards (backend release 2026-04-28):
    PUT    /sdk/schedules/{id}/dashboard    — Persist dashboard metadata
    POST   /sdk/schedules/{id}/message      — Push a message into the inbox
    GET    /sdk/schedules/{id}/messages     — Read pending message tail
"""

import uuid
from typing import Dict, Any, List, Optional, AsyncIterator
from .models import (
    Schedule,
    ScheduleList,
    ScheduleStartResult,
    DaemonStatusInfo,
    DaemonLogs,
    QuotaUsage,
    Message,
    MessageSource,
)
from .exceptions import (
    FleeksAPIError,
    FleeksResourceNotFoundError,
    FleeksFeatureUnsupportedError,
    FleeksValidationError,
)


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

        response = await self.client.post("schedules/", json=body)
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

        response = await self.client.get("schedules/", params=params)
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

    # ── DASHBOARDS & MESSAGES (backend release 2026-04-28) ───
    #
    # The canonical recommended flow is to run the in-workspace tool
    # ``publish_dashboard(schedule_id, …)`` from inside the always-on agent
    # container — it scaffolds an HTML/JS bundle, starts a static server,
    # then calls :meth:`set_dashboard` for you.
    #
    # The methods below are the *primitives* — useful when you host the
    # dashboard yourself (custom domain, on-prem, etc.) or when you want
    # to drive the agent's inbox programmatically from outside the
    # workspace (operator console, automated webhook, etc.).

    async def set_dashboard(
        self,
        schedule_id: str,
        *,
        url: str,
        port: int,
        path: Optional[str] = None,
        public: bool = False,
    ) -> Schedule:
        """
        Persist dashboard metadata on the schedule row.

        Endpoint: ``PUT /sdk/schedules/{id}/dashboard``

        Args:
            schedule_id: Schedule identifier.
            url:    Public dashboard URL (e.g.
                    ``"https://preview.fleeks.ai/<wid>/proxy/8080/"``).
            port:   Port the static server listens on inside the workspace.
            path:   Optional path prefix (e.g. ``"/dashboard"``).
            public: When ``True``, the dashboard is intended for end-users.
                    Use a **scoped, message-only** API key with this flag —
                    the key is embedded in the served HTML so the browser
                    can call ``send_message``.

        Returns:
            Schedule: Updated schedule with the new ``dashboard_*`` fields.

        Raises:
            FleeksFeatureUnsupportedError: Backend predates 2026-04-28.
            FleeksResourceNotFoundError:   Schedule not found.

        Example:
            >>> sched = await client.schedules.set_dashboard(
            ...     "sched_abc",
            ...     url="https://my.acme.io/agent/",
            ...     port=8080,
            ...     public=True,
            ... )
            >>> print(sched.dashboard_url)
        """
        body: Dict[str, Any] = {
            "dashboard_url": url,
            "dashboard_port": int(port),
            "dashboard_public": bool(public),
        }
        if path is not None:
            body["dashboard_path"] = path
        try:
            response = await self.client.put(
                f"schedules/{schedule_id}/dashboard", json=body
            )
        except FleeksAPIError as e:
            self._raise_typed(e, schedule_id)
        return Schedule.from_dict(response)

    async def send_message(
        self,
        schedule_id: str,
        *,
        message: str,
        source: str = MessageSource.OPERATOR.value,
        from_: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Message:
        """
        Push a message into the agent's inbox.

        Endpoint: ``POST /sdk/schedules/{id}/message``

        The server appends to ``agent_schedules.pending_messages`` (capped
        at 500) and best-effort drops a JSON file inside the daemon
        container. The DB row is the source of truth — even if the file
        write fails, the agent picks up the message within ~60s.

        Args:
            schedule_id:     Schedule identifier.
            message:         Message text (1+ chars).
            source:          One of ``"dashboard"``, ``"operator"``, ``"automation"``.
            from_:           Optional free-form sender identifier
                             (e.g. ``"alex@acme.io"``).
            idempotency_key: Optional client-generated key. The SDK auto-
                             generates one when not supplied so retries
                             after transient failures don't double-send.

        Returns:
            Message: The newly-queued message (with server-assigned ``id``
                and ``ts``).

        Raises:
            FleeksValidationError:        Empty message or unknown source.
            FleeksFeatureUnsupportedError: Backend predates 2026-04-28.

        Example:
            >>> msg = await client.schedules.send_message(
            ...     "sched_abc",
            ...     message="Reply to the Smith family.",
            ...     source="operator",
            ...     from_="alex@acme.io",
            ... )
            >>> print(msg.id, msg.status)
        """
        if not message or not message.strip():
            raise FleeksValidationError("message must be non-empty")

        body: Dict[str, Any] = {
            "message": message,
            "source": source,
        }
        if from_ is not None:
            body["from"] = from_

        headers = {
            "Idempotency-Key": idempotency_key or f"msg_{uuid.uuid4().hex}",
        }
        try:
            response = await self.client.post(
                f"schedules/{schedule_id}/message",
                json=body,
                headers=headers,
            )
        except FleeksAPIError as e:
            self._raise_typed(e, schedule_id)
        return Message.from_dict(response)

    async def list_messages(
        self,
        schedule_id: str,
        *,
        since_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Return the pending-message tail for a schedule.

        Endpoint: ``GET /sdk/schedules/{id}/messages``

        The server returns at most 500 messages — treat this as a tail,
        not a complete history. Future backends will offer cursor
        pagination via ``since_id`` / ``limit`` (forwarded today as a
        best-effort hint; older backends ignore them).

        Args:
            schedule_id: Schedule identifier.
            since_id:    Optional cursor — return only messages with id
                         strictly after this one.
            limit:       Optional max number of messages to return.

        Returns:
            list[Message]: Messages in chronological order.

        Raises:
            FleeksFeatureUnsupportedError: Backend predates 2026-04-28.
        """
        params: Dict[str, str] = {}
        if since_id:
            params["since_id"] = since_id
        if limit is not None:
            params["limit"] = str(int(limit))

        try:
            response = await self.client.get(
                f"schedules/{schedule_id}/messages",
                params=params or None,
            )
        except FleeksAPIError as e:
            self._raise_typed(e, schedule_id)

        # The endpoint returns a bare list, but be defensive in case a
        # future backend wraps it in {"messages": [...], "next_cursor": …}.
        items: List[Any]
        if isinstance(response, list):
            items = response
        elif isinstance(response, dict):
            items = response.get("messages") or response.get("data") or []
        else:
            items = []

        out: List[Message] = []
        for item in items:
            if isinstance(item, dict):
                try:
                    out.append(Message.from_dict(item))
                except Exception:
                    continue
        # Client-side filter — best-effort if server didn't honour params.
        if since_id:
            try:
                idx = next(i for i, m in enumerate(out) if m.id == since_id)
                out = out[idx + 1:]
            except StopIteration:
                pass
        if limit is not None and limit > 0:
            out = out[-limit:]
        return out

    # ── helpers ─────────────────────────────────────────────

    @staticmethod
    def _raise_typed(error: FleeksAPIError, schedule_id: str) -> None:
        """Map raw API errors to typed exceptions; never returns."""
        code = error.status_code
        if code == 404:
            raise FleeksResourceNotFoundError(
                f"Schedule '{schedule_id}' not found"
            ) from error
        if code in (405, 501):
            raise FleeksFeatureUnsupportedError(
                "Always-on agent dashboards are not supported by this "
                "Fleeks backend. Required minimum: 2026-04-28 release."
            ) from error
        if code == 422:
            raise FleeksValidationError(str(error)) from error
        raise error

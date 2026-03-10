"""
Automation management for the Fleeks SDK.

Matches backend endpoints in app/api/api_v1/endpoints/sdk/agent_channels.py
(automations are routed under /sdk/automations/).

Endpoints:
    POST   /sdk/automations/                — Create automation trigger
    GET    /sdk/automations/                — List automations
    GET    /sdk/automations/{id}            — Get automation details
    PUT    /sdk/automations/{id}            — Update automation
    DELETE /sdk/automations/{id}            — Remove automation
    POST   /sdk/automations/{id}/test       — Dry-run test with payload
"""

from typing import Dict, Any, List, Optional
from .models import (
    Automation,
    AutomationList,
    AutomationTestResult,
)
from .exceptions import FleeksAPIError, FleeksResourceNotFoundError


class AutomationManager:
    """
    Manager for automation trigger operations.

    Create webhook, GitHub, Slack, and event-based triggers
    that fire agent tasks automatically.

    Example:
        >>> auto = await client.automations.create(
        ...     schedule_id="sched_abc",
        ...     name="Auto-review PRs",
        ...     trigger_type="github_pr",
        ...     event_filter={"action": ["opened"], "base_branch": "main"},
        ...     task_template="Review PR #{{ pr_number }}: {{ pr_title }}",
        ...     context_mapping={
        ...         "pr_number": "pull_request.number",
        ...         "pr_title": "pull_request.title",
        ...     },
        ... )
        >>> print(f"Webhook: {auto.webhook_url}")
    """

    def __init__(self, client):
        self.client = client

    # ── CRUD ────────────────────────────────────────────────

    async def create(
        self,
        schedule_id: str,
        name: str,
        trigger_type: str,
        *,
        description: Optional[str] = None,
        webhook_url: Optional[str] = None,
        event_filter: Optional[Dict[str, Any]] = None,
        task_template: Optional[str] = None,
        context_mapping: Optional[Dict[str, str]] = None,
        cooldown_seconds: int = 0,
        max_triggers_per_hour: int = 60,
    ) -> Automation:
        """
        Create an automation trigger.

        Args:
            schedule_id: Agent schedule to trigger.
            name: Automation name (1-255 chars).
            trigger_type: One of "webhook", "cron", "github_push",
                "github_pr", "github_issue", "slack_mention",
                "email_received", "file_change", "api_call",
                "schedule", "container_event", "custom_event".
            description: Optional description.
            webhook_url: Custom webhook URL (auto-generated if None).
            event_filter: Filter rules to match events.
            task_template: Jinja2 template for the task prompt.
            context_mapping: Map event payload fields to template vars.
            cooldown_seconds: Min seconds between triggers (0-3600).
            max_triggers_per_hour: Max fires per hour (1-1000).

        Returns:
            Automation: Created automation with webhook_url and secret.

        Raises:
            FleeksValidationError: Invalid trigger type or filter.
            FleeksAPIError: On 402 (quota limit).
        """
        body: Dict[str, Any] = {
            "schedule_id": schedule_id,
            "name": name,
            "trigger_type": trigger_type,
            "cooldown_seconds": cooldown_seconds,
            "max_triggers_per_hour": max_triggers_per_hour,
        }
        if description is not None:
            body["description"] = description
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        if event_filter is not None:
            body["event_filter"] = event_filter
        if task_template is not None:
            body["task_template"] = task_template
        if context_mapping is not None:
            body["context_mapping"] = context_mapping

        response = await self.client.post("automations", json=body)
        return Automation.from_dict(response)

    async def list(
        self,
        schedule_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> AutomationList:
        """
        List automations for a schedule.

        Args:
            schedule_id: Schedule identifier.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            AutomationList: Automations and total count.
        """
        params: Dict[str, str] = {
            "schedule_id": schedule_id,
            "limit": str(limit),
            "offset": str(offset),
        }
        response = await self.client.get("automations", params=params)
        return AutomationList.from_dict(response)

    async def get(self, automation_id: str) -> Automation:
        """
        Get automation details.

        Args:
            automation_id: Automation identifier.

        Returns:
            Automation: Full automation details.

        Raises:
            FleeksResourceNotFoundError: Automation not found.
        """
        try:
            response = await self.client.get(f"automations/{automation_id}")
            return Automation.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Automation '{automation_id}' not found"
                )
            raise

    async def update(
        self,
        automation_id: str,
        **kwargs,
    ) -> Automation:
        """
        Update an automation.

        Args:
            automation_id: Automation identifier.
            **kwargs: Fields to update. Accepted keys:
                name, description, event_filter, task_template,
                context_mapping, cooldown_seconds, max_triggers_per_hour.

        Returns:
            Automation: Updated automation.
        """
        body = {k: v for k, v in kwargs.items() if v is not None}
        response = await self.client.put(
            f"automations/{automation_id}", json=body
        )
        return Automation.from_dict(response)

    async def delete(self, automation_id: str) -> None:
        """
        Remove an automation.

        Args:
            automation_id: Automation identifier.

        Raises:
            FleeksResourceNotFoundError: Automation not found.
        """
        try:
            await self.client.delete(f"automations/{automation_id}")
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Automation '{automation_id}' not found"
                )
            raise

    # ── TESTING ─────────────────────────────────────────────

    async def test(
        self,
        automation_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AutomationTestResult:
        """
        Dry-run test an automation trigger with a sample payload.

        Validates event filter matching and renders the task template
        without actually triggering the agent.

        Args:
            automation_id: Automation identifier.
            payload: Sample event payload to test against.

        Returns:
            AutomationTestResult: Rendered task, filter match result, etc.

        Example:
            >>> result = await client.automations.test(
            ...     "auto_abc",
            ...     payload={
            ...         "action": "opened",
            ...         "pull_request": {
            ...             "number": 42,
            ...             "title": "Fix bug",
            ...             "body": "Fixes #123",
            ...         },
            ...     },
            ... )
            >>> print(result.rendered_task)
            >>> print(f"Filter match: {result.event_filter_match}")
        """
        body = payload or {}
        response = await self.client.post(
            f"automations/{automation_id}/test", json=body
        )
        return AutomationTestResult.from_dict(response)

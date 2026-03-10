"""
Channel management for the Fleeks SDK.

Matches backend endpoints in app/api/api_v1/endpoints/sdk/agent_channels.py

Endpoints:
    GET    /sdk/channels/types           — List available channel types
    POST   /sdk/channels/                — Add channel to schedule
    GET    /sdk/channels/                — List channels for a schedule
    GET    /sdk/channels/{id}            — Get channel details
    PUT    /sdk/channels/{id}            — Update channel config
    DELETE /sdk/channels/{id}            — Remove channel
    POST   /sdk/channels/{id}/auth       — Initiate auth flow
    GET    /sdk/channels/{id}/auth/status — Check auth status
    POST   /sdk/channels/{id}/test       — Test channel connection
"""

from typing import Dict, Any, List, Optional
from .models import (
    ChannelTypeInfo,
    Channel,
    ChannelList,
    AuthFlowResult,
)
from .exceptions import FleeksAPIError, FleeksResourceNotFoundError


class ChannelManager:
    """
    Manager for messaging channel operations.

    Connect agents to Slack, Discord, WhatsApp, Telegram, Teams,
    and 10+ other messaging platforms.

    Example:
        >>> # List available channel types
        >>> types = await client.channels.types()
        >>> for ct in types:
        ...     print(f"{ct.type_id}: {ct.auth_flow}")
        >>>
        >>> # Add a Slack channel
        >>> chan = await client.channels.create(
        ...     schedule_id="sched_abc",
        ...     channel_type="slack",
        ...     channel_name="Team Bot",
        ...     credentials={"bot_token": "xoxb-..."},
        ... )
        >>>
        >>> # Initiate OAuth / QR auth
        >>> auth = await client.channels.auth(chan.channel_id)
        >>> print(auth.oauth_url or auth.qr_code_data)
    """

    def __init__(self, client):
        self.client = client

    # ── CHANNEL TYPES ───────────────────────────────────────

    async def types(self) -> List[ChannelTypeInfo]:
        """
        List all supported messaging channel types.

        Returns:
            List[ChannelTypeInfo]: Available channels with required credentials
                and auth flow type.
        """
        response = await self.client.get("channels/types")
        # Response is a list, not wrapped in an object
        if isinstance(response, list):
            return [ChannelTypeInfo.from_dict(ct) for ct in response]
        # Fallback for wrapped response
        items = response.get("data", response) if isinstance(response, dict) else response
        return [ChannelTypeInfo.from_dict(ct) for ct in items]

    # ── CRUD ────────────────────────────────────────────────

    async def create(
        self,
        schedule_id: str,
        channel_type: str,
        *,
        channel_name: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
        route_to_agents: Optional[List[str]] = None,
        default_agent: Optional[str] = None,
        message_filter: Optional[Dict[str, Any]] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
    ) -> Channel:
        """
        Add a messaging channel to an agent schedule.

        Args:
            schedule_id: Agent schedule to connect this channel to.
            channel_type: Channel type (e.g., "slack", "discord", "whatsapp").
            channel_name: Display name for the channel.
            credentials: Channel-specific credentials (bot token, etc.).
            route_to_agents: Specific agents to route messages to.
            default_agent: Default agent for this channel.
            message_filter: Message filter rules (prefix, regex, keywords).
            rate_limit_per_minute: Per-minute rate limit (1-1000).
            rate_limit_per_hour: Per-hour rate limit (1-100000).

        Returns:
            Channel: Created channel.

        Raises:
            FleeksValidationError: Invalid channel_type or credentials.
            FleeksAPIError: On 402 (quota limit).
        """
        body: Dict[str, Any] = {
            "schedule_id": schedule_id,
            "channel_type": channel_type,
            "rate_limit_per_minute": rate_limit_per_minute,
            "rate_limit_per_hour": rate_limit_per_hour,
        }
        if channel_name is not None:
            body["channel_name"] = channel_name
        if credentials is not None:
            body["credentials"] = credentials
        if route_to_agents is not None:
            body["route_to_agents"] = route_to_agents
        if default_agent is not None:
            body["default_agent"] = default_agent
        if message_filter is not None:
            body["message_filter"] = message_filter

        response = await self.client.post("channels", json=body)
        return Channel.from_dict(response)

    async def list(
        self,
        schedule_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> ChannelList:
        """
        List channels for a schedule.

        Args:
            schedule_id: Schedule identifier.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            ChannelList: Channels and total count.
        """
        params: Dict[str, str] = {
            "schedule_id": schedule_id,
            "limit": str(limit),
            "offset": str(offset),
        }
        response = await self.client.get("channels", params=params)
        return ChannelList.from_dict(response)

    async def get(self, channel_id: str) -> Channel:
        """
        Get channel details.

        Args:
            channel_id: Channel identifier.

        Returns:
            Channel: Full channel details.

        Raises:
            FleeksResourceNotFoundError: Channel not found.
        """
        try:
            response = await self.client.get(f"channels/{channel_id}")
            return Channel.from_dict(response)
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Channel '{channel_id}' not found"
                )
            raise

    async def update(
        self,
        channel_id: str,
        **kwargs,
    ) -> Channel:
        """
        Update channel configuration.

        Args:
            channel_id: Channel identifier.
            **kwargs: Fields to update. Accepted keys:
                channel_name, route_to_agents, default_agent,
                message_filter, rate_limit_per_minute, rate_limit_per_hour.

        Returns:
            Channel: Updated channel.
        """
        body = {k: v for k, v in kwargs.items() if v is not None}
        response = await self.client.put(f"channels/{channel_id}", json=body)
        return Channel.from_dict(response)

    async def delete(self, channel_id: str) -> None:
        """
        Remove a channel.

        Args:
            channel_id: Channel identifier.

        Raises:
            FleeksResourceNotFoundError: Channel not found.
        """
        try:
            await self.client.delete(f"channels/{channel_id}")
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(
                    f"Channel '{channel_id}' not found"
                )
            raise

    # ── AUTH ─────────────────────────────────────────────────

    async def auth(self, channel_id: str) -> AuthFlowResult:
        """
        Initiate the channel authentication flow.

        Returns different data depending on the channel type:
        - **Slack/Teams/Google Chat**: ``auth.oauth_url`` — open in browser.
        - **WhatsApp/Signal**: ``auth.qr_code_data`` — render QR in terminal.
        - **Discord/Telegram**: Token validated immediately.

        Args:
            channel_id: Channel identifier.

        Returns:
            AuthFlowResult: Auth flow data and status.
        """
        response = await self.client.post(f"channels/{channel_id}/auth")
        return AuthFlowResult.from_dict(response)

    async def auth_status(self, channel_id: str) -> AuthFlowResult:
        """
        Check the authentication status of a pending auth flow.

        Args:
            channel_id: Channel identifier.

        Returns:
            AuthFlowResult: Current auth status.
        """
        response = await self.client.get(f"channels/{channel_id}/auth/status")
        return AuthFlowResult.from_dict(response)

    async def test(self, channel_id: str) -> Dict[str, Any]:
        """
        Test a channel connection.

        Sends a test message and verifies connectivity.

        Args:
            channel_id: Channel identifier.

        Returns:
            dict: Test result with status and message.
        """
        return await self.client.post(f"channels/{channel_id}/test")

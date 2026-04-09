"""
AI provider key management for the Fleeks SDK (BYOK — bring your own key).

Matches backend endpoints in app/api/api_v1/endpoints/integrations.py

Endpoints (prefix: /api/v1/integrations):
    PUT    /ai-keys/{provider}  — Store/update an AI provider key
    GET    /ai-keys             — List stored keys (masked)
    DELETE /ai-keys/{provider}  — Remove a stored key
"""

from typing import Dict, Any, List, Optional

SUPPORTED_PROVIDERS = ("openai", "anthropic", "google", "openrouter")

_PREFIX = "/api/v1/integrations"


class AIKeysManager:
    """
    Manage AI provider API keys (BYOK).

    Store your own OpenAI, Anthropic, Google, or OpenRouter keys
    so agents use them instead of the Fleeks platform defaults.

    Example:
        >>> await client.ai_keys.set("openai", "sk-proj-...")
        >>> keys = await client.ai_keys.list()
        >>> for k in keys:
        ...     print(f"{k['provider']}: {k['key_prefix']}")
        >>> await client.ai_keys.delete("openai")
    """

    def __init__(self, client):
        self.client = client

    async def set(self, provider: str, api_key: str) -> Dict[str, Any]:
        """
        Store or update an AI provider API key.

        Args:
            provider: One of openai, anthropic, google, openrouter.
            api_key: The raw API key string.

        Returns:
            Key info dict with provider, is_set, key_prefix, updated_at.
        """
        return await self.client._make_request(
            "PUT",
            f"ai-keys/{provider}",
            json={"api_key": api_key},
            _url_prefix=_PREFIX,
        )

    async def list(self) -> List[Dict[str, Any]]:
        """
        List all stored AI provider keys (masked).

        Returns:
            List of key info dicts.
        """
        return await self.client._make_request(
            "GET",
            "ai-keys",
            _url_prefix=_PREFIX,
        )

    async def delete(self, provider: str) -> Dict[str, Any]:
        """
        Remove a stored AI provider key.

        Args:
            provider: One of openai, anthropic, google, openrouter.

        Returns:
            Confirmation dict with provider, deleted, message.
        """
        return await self.client._make_request(
            "DELETE",
            f"ai-keys/{provider}",
            _url_prefix=_PREFIX,
        )

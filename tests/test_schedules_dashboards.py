"""
Tests for always-on agent dashboards & messages (backend release 2026-04-28).

Covers:
- Schedule model: round-trip the 11 new fields (dashboard_*, pending_messages,
  template_*) — both with and without them present in the payload (back-compat
  with older backends).
- ScheduleManager.set_dashboard / send_message / list_messages.
- Typed-error mapping: 404 → FleeksResourceNotFoundError,
  405/501 → FleeksFeatureUnsupportedError, 422 → FleeksValidationError.
- Idempotency-Key header: auto-generated when not supplied, forwarded when
  the caller provides one.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fleeks_sdk.schedules import ScheduleManager
from fleeks_sdk.models import (
    Schedule,
    Message,
    MessageSource,
    MessageStatus,
)
from fleeks_sdk.exceptions import (
    FleeksAPIError,
    FleeksResourceNotFoundError,
    FleeksFeatureUnsupportedError,
    FleeksValidationError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_client() -> MagicMock:
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


def _base_schedule_payload(**overrides):
    base = {
        "schedule_id": "sched_abc",
        "name": "Realtor Lead Inbox",
        "schedule_type": "always_on",
        "agent_type": "auto",
        "status": "active",
        "created_at": "2026-04-28T12:00:00Z",
        "updated_at": "2026-04-28T12:05:00Z",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schedule model — new fields
# ---------------------------------------------------------------------------

def test_schedule_from_dict_without_new_fields_back_compat():
    """Old backend that doesn't return any of the 2026-04-28 fields."""
    sched = Schedule.from_dict(_base_schedule_payload())
    assert sched.dashboard_url is None
    assert sched.dashboard_port is None
    assert sched.dashboard_path is None
    assert sched.dashboard_public is False
    assert sched.pending_messages == []
    assert sched.template_id is None
    assert sched.template_slug is None
    assert sched.has_dashboard is False
    assert sched.pending_message_count == 0


def test_schedule_from_dict_with_dashboard_and_messages():
    payload = _base_schedule_payload(
        dashboard_url="https://preview.fleeks.ai/1276/proxy/8080/",
        dashboard_port=8080,
        dashboard_path="/dashboard",
        dashboard_public=True,
        pending_messages=[
            {
                "id": "msg_1",
                "message": "Hi",
                "source": "dashboard",
                "from": "alex@acme.io",
                "ts": "2026-04-28T12:30:00Z",
                "status": "queued",
            },
            {
                "id": "msg_2",
                "message": "Bye",
                "source": "operator",
                "from": None,
                "ts": "2026-04-28T12:31:00Z",
                "status": "consumed",
            },
        ],
        template_id=42,
        template_slug="real-estate-lead-bot",
        template_title="Real Estate Lead Bot",
        template_industry="real-estate",
        template_category="sales",
        template_version="1.2.0",
    )
    sched = Schedule.from_dict(payload)
    assert sched.dashboard_url == payload["dashboard_url"]
    assert sched.dashboard_port == 8080
    assert sched.dashboard_path == "/dashboard"
    assert sched.dashboard_public is True
    assert sched.has_dashboard is True
    assert sched.pending_message_count == 2
    assert sched.pending_messages[0].id == "msg_1"
    assert sched.pending_messages[0].source == "dashboard"
    assert sched.pending_messages[0].from_ == "alex@acme.io"
    assert sched.pending_messages[1].status == "consumed"
    assert sched.template_slug == "real-estate-lead-bot"
    assert sched.template_version == "1.2.0"


def test_schedule_skips_garbage_message_entries_resiliently():
    payload = _base_schedule_payload(
        pending_messages=[
            "not-a-dict",
            {"id": "msg_ok", "message": "ok"},
            None,
        ]
    )
    sched = Schedule.from_dict(payload)
    assert sched.pending_message_count == 1
    assert sched.pending_messages[0].id == "msg_ok"


# ---------------------------------------------------------------------------
# Message model
# ---------------------------------------------------------------------------

def test_message_to_dict_uses_wire_field_name_from_not_from_():
    m = Message(
        id="msg_1",
        message="hi",
        source=MessageSource.DASHBOARD.value,
        from_="alex@acme.io",
        ts="2026-04-28T12:00:00Z",
        status=MessageStatus.QUEUED.value,
    )
    d = m.to_dict()
    assert d["from"] == "alex@acme.io"
    assert "from_" not in d
    assert d["source"] == "dashboard"


# ---------------------------------------------------------------------------
# ScheduleManager.set_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_dashboard_happy_path():
    client = _mock_client()
    expected = _base_schedule_payload(
        dashboard_url="https://preview.fleeks.ai/1276/proxy/8080/",
        dashboard_port=8080,
        dashboard_path="/dashboard",
        dashboard_public=True,
    )
    client.put.return_value = expected
    mgr = ScheduleManager(client)

    sched = await mgr.set_dashboard(
        "sched_abc",
        url=expected["dashboard_url"],
        port=8080,
        path="/dashboard",
        public=True,
    )

    client.put.assert_awaited_once()
    args, kwargs = client.put.call_args
    assert args[0] == "schedules/sched_abc/dashboard"
    body = kwargs["json"]
    assert body == {
        "dashboard_url": expected["dashboard_url"],
        "dashboard_port": 8080,
        "dashboard_path": "/dashboard",
        "dashboard_public": True,
    }
    assert sched.dashboard_url == expected["dashboard_url"]
    assert sched.dashboard_public is True


@pytest.mark.asyncio
async def test_set_dashboard_404_raises_resource_not_found():
    client = _mock_client()
    client.put.side_effect = FleeksAPIError("not found", status_code=404)
    mgr = ScheduleManager(client)

    with pytest.raises(FleeksResourceNotFoundError):
        await mgr.set_dashboard("sched_x", url="u", port=8080)


@pytest.mark.asyncio
async def test_set_dashboard_405_raises_feature_unsupported():
    client = _mock_client()
    client.put.side_effect = FleeksAPIError("not allowed", status_code=405)
    mgr = ScheduleManager(client)

    with pytest.raises(FleeksFeatureUnsupportedError):
        await mgr.set_dashboard("sched_x", url="u", port=8080)


# ---------------------------------------------------------------------------
# ScheduleManager.send_message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_happy_path_auto_idempotency_key():
    client = _mock_client()
    client.post.return_value = {
        "id": "msg_99",
        "message": "Reply please",
        "source": "operator",
        "from": "alex@acme.io",
        "ts": "2026-04-28T13:00:00Z",
        "status": "queued",
    }
    mgr = ScheduleManager(client)

    msg = await mgr.send_message(
        "sched_abc",
        message="Reply please",
        source=MessageSource.OPERATOR.value,
        from_="alex@acme.io",
    )

    client.post.assert_awaited_once()
    args, kwargs = client.post.call_args
    assert args[0] == "schedules/sched_abc/message"
    assert kwargs["json"] == {
        "message": "Reply please",
        "source": "operator",
        "from": "alex@acme.io",
    }
    headers = kwargs["headers"]
    assert "Idempotency-Key" in headers
    assert headers["Idempotency-Key"].startswith("msg_")
    assert msg.id == "msg_99"
    assert msg.status == "queued"


@pytest.mark.asyncio
async def test_send_message_forwards_caller_idempotency_key():
    client = _mock_client()
    client.post.return_value = {
        "id": "msg_1",
        "message": "x",
        "source": "operator",
        "from": None,
        "ts": "now",
        "status": "queued",
    }
    mgr = ScheduleManager(client)

    await mgr.send_message(
        "sched_abc",
        message="x",
        idempotency_key="caller-supplied-key-123",
    )

    _, kwargs = client.post.call_args
    assert kwargs["headers"]["Idempotency-Key"] == "caller-supplied-key-123"


@pytest.mark.asyncio
async def test_send_message_empty_message_raises_validation():
    client = _mock_client()
    mgr = ScheduleManager(client)
    with pytest.raises(FleeksValidationError):
        await mgr.send_message("sched_abc", message="")
    with pytest.raises(FleeksValidationError):
        await mgr.send_message("sched_abc", message="   ")
    client.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_message_404_raises_resource_not_found():
    client = _mock_client()
    client.post.side_effect = FleeksAPIError("nope", status_code=404)
    mgr = ScheduleManager(client)
    with pytest.raises(FleeksResourceNotFoundError):
        await mgr.send_message("sched_x", message="hi")


# ---------------------------------------------------------------------------
# ScheduleManager.list_messages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_messages_returns_models():
    client = _mock_client()
    client.get.return_value = [
        {"id": "msg_1", "message": "a", "source": "dashboard"},
        {"id": "msg_2", "message": "b", "source": "operator"},
    ]
    mgr = ScheduleManager(client)
    msgs = await mgr.list_messages("sched_abc")
    assert len(msgs) == 2
    assert all(isinstance(m, Message) for m in msgs)
    args, kwargs = client.get.call_args
    assert args[0] == "schedules/sched_abc/messages"
    # No params → params=None when neither cursor nor limit is supplied.
    assert kwargs.get("params") is None


@pytest.mark.asyncio
async def test_list_messages_forwards_since_id_and_limit_and_filters_locally():
    client = _mock_client()
    client.get.return_value = [
        {"id": "msg_1", "message": "a"},
        {"id": "msg_2", "message": "b"},
        {"id": "msg_3", "message": "c"},
        {"id": "msg_4", "message": "d"},
    ]
    mgr = ScheduleManager(client)
    msgs = await mgr.list_messages("sched_abc", since_id="msg_2", limit=2)
    args, kwargs = client.get.call_args
    assert kwargs["params"] == {"since_id": "msg_2", "limit": "2"}
    # Server returned full list (older backend ignores params); SDK trims.
    assert [m.id for m in msgs] == ["msg_3", "msg_4"]


@pytest.mark.asyncio
async def test_list_messages_handles_dict_envelope_response():
    client = _mock_client()
    client.get.return_value = {
        "messages": [{"id": "msg_1", "message": "a"}],
        "next_cursor": "cur_xyz",
    }
    mgr = ScheduleManager(client)
    msgs = await mgr.list_messages("sched_abc")
    assert [m.id for m in msgs] == ["msg_1"]


@pytest.mark.asyncio
async def test_list_messages_501_raises_feature_unsupported():
    client = _mock_client()
    client.get.side_effect = FleeksAPIError("not implemented", status_code=501)
    mgr = ScheduleManager(client)
    with pytest.raises(FleeksFeatureUnsupportedError):
        await mgr.list_messages("sched_abc")

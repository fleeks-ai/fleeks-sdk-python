"""
examples/publish_dashboard.py — Always-on agent dashboards & messages.

Recommended canonical flow for end-to-end dashboard publishing is the
in-workspace tool ``publish_dashboard(schedule_id, …)`` invoked from inside
the agent's container — it scaffolds an HTML/JS bundle, starts a static
server, and calls the same SDK primitives shown below.

This example demonstrates the *primitives* (set_dashboard, send_message,
list_messages) — useful when you host the dashboard yourself, drive the
agent's inbox programmatically from outside the workspace, or build an
operator console.

Backend requirement: 2026-04-28 always-on agent dashboards release.
"""

import asyncio
import os
import time

from fleeks_sdk import (
    FleeksClient,
    MessageSource,
    FleeksFeatureUnsupportedError,
)


SCHEDULE_ID = os.environ["FLEEKS_SCHEDULE_ID"]   # e.g. "sched_abc"
API_KEY = os.environ["FLEEKS_API_KEY"]            # use a SCOPED key for public dashboards!


async def main() -> None:
    async with FleeksClient(api_key=API_KEY) as client:
        # 1. (optional) point the schedule row at a dashboard URL we host
        #    ourselves. The in-workspace `publish_dashboard` tool does this
        #    for you — only call this directly when self-hosting.
        try:
            sched = await client.schedules.set_dashboard(
                SCHEDULE_ID,
                url="https://preview.fleeks.ai/1276/proxy/8080/",
                port=8080,
                path="/dashboard",
                public=True,  # ⚠ embeds the API key in HTML — use a scoped key.
            )
            print(f"Dashboard set: {sched.dashboard_url} (public={sched.dashboard_public})")
        except FleeksFeatureUnsupportedError:
            print("Backend predates 2026-04-28 release — dashboards not supported.")
            return

        # 2. Push two operator messages into the agent's inbox.
        m1 = await client.schedules.send_message(
            SCHEDULE_ID,
            message="Reply to the Smith family about Tuesday's showing.",
            source=MessageSource.OPERATOR.value,
            from_="alex@acme.io",
        )
        print(f"Queued message: {m1.id} ({m1.status})")

        m2 = await client.schedules.send_message(
            SCHEDULE_ID,
            message="Mark listing 123 Main St as sold.",
            source=MessageSource.AUTOMATION.value,
            idempotency_key=f"sale-123-{int(time.time())}",
        )
        print(f"Queued message: {m2.id} ({m2.status})")

        # 3. Poll the inbox tail.
        for _ in range(3):
            messages = await client.schedules.list_messages(SCHEDULE_ID, limit=10)
            print(f"--- {len(messages)} messages in tail ---")
            for m in messages:
                print(f"  [{m.status:8}] {m.source:10} {m.id}: {m.message[:60]}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())

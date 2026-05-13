"""Live end-to-end audit runner for the Fleeks Python SDK.

This script exercises the SDK against the live Fleeks API and prints a
phase-by-phase PASS / FAIL / SKIP summary similar to the TypeScript audit
handoff. It is intentionally tolerant of backend variation: every phase runs
independently where possible, cleanup is best-effort, and one failure should
not prevent later phases from executing.

Environment variables:
    FLEEKS_LIVE_API_KEY   Required. Live Fleeks API key.
    FLEEKS_BASE_URL       Optional. Defaults to https://api.fleeks.ai
    FLEEKS_AUDIT_TIMEOUT  Optional. Defaults to 90 seconds.

Usage:
    python scripts/live_audit.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fleeks_sdk import FleeksClient
from fleeks_sdk.embeds import EmbedTemplate
from fleeks_sdk.exceptions import FleeksAPIError, FleeksException, WorkspaceNotReadyError


try:
    from tenacity import RetryError as TenacityRetryError
except ImportError:
    TenacityRetryError = None  # type: ignore


PhaseFn = Callable[[], Awaitable[None]]


@dataclass
class PhaseResult:
    name: str
    status: str
    detail: str = ""
    duration_seconds: float = 0.0


@dataclass
class AuditContext:
    client: FleeksClient
    workspace: Any | None = None
    workspace_id: str | None = None
    workspace_container_id: str | None = None
    schedule_id: str | None = None
    embed_id: str | None = None
    preview_session_id: str | None = None
    terminal_job_id: str | None = None
    created_resources: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "workspaces": [],
            "schedules": [],
            "embeds": [],
            "previews": [],
            "terminal_jobs": [],
        }
    )


class LiveAuditRunner:
    def __init__(self, client: FleeksClient) -> None:
        self.client = client
        self.ctx = AuditContext(client=client)
        self.results: List[PhaseResult] = []
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.project_id = f"audit-py-{suffix}"

    async def run(self) -> int:
        phases: List[tuple[str, PhaseFn]] = [
            ("1. API key helpers", self.phase_api_key_helpers),
            ("2. Workspaces", self.phase_workspaces),
            ("3. Files", self.phase_files),
            ("4. Terminal", self.phase_terminal),
            ("5. Containers", self.phase_containers),
            ("6. Agents", self.phase_agents),
            ("7. Schedules", self.phase_schedules),
            ("8. Embeds", self.phase_embeds),
            ("9. Channels", self.phase_channels),
            ("10. Automations", self.phase_automations),
            ("11. Previews", self.phase_previews),
            ("12. Voice", self.phase_voice),
            ("13. AI keys", self.phase_ai_keys),
            ("14. Background jobs", self.phase_background_jobs),
            ("15. Error matrix", self.phase_error_matrix),
            ("16. Cleanup", self.phase_cleanup),
        ]

        for name, phase in phases:
            await self._run_phase(name, phase)

        self._print_summary()
        failed = sum(1 for result in self.results if result.status == "FAIL")
        return 1 if failed else 0

    async def _run_phase(self, name: str, phase: PhaseFn) -> None:
        started = time.perf_counter()
        try:
            await phase()
        except SkipPhase as exc:
            self.results.append(
                PhaseResult(
                    name=name,
                    status="SKIP",
                    detail=str(exc),
                    duration_seconds=time.perf_counter() - started,
                )
            )
            print(f"SKIP  {name}: {exc}")
            return
        except (Exception, asyncio.CancelledError) as exc:
            detail = self._format_exception(exc)
            self.results.append(
                PhaseResult(
                    name=name,
                    status="FAIL",
                    detail=detail,
                    duration_seconds=time.perf_counter() - started,
                )
            )
            print(f"FAIL  {name}: {detail}")
            return

        duration = time.perf_counter() - started
        self.results.append(PhaseResult(name=name, status="PASS", duration_seconds=duration))
        print(f"PASS  {name} ({duration:.2f}s)")

    async def phase_api_key_helpers(self) -> None:
        key_info = await self.client.get_api_key_info()
        usage = await self.client.get_usage_stats()

        if not isinstance(key_info, dict) or not key_info:
            raise AssertionError("get_api_key_info returned no data")
        if not isinstance(usage, dict) or not usage:
            raise AssertionError("get_usage_stats returned no data")

    async def phase_workspaces(self) -> None:
        workspace = await self._create_workspace_with_retry()
        self.ctx.workspace = workspace
        self.ctx.workspace_id = getattr(workspace, "project_id", self.project_id)
        self.ctx.workspace_container_id = getattr(workspace, "container_id", None)
        self.ctx.created_resources["workspaces"].append(self.ctx.workspace_id)

        listed = await self.client.workspaces.list(page_size=50)
        if not any(getattr(item, "project_id", None) == self.ctx.workspace_id for item in listed):
            raise AssertionError(f"workspace {self.ctx.workspace_id} not returned by list()")

        fetched = await self.client.workspaces.get(self.ctx.workspace_id)
        if getattr(fetched, "project_id", None) != self.ctx.workspace_id:
            raise AssertionError("workspaces.get returned the wrong workspace")

    async def phase_files(self) -> None:
        workspace = self._require_workspace()
        path = "audit/live-audit.txt"
        initial_content = "hello from live audit\n"
        updated_content = "updated by live audit\n"

        await workspace.files.create(path=path, content=initial_content)
        listing = await workspace.files.list(path="/", recursive=True)
        entries = getattr(listing, "files", []) or getattr(listing, "items", []) or []
        if not any(getattr(item, "path", None) == path for item in entries):
            raise AssertionError("created file was not returned by files.list")

        content = await workspace.files.read(path)
        if initial_content.strip() not in content:
            raise AssertionError("files.read did not return the uploaded content")

        await workspace.files.update(path=path, content=updated_content)
        reread = await workspace.files.read(path)
        if updated_content.strip() not in reread:
            raise AssertionError("files.update did not persist the new content")

        await workspace.files.delete(path)

    async def phase_terminal(self) -> None:
        workspace = self._require_workspace()
        job = await workspace.terminal.execute("python --version", timeout_seconds=30)
        stdout = getattr(job, "stdout", "") or ""
        stderr = getattr(job, "stderr", "") or ""
        exit_code = getattr(job, "exit_code", None)
        if exit_code not in (0, None):
            raise AssertionError(f"terminal.execute exit_code={exit_code}, stderr={stderr!r}")
        if "Python" not in f"{stdout}\n{stderr}":
            raise AssertionError("terminal.execute did not return the Python version output")

    async def phase_containers(self) -> None:
        workspace = self._require_workspace()

        info = await workspace.containers.get_info()
        if not getattr(info, "container_id", None):
            raise AssertionError("containers.get_info returned no container_id")

        stats = await workspace.containers.get_stats()
        if not hasattr(stats, "cpu_percent"):
            raise AssertionError("containers.get_stats did not return resource stats")

        processes = await workspace.containers.get_processes()
        count = getattr(processes, "process_count", None)
        if count is None:
            count = len(getattr(processes, "processes", []) or [])
        if count is None:
            raise AssertionError("containers.get_processes returned no process information")

    async def phase_agents(self) -> None:
        workspace = self._require_workspace()
        agents = await workspace.agents.list(page_size=10)
        items = getattr(agents, "agents", None)
        if items is None:
            items = agents if isinstance(agents, list) else None
        if items is None:
            raise AssertionError("agents.list returned an unexpected shape")

    async def phase_schedules(self) -> None:
        schedule = await self.client.schedules.create(
            name=f"{self.project_id}-schedule",
            schedule_type="manual",
            default_task="audit ping",
            agent_type="assistant",
        )
        schedule_id = getattr(schedule, "schedule_id", None)
        if not schedule_id:
            raise AssertionError("schedules.create returned no schedule_id")

        self.ctx.schedule_id = schedule_id
        self.ctx.created_resources["schedules"].append(schedule_id)

        listing = await self.client.schedules.list(active_only=False, limit=100)
        items = getattr(listing, "items", None)
        if items is None:
            items = getattr(listing, "schedules", None)
        if items is None:
            raise AssertionError("schedules.list returned an unexpected shape")
        if not any(getattr(item, "schedule_id", None) == schedule_id for item in items):
            raise AssertionError(f"schedule {schedule_id} not returned by schedules.list")

        fetched = await self.client.schedules.get(schedule_id)
        if getattr(fetched, "schedule_id", None) != schedule_id:
            raise AssertionError("schedules.get returned the wrong schedule")

    async def phase_embeds(self) -> None:
        embed = await self.client.embeds.create(
            name=f"{self.project_id}-embed",
            template=EmbedTemplate.PYTHON,
            files={"main.py": "print('hello from embed')\n"},
            allowed_origins=["*"],
            description="Live audit embed",
        )
        embed_id = getattr(embed.info, "id", None) or getattr(embed.info, "embed_id", None)
        if not embed_id:
            raise AssertionError("embeds.create returned no id")

        self.ctx.embed_id = embed_id
        self.ctx.created_resources["embeds"].append(embed_id)

        embeds = await self.client.embeds.list(page_size=100)
        if not any(
            (getattr(item.info, "id", None) or getattr(item.info, "embed_id", None)) == embed_id
            for item in embeds
        ):
            raise AssertionError(f"embed {embed_id} not returned by embeds.list")

        fetched = await self.client.embeds.get(embed_id)
        fetched_id = getattr(fetched.info, "id", None) or getattr(fetched.info, "embed_id", None)
        if fetched_id != embed_id:
            raise AssertionError("embeds.get returned the wrong embed")

    async def phase_channels(self) -> None:
        schedule_id = self.ctx.schedule_id
        if not schedule_id:
            raise SkipPhase("schedule phase did not create a schedule")

        listing = await self.client.channels.list(schedule_id=schedule_id, limit=50)
        items = getattr(listing, "channels", None)
        if items is None:
            items = getattr(listing, "items", None)
        if items is None:
            raise AssertionError("channels.list returned an unexpected shape")

    async def phase_automations(self) -> None:
        schedule_id = self.ctx.schedule_id
        if not schedule_id:
            raise SkipPhase("schedule phase did not create a schedule")

        listing = await self.client.automations.list(schedule_id=schedule_id, limit=50)
        items = getattr(listing, "automations", None)
        if items is None:
            items = getattr(listing, "items", None)
        if items is None:
            raise AssertionError("automations.list returned an unexpected shape")

    async def phase_previews(self) -> None:
        workspace = self._require_workspace()
        project_id = self._workspace_project_id_as_int(workspace)
        if project_id is None:
            info = getattr(workspace, "_info", None) or getattr(workspace, "info", None)
            project_id = getattr(info, "db_project_id", None) if info else None
        if project_id is None:
            raise SkipPhase("preview manager requires an integer project_id (no db_project_id on this workspace)")

        # detect returns 200 with detected_framework="unknown" if probing fails;
        # raises WorkspaceNotReadyError (409) if container is not running.
        try:
            detect = await self.client.previews.detect(project_id)
        except WorkspaceNotReadyError as exc:
            raise SkipPhase(f"container not running for preview detect — {exc.remediation[0] if exc.remediation else 'start workspace container first'}")

        if not hasattr(detect, "detected_framework"):
            raise AssertionError("previews.detect returned an unexpected shape")

        listing = await self.client.previews.list(project_id, limit=20)
        items = getattr(listing, "sessions", None)
        if items is None:
            items = getattr(listing, "items", None)
        if items is None:
            raise AssertionError("previews.list returned an unexpected shape")

    async def phase_voice(self) -> None:
        health = await self.client.voice.health()
        config = await self.client.voice.get_config()
        stats = await self.client.voice.get_stats()
        sessions = await self.client.voice.get_sessions()

        if not isinstance(health, dict):
            raise AssertionError("voice.health returned an unexpected shape")
        if not isinstance(config, dict):
            raise AssertionError("voice.get_config returned an unexpected shape")
        if not isinstance(stats, dict):
            raise AssertionError("voice.get_stats returned an unexpected shape")
        if not isinstance(sessions, list):
            raise AssertionError("voice.get_sessions returned an unexpected shape")

    async def phase_ai_keys(self) -> None:
        keys = await self.client.ai_keys.list()
        if not isinstance(keys, list):
            raise AssertionError("ai_keys.list returned an unexpected shape")

    async def phase_background_jobs(self) -> None:
        workspace = self._require_workspace()
        job = await workspace.terminal.start_background_job(
            "python -c \"import time; print('audit-job-started'); time.sleep(1); print('audit-job-done')\""
        )
        job_id = getattr(job, "job_id", None)
        if not job_id:
            raise AssertionError("start_background_job returned no job_id")

        self.ctx.terminal_job_id = job_id
        self.ctx.created_resources["terminal_jobs"].append(job_id)

        listed = await workspace.terminal.list_jobs()
        jobs = getattr(listed, "jobs", None)
        if jobs is None:
            raise AssertionError("terminal.list_jobs returned an unexpected shape")
        if not any(getattr(item, "job_id", None) == job_id for item in jobs):
            raise AssertionError(f"background job {job_id} not returned by list_jobs")

        fetched = await workspace.terminal.get_job(job_id)
        if getattr(fetched, "job_id", None) != job_id:
            raise AssertionError("terminal.get_job returned the wrong job")

    async def phase_error_matrix(self) -> None:
        # Use a correctly-formatted but non-existent key so the API validates
        # structure first and returns 401 (Unauthorized), not 400 (malformed key).
        bad_key = "fleeks_live_" + "a" * 64 + "_" + "b" * 8
        bad_client = FleeksClient(
            api_key=bad_key,
            base_url=self.client.base_url,
            timeout=self.client.config.timeout,
        )
        try:
            try:
                await bad_client.get_api_key_info()
            except FleeksAPIError as exc:
                if exc.status_code != 401:
                    raise AssertionError(f"expected 401 for invalid key, got {exc.status_code}")
            else:
                raise AssertionError("invalid API key unexpectedly succeeded")
        finally:
            await bad_client.close()

        try:
            await self.client.workspaces.get(f"{self.project_id}-missing")
        except FleeksAPIError as exc:
            if exc.status_code != 404:
                raise AssertionError(f"expected 404 for missing workspace, got {exc.status_code}")
        except FleeksException:
            raise
        else:
            raise AssertionError("missing workspace unexpectedly succeeded")

        workspace = self._require_workspace()
        try:
            await workspace.files.update(path="/", content="bad body")
        except FleeksAPIError as exc:
            if exc.status_code not in (400, 404, 422, 500):
                raise AssertionError(f"expected validation/server failure, got {exc.status_code}")
        else:
            raise AssertionError("invalid files.update unexpectedly succeeded")

    async def phase_cleanup(self) -> None:
        await self._cleanup_resources()

    async def _create_workspace_with_retry(self) -> Any:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                return await self.client.workspaces.create(
                    project_id=self.project_id,
                    template="python",
                )
            except FleeksAPIError as exc:
                last_error = exc
                if exc.status_code != 503 or attempt == 3:
                    raise
                await asyncio.sleep(2 ** attempt)
        if last_error is None:
            raise AssertionError("workspace creation failed without an exception")
        raise last_error

    def _require_workspace(self) -> Any:
        if self.ctx.workspace is None:
            raise SkipPhase("workspace phase did not create a workspace")
        return self.ctx.workspace

    def _workspace_project_id_as_int(self, workspace: Any) -> int | None:
        project_id = getattr(workspace, "project_id", None)
        if isinstance(project_id, int):
            return project_id
        if isinstance(project_id, str) and project_id.isdigit():
            return int(project_id)
        return None

    async def _cleanup_resources(self) -> None:
        if self.ctx.preview_session_id:
            try:
                await self.client.previews.stop(self.ctx.preview_session_id)
            except Exception:
                pass
            self.ctx.preview_session_id = None

        if self.ctx.terminal_job_id and self.ctx.workspace is not None:
            try:
                await self.ctx.workspace.terminal.stop_job(self.ctx.terminal_job_id)
            except Exception:
                pass
            self.ctx.terminal_job_id = None

        while self.ctx.created_resources["embeds"]:
            embed_id = self.ctx.created_resources["embeds"].pop()
            try:
                await self.client.embeds.delete(embed_id)
            except Exception:
                pass

        while self.ctx.created_resources["schedules"]:
            schedule_id = self.ctx.created_resources["schedules"].pop()
            try:
                await self.client.schedules.delete(schedule_id)
            except Exception:
                pass

        while self.ctx.created_resources["workspaces"]:
            workspace_id = self.ctx.created_resources["workspaces"].pop()
            try:
                await self.client.workspaces.delete(workspace_id)
            except Exception:
                pass

    def _print_summary(self) -> None:
        print("\nSummary")
        print("-" * 72)
        for result in self.results:
            detail = f": {result.detail}" if result.detail else ""
            print(
                f"{result.status:<5} {result.name} "
                f"({result.duration_seconds:.2f}s){detail}"
            )

        counts = {
            "PASS": sum(1 for result in self.results if result.status == "PASS"),
            "FAIL": sum(1 for result in self.results if result.status == "FAIL"),
            "SKIP": sum(1 for result in self.results if result.status == "SKIP"),
        }
        print("-" * 72)
        print(
            f"Totals: {counts['PASS']} PASS / {counts['FAIL']} FAIL / {counts['SKIP']} SKIP"
        )

    def _format_exception(self, exc: Exception) -> str:
        # Unwrap tenacity RetryError to reveal the underlying exception
        if TenacityRetryError is not None and isinstance(exc, TenacityRetryError):
            try:
                underlying = exc.last_attempt.exception()
                if underlying is not None:
                    return f"RetryError wrapping: {self._format_exception(underlying)}"
            except Exception:
                pass
            return str(exc)
        if isinstance(exc, FleeksAPIError):
            return f"HTTP {exc.status_code}: {exc}"
        if isinstance(exc, AssertionError):
            return str(exc)
        return f"{exc.__class__.__name__}: {exc}"


class SkipPhase(Exception):
    pass


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise SystemExit(f"Missing required environment variable: {name}")


async def _main() -> int:
    api_key = _require_env("FLEEKS_LIVE_API_KEY")
    base_url = os.getenv("FLEEKS_BASE_URL", "https://api.fleeks.ai")
    timeout = float(os.getenv("FLEEKS_AUDIT_TIMEOUT", "90"))

    client = FleeksClient(api_key=api_key, base_url=base_url, timeout=timeout)
    try:
        runner = LiveAuditRunner(client)
        return await runner.run()
    finally:
        await client.close()


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
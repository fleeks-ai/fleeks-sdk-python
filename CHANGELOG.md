# Changelog

All notable changes to the Fleeks Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2026-05-13

### Fixed

- Live-audited the SDK against `https://api.fleeks.ai` and fixed all audited regressions. Verified with a full end-to-end audit run: `16 PASS / 0 FAIL / 0 SKIP`.
- Added dual auth headers in the core client (`X-API-Key` and `Authorization: Bearer`) for backend routes that require bearer auth.
- Restricted automatic retries to transient transport and rate-limit failures so 4xx API errors are surfaced directly.
- Preserved explicit trailing slashes in the client URL builder and updated schedules, channels, and automations collection routes to use the backend-required trailing-slash form.
- Fixed `files.update()` to send `path` as a query parameter instead of a JSON body field.
- Added empty-body handling for 204 responses to avoid JSON decode failures on successful delete/update calls.
- Updated `get_api_key_info()` and `get_usage_stats()` to use the SDK endpoints with fallback to older backend routes on `404` and `500`.
- Moved voice manager REST calls to `/api/v1/voice/*` and added compatibility for both envelope and bare-list session responses.
- Moved preview manager REST calls to `/api/v1/preview/*`, mapped `409 container_not_running` into `WorkspaceNotReadyError`, and added compatibility for both envelope and bare-list preview listings.
- Exported `WorkspaceNotReadyError` from the public package surface.
- Added `scripts/live_audit.py`, a 16-phase live audit runner covering API key helpers, workspaces, files, terminal, containers, agents, schedules, embeds, channels, automations, previews, voice, AI keys, background jobs, error handling, and cleanup.

### Notes

- Minimum recommended backend version for the new SDK auth and usage endpoints is `2026.05.13+`. The SDK falls back automatically when talking to older backends.

## [0.7.0] - 2026-04-28

### Added — Always-On Agent Custom Dashboards

Tracks backend release `2026_04_28_agent_dashboards_001`. **Minimum backend
version: 2026-04-28.**

- **`Schedule.set_dashboard(id, *, url, port, path=None, public=False)`** —
  persist dashboard metadata on the schedule row
  (`PUT /sdk/schedules/{id}/dashboard`).
- **`Schedule.send_message(id, *, message, source="operator", from_=None,
  idempotency_key=None)`** — push a message into an always-on agent's
  inbox (`POST /sdk/schedules/{id}/message`). Auto-generates an
  `Idempotency-Key` header when none is supplied.
- **`Schedule.list_messages(id, *, since_id=None, limit=None)`** — read
  the pending-message tail (`GET /sdk/schedules/{id}/messages`). Capped at
  500 server-side; treat as a tail, not full history.
- **New `Message` dataclass** + `MessageSource` / `MessageStatus` enums.
  `from` is exposed as `from_` in Python (reserved keyword) and
  serialized as `from` on the wire via `Message.to_dict()`.
- **`Schedule` model** gains 11 optional fields: `dashboard_url`,
  `dashboard_port`, `dashboard_path`, `dashboard_public`,
  `pending_messages`, `template_id`, `template_slug`, `template_title`,
  `template_industry`, `template_category`, `template_version`. Plus
  `Schedule.has_dashboard` and `Schedule.pending_message_count`
  convenience properties. **All additive — fully back-compatible with
  older backends.**
- **`FleeksFeatureUnsupportedError`** — raised when the backend returns
  404 / 405 / 501 on a known dashboards/messages endpoint, indicating an
  outdated backend.
- HTTP `client.get/post/put/patch` now accept an optional `headers=` arg
  for request-scoped headers (used internally for `Idempotency-Key`).
- Example: [`examples/publish_dashboard.py`](examples/publish_dashboard.py).

### Notes

- The canonical end-to-end flow is the in-workspace tool
  `publish_dashboard(schedule_id, …)` invoked from inside the agent's
  container. The new SDK methods are the *primitives* underneath it —
  use them when self-hosting dashboards or driving the inbox from
  outside the workspace.
- When `public=True`, the API key is embedded in the served HTML so the
  browser can call back. Always use a **scoped, message-only** API key
  for end-customer-facing pages and rotate via `/api-keys` if leaked.

## [0.5.2] - 2026-03-30

### Added
- **Deployment Diagnostics** (`deploy.diagnose()`) — Pattern-matches against 13 known failure signatures (npm errors, missing modules, OOM kills, port conflicts, etc.) and returns actionable diagnosis with suggested fixes
- **Deployment Health Checks** (`deploy.health()`) — Inspect Cloud Run revision conditions, traffic split, and URL reachability; returns HEALTHY, DEGRADED, or UNHEALTHY status
- **Runtime Logs** (`deploy.runtime_logs()`) — Fetch live container logs from Cloud Logging (distinct from build-time logs), with severity filtering and limit control
- **Deployment Metrics** (`deploy.metrics()`) — Request count, latency percentiles (p50/p95/p99), error rate, and active instance count over configurable time windows
- **Multi-Service Deploy** (`deploy.multi_deploy()`) — Deploy multi-service projects from a `fleeks.yaml` manifest with auto-injected service-to-service URLs; tier-aware limits
- **Secrets Management** — `deploy.set_secrets()`, `deploy.list_secrets()`, `deploy.delete_secrets()` for GCP Secret Manager integration with auto-injection into Cloud Run
- **New models** — `DiagnoseResult`, `HealthCheckResult`, `RuntimeLogEntry`, `RuntimeLogsResult`, `LatencyMetrics`, `MetricsResult`, `MultiServiceDeployResult`, `MultiDeployResult`

### Changed
- **`ProvisionDbResult`** — Expanded with `database_url`, `db_name`, `db_user`, `db_host`, `db_port` fields; Cloud SQL (PostgreSQL) and Memorystore (Redis) support; all fields now have safe defaults

## [0.4.1] - 2026-02-27

### Changed
- **Agent stop endpoint** — `agents.stop()` now uses `POST /agents/{agent_id}/stop` instead of `DELETE /agents/{agent_id}`, matching updated backend behavior
- **`agents.stop()` return type** — Now returns `AgentStopResponse` (with `agent_id`, `status`, `message`, `handoff_id`) instead of `None`
- **`agents.handoff()`** — Accepts new optional `skills` parameter to specify agent capabilities

### Added
- **`AgentStopResponse` model** — Typed response for agent stop operations
- **`AgentHandoff` new fields** — `workspace_url`, `container_id`, `detected_types`, `active_skills` now included in handoff responses

## [0.4.0] - 2026-02-22

### Added
- **Deployment Management** (`DeployManager`) - Full deployment lifecycle via SDK
  - `deploy.create()` - Trigger new deployments to Fleeks Cloud (Cloud Run)
  - `deploy.status()` - Check deployment progress and health
  - `deploy.logs()` - Retrieve build/runtime logs
  - `deploy.stream_logs()` - Stream real-time deployment logs via SSE
  - `deploy.rollback()` - Rollback to previous Cloud Run revision
  - `deploy.delete()` - Tear down deployment infrastructure
  - `deploy.list()` - List all deployments for a project
- **Deployment Models** - Type-safe response objects
  - `DeploymentStatusEnum` enum (pending, in_progress, succeeded, failed, cancelled)
  - `DeployResponse`, `DeployStatus`, `DeployListItem` dataclasses
- **`WorkspaceInfo.db_project_id`** field for numeric project ID (used by deploy endpoints)
- **`HibernationResponse.state`** convenience property (alias for `.status`)
- **Setup & test script** (`scripts/setup_and_test.py`) for first-time onboarding

### Changed
- **URL normalization** - Client now strips trailing slash (FastAPI convention) instead of adding one
- **Rate-limit errors** now preserve the API `detail` message from the response body
- Updated `__init__.py` exports with all new deployment types

### Security
- Added `debug_deploy.py` to `.gitignore` to prevent credential leakage

## [0.3.0] - 2026-02-16

### Added
- **Embed Management** - Full embed CRUD for shareable code environments
  - `EmbedManager` with `create()`, `list()`, `get()`, `delete()` methods
  - 30+ embed templates (`EmbedTemplate` enum) - React, Python, Flutter, Go, Rust, etc.
  - `EmbedSettings` with layout presets, themes, font size, read-only mode
  - `EmbedAnalytics` for tracking views, sessions, and engagement
  - `EmbedSession` for monitoring active embed sessions
  - `Embed` instance with `.embed_url`, `.iframe_html`, `.markdown_embed` properties
  - Convenience factories: `create_react()`, `create_python()`, `create_jupyter()`, `create_static()`
- **Container Lifecycle Management** - Complete lifecycle control
  - `containers.heartbeat()` - Send heartbeat to prevent idle shutdown
  - `containers.extend_timeout(minutes)` - Extend container timeout
  - `containers.get_lifecycle_status()` - Get lifecycle state and configuration
  - `containers.hibernate()` / `containers.wake()` - Hibernate and resume containers (Pro+)
  - `containers.set_keep_alive(enabled)` - Prevent auto-shutdown (Enterprise)
  - `containers.configure_lifecycle(config)` - Apply lifecycle configuration
  - `LifecycleConfig` with presets: `development()`, `agent_task()`, `always_on()`, `quick_test()`
  - `IdleAction` enum: SHUTDOWN, HIBERNATE, KEEP_ALIVE
  - `TIER_LIMITS` dict for tier-based timeout limits
- **Client `patch()` method** for PATCH HTTP requests

### Changed
- Bumped version to 0.3.0
- Updated `__init__.py` with all new exports
- Upgraded development status classifier to Beta
- Added new keywords: embeds, lifecycle, cloud-ide

## [0.2.0] - 2025-11-14

### Added
- **Preview URL Support** - Instant HTTPS access to workspace applications (major new feature!)
  - `preview_url` and `websocket_url` fields in `WorkspaceInfo`
  - New `workspace.get_preview_url()` method for detailed preview information
  - New `PreviewURLInfo` model for preview URL details
  - Properties `workspace.preview_url` and `workspace.websocket_url` for quick access
  - Comprehensive example in `examples/preview_url_example.py` with Flask, React, WebSocket, and full-stack examples
  - Updated README with Preview URL documentation and new Quick Start example
  - Added CHANGELOG.md to track version history

### Changed
- Updated Quick Start example to showcase preview URL feature
- Enhanced README with preview URL section highlighting zero-config HTTPS access

## [0.1.1] - 2025-11-14

### Fixed
- Fixed README image URL to use absolute path for PyPI rendering

## [0.1.0] - 2025-11-14

### Added
- Initial release of Fleeks Python SDK
- Full async/await support using `httpx` and `aiohttp`
- Workspace management (create, get, list, delete, health check)
- Container operations (info, stats, execute, logs, list processes)
- File operations (create, read, update, delete, list, search, upload, download)
- Terminal operations (execute commands, streaming, background jobs)
- Agent orchestration (execute, status, stream, handoff, cancel)
- Socket.IO streaming client for real-time updates
- Comprehensive error handling and custom exceptions
- Type hints throughout
- Full documentation with examples
- PyPI package published at https://pypi.org/project/fleeks-sdk/

# Changelog

All notable changes to the Fleeks Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

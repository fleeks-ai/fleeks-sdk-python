"""
Embed management for the Fleeks SDK.

Embeds are embeddable, shareable code environments that can be placed on
third-party websites. Unlike regular workspaces, embeds are designed for:
- Public demos and tutorials
- Interactive documentation
- Educational content
- Shareable code samples

Backend endpoints:
- POST /api/v1/embeds/ - Create embed
- GET /api/v1/embeds/ - List user's embeds
- GET /api/v1/embeds/{embed_id} - Get embed details
- PATCH /api/v1/embeds/{embed_id} - Update embed
- DELETE /api/v1/embeds/{embed_id} - Delete embed
- GET /api/v1/embeds/{embed_id}/sessions - List active sessions
- DELETE /api/v1/embeds/{embed_id}/sessions/{session_id} - Terminate session
- GET /api/v1/embeds/{embed_id}/analytics - Get analytics
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class EmbedTemplate(str, Enum):
    """
    Available embed templates.
    
    Each template includes pre-configured language support, starter files,
    and appropriate display mode.
    """
    # Web Frameworks
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    SVELTE = "svelte"
    NEXTJS = "nextjs"
    NUXT = "nuxt"
    ASTRO = "astro"
    SOLID = "solid"
    QWIK = "qwik"
    
    # Backend Languages
    PYTHON = "python"
    NODE = "node"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    KOTLIN = "kotlin"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    
    # Mobile (VNC/Guacamole display)
    FLUTTER = "flutter"
    REACT_NATIVE = "react_native"
    SWIFT = "swift"
    ANDROID = "android"
    
    # Specialized
    JUPYTER = "jupyter"
    UNITY = "unity"
    GODOT = "godot"
    
    # Minimal
    STATIC = "static"
    VANILLA_JS = "vanilla_js"
    DEFAULT = "default"


class DisplayMode(str, Enum):
    """
    How the embed preview is rendered.
    
    Determines the preview panel rendering method based on the type
    of application being developed.
    """
    WEB_PREVIEW = "web_preview"
    """Standard iframe preview for web apps (default)."""
    
    VNC_STREAM = "vnc_stream"
    """VNC-based streaming for desktop apps."""
    
    GUACAMOLE_STREAM = "guacamole_stream"
    """Apache Guacamole streaming for mobile emulators."""
    
    TERMINAL_ONLY = "terminal_only"
    """Terminal output only, no preview panel."""
    
    NOTEBOOK = "notebook"
    """Jupyter notebook interface."""
    
    SPLIT_VIEW = "split_view"
    """Split between editor and terminal output."""


class EmbedLayoutPreset(str, Enum):
    """
    Embed UI layout options.
    
    Controls how the embed panels are arranged for optimal viewing
    of different content types.
    """
    EDITOR_ONLY = "editor-only"
    """Full-width code editor, no preview."""
    
    PREVIEW_ONLY = "preview-only"
    """Full-width preview, no editor (view-only demos)."""
    
    SIDE_BY_SIDE = "side-by-side"
    """Editor left, preview right (default)."""
    
    STACKED = "stacked"
    """Editor top, preview bottom."""
    
    FULL_IDE = "full-ide"
    """Complete IDE with file tree, editor, terminal, preview."""
    
    MOBILE_PREVIEW = "mobile-preview"
    """Phone-sized preview frame."""
    
    TABLET_PREVIEW = "tablet-preview"
    """Tablet-sized preview frame."""


class EmbedTheme(str, Enum):
    """Color themes for embeds."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"  # Follow system preference
    GITHUB_DARK = "github-dark"
    GITHUB_LIGHT = "github-light"
    MONOKAI = "monokai"
    DRACULA = "dracula"
    NORD = "nord"
    SOLARIZED_DARK = "solarized-dark"
    SOLARIZED_LIGHT = "solarized-light"


class EmbedStatus(str, Enum):
    """Embed status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class EmbedSettings:
    """
    Embed display and behavior settings.
    
    Attributes:
        layout: UI layout preset
        theme: Color theme
        read_only: Prevent code editing
        show_terminal: Show terminal panel
        show_file_tree: Show file explorer
        show_console: Show browser console output
        auto_run: Auto-run on load
        hide_navigation: Hide Fleeks branding/nav
        font_size: Editor font size
        tab_size: Tab width in spaces
    """
    layout: EmbedLayoutPreset = EmbedLayoutPreset.SIDE_BY_SIDE
    theme: EmbedTheme = EmbedTheme.DARK
    read_only: bool = False
    show_terminal: bool = True
    show_file_tree: bool = True
    show_console: bool = True
    auto_run: bool = True
    hide_navigation: bool = False
    font_size: int = 14
    tab_size: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API request."""
        return {
            'layout': self.layout.value,
            'theme': self.theme.value,
            'read_only': self.read_only,
            'show_terminal': self.show_terminal,
            'show_file_tree': self.show_file_tree,
            'show_console': self.show_console,
            'auto_run': self.auto_run,
            'hide_navigation': self.hide_navigation,
            'font_size': self.font_size,
            'tab_size': self.tab_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbedSettings':
        """Create from API response dict."""
        return cls(
            layout=EmbedLayoutPreset(data.get('layout', 'side-by-side')),
            theme=EmbedTheme(data.get('theme', 'dark')),
            read_only=data.get('read_only', False),
            show_terminal=data.get('show_terminal', True),
            show_file_tree=data.get('show_file_tree', True),
            show_console=data.get('show_console', True),
            auto_run=data.get('auto_run', True),
            hide_navigation=data.get('hide_navigation', False),
            font_size=data.get('font_size', 14),
            tab_size=data.get('tab_size', 2)
        )


@dataclass
class EmbedFile:
    """
    A file in an embed's initial file set.
    
    Attributes:
        path: File path relative to workspace root
        code: File content
        hidden: Whether to hide from file tree
        active: Whether this file is initially open in editor
    """
    path: str
    code: str
    hidden: bool = False
    active: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API request."""
        return {
            'code': self.code,
            'hidden': self.hidden,
            'active': self.active
        }
    
    @classmethod
    def from_dict(cls, path: str, data: Dict[str, Any]) -> 'EmbedFile':
        """Create from API response dict."""
        if isinstance(data, str):
            return cls(path=path, code=data)
        return cls(
            path=path,
            code=data.get('code', ''),
            hidden=data.get('hidden', False),
            active=data.get('active', False)
        )


@dataclass
class EmbedInfo:
    """
    Embed information - matches backend SDKEmbedResponse.
    
    Attributes:
        id: Unique embed identifier
        name: Embed name
        description: Embed description
        template: Project template
        display_mode: Preview rendering mode
        project_category: Category of the project
        embed_url: URL for embedding
        iframe_html: Ready-to-use iframe HTML
        files: Initial file set
        allowed_origins: Allowed CORS origins
        max_sessions: Maximum concurrent sessions
        session_timeout_minutes: Session timeout
        is_active: Whether embed is active
        is_public: Whether embed is public
        requires_streaming: Whether streaming is required
        owner_tier: Owner's subscription tier
        min_required_tier: Minimum tier required for template
        is_tier_sufficient: Whether owner's tier is sufficient
        total_views: Total embed views
        active_sessions: Active session count
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: str
    name: str
    template: str
    display_mode: str
    project_category: str
    embed_url: str
    iframe_html: str
    files: Dict[str, Any]
    allowed_origins: List[str]
    max_sessions: int
    session_timeout_minutes: int
    is_active: bool
    is_public: bool
    requires_streaming: bool
    owner_tier: str
    min_required_tier: str
    is_tier_sufficient: bool
    created_at: str
    updated_at: str
    description: Optional[str] = None
    total_views: Optional[int] = None
    active_sessions: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbedInfo':
        """Create from API response dict."""
        # Handle datetime conversion
        created_at = data.get('created_at', '')
        updated_at = data.get('updated_at', created_at)
        if hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()
        if hasattr(updated_at, 'isoformat'):
            updated_at = updated_at.isoformat()
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            template=data.get('template', 'default'),
            display_mode=data.get('display_mode', 'web_preview'),
            project_category=data.get('project_category', 'other'),
            embed_url=data.get('embed_url', f"https://embed.fleeks.ai/{data['id']}"),
            iframe_html=data.get('iframe_html', ''),
            files=data.get('files', {}),
            allowed_origins=data.get('allowed_origins', ['*']),
            max_sessions=data.get('max_sessions', 100),
            session_timeout_minutes=data.get('session_timeout_minutes', 30),
            is_active=data.get('is_active', True),
            is_public=data.get('is_public', True),
            requires_streaming=data.get('requires_streaming', False),
            owner_tier=data.get('owner_tier', 'FREE'),
            min_required_tier=data.get('min_required_tier', 'FREE'),
            is_tier_sufficient=data.get('is_tier_sufficient', True),
            total_views=data.get('total_views'),
            active_sessions=data.get('active_sessions'),
            created_at=str(created_at),
            updated_at=str(updated_at)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template': self.template,
            'display_mode': self.display_mode,
            'project_category': self.project_category,
            'embed_url': self.embed_url,
            'iframe_html': self.iframe_html,
            'files': self.files,
            'allowed_origins': self.allowed_origins,
            'max_sessions': self.max_sessions,
            'session_timeout_minutes': self.session_timeout_minutes,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'requires_streaming': self.requires_streaming,
            'owner_tier': self.owner_tier,
            'min_required_tier': self.min_required_tier,
            'is_tier_sufficient': self.is_tier_sufficient,
            'total_views': self.total_views,
            'active_sessions': self.active_sessions,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class EmbedSession:
    """
    An active embed session.
    
    Matches backend: SDKEmbedSessionResponse
    
    Attributes:
        session_id: Unique session identifier
        display_mode: Display mode of the session
        status: Session status
        origin_url: Origin URL of the embedding page
        started_at: Session start timestamp
        last_activity_at: Last activity timestamp
        is_streaming: Whether session is streaming
        metrics: Session metrics (dict with int values)
    """
    session_id: str
    display_mode: str
    status: str
    started_at: str
    is_streaming: bool
    metrics: Dict[str, int]
    origin_url: Optional[str] = None
    last_activity_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbedSession':
        """Create from API response dict."""
        # Handle datetime conversion
        started_at = data.get('started_at', '')
        last_activity = data.get('last_activity_at')
        if hasattr(started_at, 'isoformat'):
            started_at = started_at.isoformat()
        if last_activity and hasattr(last_activity, 'isoformat'):
            last_activity = last_activity.isoformat()
        
        return cls(
            session_id=data['session_id'],
            display_mode=data.get('display_mode', 'web_preview'),
            status=data.get('status', 'active'),
            origin_url=data.get('origin_url'),
            started_at=str(started_at),
            last_activity_at=str(last_activity) if last_activity else None,
            is_streaming=data.get('is_streaming', False),
            metrics=data.get('metrics', {})
        )


@dataclass
class EmbedAnalytics:
    """
    Analytics data for an embed.
    
    Attributes:
        embed_id: Embed ID
        period: Analytics period (e.g., "7d", "30d")
        total_views: Total page views
        unique_visitors: Unique visitors
        total_sessions: Total sessions started
        average_session_duration_seconds: Avg session length
        top_origins: Most common embedding domains
        views_by_day: Daily view counts
        sessions_by_day: Daily session counts
    """
    embed_id: str
    period: str
    total_views: int
    unique_visitors: int
    total_sessions: int
    average_session_duration_seconds: float
    top_origins: List[Dict[str, Any]]
    views_by_day: List[Dict[str, Any]]
    sessions_by_day: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbedAnalytics':
        """Create from API response dict."""
        return cls(
            embed_id=data['embed_id'],
            period=data.get('period', '30d'),
            total_views=data.get('total_views', 0),
            unique_visitors=data.get('unique_visitors', 0),
            total_sessions=data.get('total_sessions', 0),
            average_session_duration_seconds=data.get('average_session_duration_seconds', 0),
            top_origins=data.get('top_origins', []),
            views_by_day=data.get('views_by_day', []),
            sessions_by_day=data.get('sessions_by_day', [])
        )


@dataclass
class EmbedStatusChangeResponse:
    """
    Response from embed status change operations (pause, resume, archive).
    
    Matches backend: EmbedStatusChangeResponse
    
    Attributes:
        id: Embed ID
        status: New status (active, paused, archived)
        previous_status: Previous status
        message: Status message
    """
    id: str
    status: str
    previous_status: str
    message: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbedStatusChangeResponse':
        """Create from API response dict."""
        return cls(
            id=data['id'],
            status=data.get('status', 'unknown'),
            previous_status=data.get('previous_status', 'unknown'),
            message=data.get('message', '')
        )


# ============================================================================
# EMBED CLASS
# ============================================================================

class Embed:
    """
    A single embed instance.
    
    Provides methods to manage, update, and analyze an embed.
    
    Attributes:
        client: FleeksClient instance
        id: Embed ID
        info: EmbedInfo with full details
    
    Example:
        >>> embed = await client.embeds.get("emb_abc123")
        >>> print(f"Name: {embed.info.name}")
        >>> print(f"Active sessions: {embed.info.active_sessions}")
        >>> 
        >>> # Get embed URL for iframe
        >>> print(f"Embed URL: {embed.embed_url}")
    """
    
    def __init__(self, client, info: EmbedInfo):
        """
        Initialize embed instance.
        
        Args:
            client: FleeksClient instance
            info: EmbedInfo with embed details
        """
        self.client = client
        self.id = info.id
        self.info = info
    
    @property
    def embed_url(self) -> str:
        """
        URL to embed in iframe.
        
        Returns:
            str: Public embed URL
        
        Example:
            >>> print(embed.embed_url)
            https://embed.fleeks.ai/emb_abc123
        """
        return f"https://embed.fleeks.ai/{self.id}"
    
    @property
    def iframe_html(self) -> str:
        """
        Ready-to-use iframe HTML.
        
        Returns:
            str: HTML iframe element
        
        Example:
            >>> print(embed.iframe_html)
            <iframe src="https://embed.fleeks.ai/emb_abc123" ...></iframe>
        """
        return (
            f'<iframe src="{self.embed_url}" '
            f'width="100%" height="500px" '
            f'frameborder="0" '
            f'allow="clipboard-read; clipboard-write" '
            f'sandbox="allow-scripts allow-same-origin allow-forms allow-popups">'
            f'</iframe>'
        )
    
    @property
    def markdown_embed(self) -> str:
        """
        Markdown embed code for documentation.
        
        Returns:
            str: Markdown/MDX component
        """
        return f'<FleeksEmbed id="{self.id}" />'
    
    async def refresh(self) -> 'Embed':
        """
        Refresh embed info from API.
        
        Returns:
            Embed: Self with updated info
        """
        response = await self.client.get(f'embeds/{self.id}')
        self.info = EmbedInfo.from_dict(response)
        return self
    
    async def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
        allowed_origins: Optional[List[str]] = None,
        settings: Optional[EmbedSettings] = None,
        session_timeout_minutes: Optional[int] = None,
        max_sessions: Optional[int] = None
    ) -> 'Embed':
        """
        Update embed configuration.
        
        Only provided fields will be updated. None values are ignored.
        
        Args:
            name: New embed name
            description: New description
            files: Updated file contents {path: content}
            allowed_origins: Updated CORS origins
            settings: Updated display settings
            session_timeout_minutes: Updated session timeout
            max_sessions: Updated max concurrent sessions
        
        Returns:
            Embed: Self with updated info
        
        Example:
            >>> embed = await embed.update(
            ...     name="Updated Demo",
            ...     files={"src/App.js": new_code}
            ... )
        """
        data = {}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        if files is not None:
            data['files'] = {k: {'code': v} for k, v in files.items()}
        if allowed_origins is not None:
            data['allowed_origins'] = allowed_origins
        if settings is not None:
            data['settings'] = settings.to_dict()
        if session_timeout_minutes is not None:
            data['session_timeout_minutes'] = session_timeout_minutes
        if max_sessions is not None:
            data['max_sessions'] = max_sessions
        
        response = await self.client.patch(f'embeds/{self.id}', json=data)
        self.info = EmbedInfo.from_dict(response)
        return self
    
    async def update_file(self, path: str, content: str) -> 'Embed':
        """
        Update a single file in the embed.
        
        Args:
            path: File path
            content: New file content
        
        Returns:
            Embed: Self with updated info
        """
        return await self.update(files={path: content})
    
    async def get_sessions(self) -> List[EmbedSession]:
        """
        List active sessions for this embed.
        
        Returns:
            List[EmbedSession]: Active sessions
        
        Example:
            >>> sessions = await embed.get_sessions()
            >>> print(f"Active sessions: {len(sessions)}")
            >>> for s in sessions:
            ...     print(f"  {s.origin_url}: started {s.started_at}")
        """
        response = await self.client.get(f'embeds/{self.id}/sessions')
        return [
            EmbedSession.from_dict(s) 
            for s in response.get('sessions', [])
        ]
    
    async def terminate_session(self, session_id: str) -> None:
        """
        Terminate a specific session.
        
        Args:
            session_id: Session ID to terminate
        """
        await self.client.delete(f'embeds/{self.id}/sessions/{session_id}')
    
    async def terminate_all_sessions(self) -> int:
        """
        Terminate all active sessions.
        
        Returns:
            int: Number of sessions terminated
        """
        sessions = await self.get_sessions()
        for session in sessions:
            await self.terminate_session(session.session_id)
        return len(sessions)
    
    async def get_analytics(
        self,
        period: str = "30d"
    ) -> EmbedAnalytics:
        """
        Get analytics for this embed.
        
        Args:
            period: Time period ("7d", "30d", "90d", "1y")
        
        Returns:
            EmbedAnalytics: Analytics data
        
        Example:
            >>> analytics = await embed.get_analytics("30d")
            >>> print(f"Views: {analytics.total_views}")
            >>> print(f"Unique visitors: {analytics.unique_visitors}")
            >>> print(f"Avg session: {analytics.average_session_duration_seconds}s")
        """
        response = await self.client.get(
            f'embeds/{self.id}/analytics',
            params={'period': period}
        )
        return EmbedAnalytics.from_dict(response)
    
    async def pause(self) -> EmbedStatusChangeResponse:
        """
        Pause the embed.
        
        Paused embeds show a placeholder instead of running code.
        Existing sessions are terminated.
        
        Returns:
            EmbedStatusChangeResponse: Status change confirmation
        """
        response = await self.client.post(f'embeds/{self.id}/pause')
        return EmbedStatusChangeResponse.from_dict(response)
    
    async def resume(self) -> EmbedStatusChangeResponse:
        """
        Resume a paused embed.
        
        Returns:
            EmbedStatusChangeResponse: Status change confirmation
        """
        response = await self.client.post(f'embeds/{self.id}/resume')
        return EmbedStatusChangeResponse.from_dict(response)
    
    async def archive(self) -> EmbedStatusChangeResponse:
        """
        Archive the embed.
        
        Archived embeds cannot be accessed. Use for long-term storage
        without deletion.
        
        Returns:
            EmbedStatusChangeResponse: Status change confirmation
        """
        response = await self.client.post(f'embeds/{self.id}/archive')
        return EmbedStatusChangeResponse.from_dict(response)
    
    async def delete(self) -> None:
        """
        Permanently delete this embed.
        
        This terminates all sessions and removes the embed.
        This action cannot be undone.
        """
        await self.client.delete(f'embeds/{self.id}')
    
    async def duplicate(self, new_name: Optional[str] = None) -> 'Embed':
        """
        Create a copy of this embed.
        
        Args:
            new_name: Name for the duplicate (default: "{name} (copy)")
        
        Returns:
            Embed: New embed instance
        """
        response = await self.client.post(
            f'embeds/{self.id}/duplicate',
            json={'name': new_name or f"{self.info.name} (copy)"}
        )
        return Embed(self.client, EmbedInfo.from_dict(response))


# ============================================================================
# EMBED MANAGER
# ============================================================================

class EmbedManager:
    """
    Manager for embed operations.
    
    Accessed via `client.embeds`:
    
    Example:
        >>> async with FleeksClient(api_key="...") as client:
        ...     # Create new embed
        ...     embed = await client.embeds.create(
        ...         name="React Counter",
        ...         template=EmbedTemplate.REACT,
        ...         files={"src/App.js": counter_code}
        ...     )
        ...     print(f"Embed URL: {embed.embed_url}")
        ...     
        ...     # List all embeds
        ...     embeds = await client.embeds.list()
        ...     for e in embeds:
        ...         print(f"{e.info.name}: {e.info.total_views} views")
    """
    
    def __init__(self, client):
        """
        Initialize embed manager.
        
        Args:
            client: FleeksClient instance
        """
        self.client = client
    
    async def create(
        self,
        name: str,
        template: EmbedTemplate = EmbedTemplate.REACT,
        files: Optional[Dict[str, str]] = None,
        allowed_origins: Optional[List[str]] = None,
        display_mode: DisplayMode = DisplayMode.WEB_PREVIEW,
        layout_preset: EmbedLayoutPreset = EmbedLayoutPreset.SIDE_BY_SIDE,
        theme: EmbedTheme = EmbedTheme.DARK,
        session_timeout_minutes: int = 30,
        max_sessions: int = 100,
        read_only: bool = False,
        show_terminal: bool = True,
        show_file_tree: bool = True,
        auto_run: bool = True,
        description: Optional[str] = None
    ) -> Embed:
        """
        Create a new embed.
        
        Args:
            name: Embed name for identification
            template: Project template (react, python, flutter, etc.)
            files: Initial files as {path: content}
            allowed_origins: Allowed CORS origins (["*"] = any domain)
            display_mode: Preview rendering mode
            layout_preset: UI layout preset
            theme: Color theme
            session_timeout_minutes: Auto-cleanup after inactivity (5-60)
            max_sessions: Max concurrent embed sessions (1-1000)
            read_only: Prevent visitors from editing code
            show_terminal: Show terminal panel
            show_file_tree: Show file explorer
            auto_run: Auto-run on embed load
            description: Embed description
        
        Returns:
            Embed: New embed instance
        
        Example:
            >>> embed = await client.embeds.create(
            ...     name="React Counter Demo",
            ...     template=EmbedTemplate.REACT,
            ...     files={
            ...         "src/App.js": '''
            ...             import { useState } from 'react';
            ...             export default function App() {
            ...                 const [count, setCount] = useState(0);
            ...                 return <button onClick={() => setCount(c => c+1)}>
            ...                     Count: {count}
            ...                 </button>;
            ...             }
            ...         '''
            ...     },
            ...     allowed_origins=["https://myblog.com", "https://docs.mysite.com"],
            ...     theme=EmbedTheme.GITHUB_DARK
            ... )
            >>> print(f"Embed URL: {embed.embed_url}")
            >>> print(f"IFrame: {embed.iframe_html}")
        """
        settings = EmbedSettings(
            layout=layout_preset,
            theme=theme,
            read_only=read_only,
            show_terminal=show_terminal,
            show_file_tree=show_file_tree,
            auto_run=auto_run
        )
        
        data = {
            'name': name,
            'template': template.value if isinstance(template, EmbedTemplate) else template,
            'display_mode': display_mode.value if isinstance(display_mode, DisplayMode) else display_mode,
            'allowed_origins': allowed_origins or ['*'],
            'session_timeout_minutes': max(5, min(60, session_timeout_minutes)),
            'max_sessions': max(1, min(1000, max_sessions)),
            'settings': settings.to_dict()
        }
        
        if files:
            data['files'] = files  # Backend expects {path: content_string}
        
        if description:
            data['description'] = description
        
        response = await self.client.post('embeds', json=data)
        return Embed(self.client, EmbedInfo.from_dict(response))
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False,
        template: Optional[EmbedTemplate] = None,
        search: Optional[str] = None
    ) -> List[Embed]:
        """
        List all embeds owned by authenticated user.
        
        Args:
            page: Page number (1-indexed)
            page_size: Results per page (1-100)
            include_inactive: Include inactive embeds (paused/archived)
            template: Filter by template
            search: Search in name and description
        
        Returns:
            List[Embed]: List of embed instances
        
        Example:
            >>> embeds = await client.embeds.list()
            >>> for embed in embeds:
            ...     print(f"{embed.info.name}: {embed.info.active_sessions} active")
            
            >>> # Filter by template
            >>> react_embeds = await client.embeds.list(template=EmbedTemplate.REACT)
        """
        params = {
            'page': page,
            'page_size': min(100, page_size),
            'include_inactive': include_inactive
        }
        if template:
            params['template'] = template.value if isinstance(template, EmbedTemplate) else template
        if search:
            params['search'] = search
        
        response = await self.client.get('embeds', params=params)
        return [
            Embed(self.client, EmbedInfo.from_dict(e))
            for e in response.get('embeds', [])
        ]
    
    async def get(self, embed_id: str) -> Embed:
        """
        Get embed by ID.
        
        Args:
            embed_id: Embed ID
        
        Returns:
            Embed: Embed instance
        
        Raises:
            FleeksResourceNotFoundError: If embed not found
        
        Example:
            >>> embed = await client.embeds.get("emb_abc123")
            >>> print(f"Name: {embed.info.name}")
        """
        response = await self.client.get(f'embeds/{embed_id}')
        return Embed(self.client, EmbedInfo.from_dict(response))
    
    async def delete(self, embed_id: str) -> None:
        """
        Delete embed by ID.
        
        Terminates all active sessions and permanently removes the embed.
        
        Args:
            embed_id: Embed ID to delete
        """
        await self.client.delete(f'embeds/{embed_id}')
    
    async def get_total_analytics(
        self,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics across all embeds.
        
        Args:
            period: Time period ("7d", "30d", "90d", "1y")
        
        Returns:
            dict: Aggregated analytics data
        
        Example:
            >>> analytics = await client.embeds.get_total_analytics("30d")
            >>> print(f"Total views: {analytics['total_views']}")
            >>> print(f"Total embeds: {analytics['embed_count']}")
        """
        response = await self.client.get(
            'embeds/analytics/total',
            params={'period': period}
        )
        return response
    
    # Convenience factory methods for common embed types
    
    async def create_react(
        self,
        name: str,
        files: Dict[str, str],
        **kwargs
    ) -> Embed:
        """Create a React embed with sensible defaults."""
        return await self.create(
            name=name,
            template=EmbedTemplate.REACT,
            files=files,
            **kwargs
        )
    
    async def create_python(
        self,
        name: str,
        files: Dict[str, str],
        **kwargs
    ) -> Embed:
        """Create a Python embed with sensible defaults."""
        return await self.create(
            name=name,
            template=EmbedTemplate.PYTHON,
            files=files,
            layout_preset=EmbedLayoutPreset.STACKED,
            display_mode=DisplayMode.SPLIT_VIEW,
            **kwargs
        )
    
    async def create_jupyter(
        self,
        name: str,
        files: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Embed:
        """Create a Jupyter notebook embed."""
        return await self.create(
            name=name,
            template=EmbedTemplate.JUPYTER,
            files=files,
            display_mode=DisplayMode.NOTEBOOK,
            layout_preset=EmbedLayoutPreset.FULL_IDE,
            show_terminal=False,
            **kwargs
        )
    
    async def create_static(
        self,
        name: str,
        files: Dict[str, str],
        **kwargs
    ) -> Embed:
        """Create a static HTML/CSS/JS embed."""
        return await self.create(
            name=name,
            template=EmbedTemplate.STATIC,
            files=files,
            **kwargs
        )

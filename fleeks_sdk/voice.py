"""
Voice session manager for real-time voice conversations with Fleeks AI agents.

Uses Socket.IO to stream PCM audio to/from the backend Gemini Live API.

Protocol:
    1. Start a voice session linked to an agent session
    2. Stream mic audio as base64-encoded PCM16 16kHz chunks
    3. Receive audio responses as base64 PCM 24kHz + live transcripts
    4. Agent can execute tools mid-conversation
    5. Stop the session when done

Example:
    >>> async with client.voice.session(
    ...     workspace_id="ws_abc",
    ...     agent_session_id="agt_xyz",
    ... ) as vs:
    ...     # Send audio chunk (base64 PCM16 16kHz mono LE)
    ...     await vs.send_audio(audio_b64)
    ...     # Or send text into voice session
    ...     await vs.send_text("What does main.py do?")
"""

import asyncio
import base64
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import socketio

from .config import Config
from .exceptions import FleeksConnectionError, FleeksStreamingError, FleeksException
from .models import (
    VoiceSessionConfig,
    VoiceSessionInfo,
    VoiceAudioResponse,
    VoiceTranscript,
    VoiceToolExecution,
    VoiceEvent,
    VoiceEventType,
    VoiceSessionState,
    VoiceUsage,
)


class VoiceSession:
    """
    An active voice conversation session.

    Created by VoiceManager.session() or VoiceManager.start().
    Provides methods to send audio/text and async-iterate voice events.
    """

    def __init__(
        self,
        session_id: str,
        sio: socketio.AsyncClient,
        event_queue: asyncio.Queue,
    ):
        self.session_id = session_id
        self._sio = sio
        self._event_queue = event_queue
        self._closed = False

    @property
    def is_active(self) -> bool:
        return not self._closed

    async def send_audio(self, audio_b64: str) -> None:
        """
        Send a base64-encoded PCM16 audio chunk (16kHz mono LE).

        Args:
            audio_b64: Base64-encoded PCM16 bytes (~100ms chunk recommended)
        """
        if self._closed:
            raise FleeksStreamingError("Voice session is closed")
        await self._sio.emit("voice_audio_chunk", {
            "session_id": self.session_id,
            "audio": audio_b64,
        })

    async def send_audio_bytes(self, pcm_bytes: bytes) -> None:
        """
        Send raw PCM16 audio bytes (16kHz mono LE). Auto-encodes to base64.

        Args:
            pcm_bytes: Raw PCM16 bytes
        """
        b64 = base64.b64encode(pcm_bytes).decode("ascii")
        await self.send_audio(b64)

    async def send_text(self, text: str) -> None:
        """
        Send text into the active voice session.

        Args:
            text: Text message to send to the agent
        """
        if self._closed:
            raise FleeksStreamingError("Voice session is closed")
        await self._sio.emit("voice_text_input", {
            "session_id": self.session_id,
            "text": text,
        })

    async def mute(self) -> None:
        """Signal mic muted (sends audio_stream_end to Gemini)."""
        if self._closed:
            return
        await self._sio.emit("voice_mute", {
            "session_id": self.session_id,
        })

    async def stop(self) -> None:
        """Stop the voice session."""
        if self._closed:
            return
        self._closed = True
        await self._sio.emit("voice_stop", {
            "session_id": self.session_id,
        })

    async def events(self) -> AsyncIterator[VoiceEvent]:
        """
        Async iterator over voice events (audio, transcripts, tools, errors).

        Yields VoiceEvent objects until the session ends.

        Example:
            >>> async for event in vs.events():
            ...     if event.type == VoiceEventType.AUDIO_RESPONSE:
            ...         play_audio(event.audio_response.audio)
            ...     elif event.type == VoiceEventType.OUTPUT_TRANSCRIPT:
            ...         print(f"Agent: {event.transcript.text}")
        """
        while not self._closed:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                yield event
                if event.type in (VoiceEventType.SESSION_ENDED, VoiceEventType.ERROR):
                    self._closed = True
                    break
            except asyncio.TimeoutError:
                continue

    async def __aenter__(self) -> "VoiceSession":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()


class VoiceManager:
    """
    Manages voice sessions for real-time voice conversations with Fleeks AI agents.

    Provides methods to start voice sessions, stream audio, and receive
    responses via Socket.IO events backed by Gemini 3.1 Flash Live.
    """

    def __init__(self, fleeks_client):
        self._client = fleeks_client
        self._config: Config = fleeks_client.config
        self._sio: Optional[socketio.AsyncClient] = None
        self._connected = False
        self._active_session: Optional[VoiceSession] = None
        self._event_queue: Optional[asyncio.Queue] = None
        self._session_started_future: Optional[asyncio.Future] = None

    # ── REST endpoints ───────────────────────────────────────

    async def get_config(self) -> Dict[str, Any]:
        """
        Get voice configuration (available models, voices, limits).

        Returns:
            Dict with models, voices, limits, and default config.
        """
        return await self._client.get("voice/config")

    async def get_sessions(self) -> List[Dict[str, Any]]:
        """
        List active voice sessions for the current user.

        Returns:
            List of active voice session info dicts.
        """
        result = await self._client.get("voice/sessions")
        return result.get("sessions", [])

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get voice service statistics.

        Returns:
            Dict with active sessions count, total, and capacity info.
        """
        return await self._client.get("voice/stats")

    async def health(self) -> Dict[str, Any]:
        """
        Check voice service health.

        Returns:
            Dict with health status and component checks.
        """
        return await self._client.get("voice/health")

    # ── Socket.IO session management ────────────────────────

    async def _ensure_connected(self) -> None:
        """Ensure Socket.IO connection is established."""
        if self._connected and self._sio:
            return

        self._sio = socketio.AsyncClient(
            reconnection=self._config.auto_reconnect,
            reconnection_attempts=self._config.reconnect_attempts,
            reconnection_delay=self._config.reconnect_delay,
            logger=False,
            engineio_logger=False,
        )

        self._register_voice_handlers()

        try:
            await self._sio.connect(
                self._config.socketio_url,
                auth={"api_key": self._client.api_key},
                namespace=self._config.socketio_namespace,
            )
            self._connected = True
        except Exception as e:
            raise FleeksConnectionError(
                f"Failed to connect for voice session: {e}"
            )

    def _register_voice_handlers(self) -> None:
        """Register Socket.IO event handlers for voice events."""
        if not self._sio:
            return

        @self._sio.on("voice_session_started")
        async def on_session_started(data):
            if self._session_started_future and not self._session_started_future.done():
                self._session_started_future.set_result(data)
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.SESSION_STARTED,
                    session_id=data.get("session_id", ""),
                    session_info=VoiceSessionInfo.from_dict(data),
                ))

        @self._sio.on("voice_audio_response")
        async def on_audio_response(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.AUDIO_RESPONSE,
                    session_id=data.get("session_id", ""),
                    audio_response=VoiceAudioResponse(
                        audio=data.get("audio", ""),
                        mime_type=data.get("mime_type", "audio/pcm;rate=24000"),
                    ),
                ))

        @self._sio.on("voice_input_transcript")
        async def on_input_transcript(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.INPUT_TRANSCRIPT,
                    session_id=data.get("session_id", ""),
                    transcript=VoiceTranscript(
                        text=data.get("text", ""),
                        role="user",
                    ),
                ))

        @self._sio.on("voice_output_transcript")
        async def on_output_transcript(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.OUTPUT_TRANSCRIPT,
                    session_id=data.get("session_id", ""),
                    transcript=VoiceTranscript(
                        text=data.get("text", ""),
                        role="agent",
                    ),
                ))

        @self._sio.on("voice_tool_start")
        async def on_tool_start(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.TOOL_START,
                    session_id=data.get("session_id", ""),
                    tool_execution=VoiceToolExecution(
                        call_id=data.get("call_id", ""),
                        function_name=data.get("function_name", ""),
                        arguments=data.get("arguments", {}),
                        status="running",
                    ),
                ))

        @self._sio.on("voice_tool_result")
        async def on_tool_result(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.TOOL_RESULT,
                    session_id=data.get("session_id", ""),
                    tool_execution=VoiceToolExecution(
                        call_id=data.get("call_id", ""),
                        function_name=data.get("function_name", ""),
                        arguments={},
                        result=data.get("result"),
                        execution_time=data.get("execution_time"),
                        success=data.get("success", True),
                        status="completed" if data.get("success", True) else "failed",
                    ),
                ))

        @self._sio.on("voice_interrupted")
        async def on_interrupted(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.INTERRUPTED,
                    session_id=data.get("session_id", ""),
                ))

        @self._sio.on("voice_state_changed")
        async def on_state_changed(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.STATE_CHANGED,
                    session_id=data.get("session_id", ""),
                    old_state=data.get("old_state"),
                    new_state=data.get("new_state"),
                ))

        @self._sio.on("voice_error")
        async def on_error(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.ERROR,
                    session_id=data.get("session_id", ""),
                    error=data.get("error", "Unknown voice error"),
                ))

        @self._sio.on("voice_session_ended")
        async def on_session_ended(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.SESSION_ENDED,
                    session_id=data.get("session_id", ""),
                ))

        @self._sio.on("voice_usage")
        async def on_usage(data):
            if self._event_queue:
                await self._event_queue.put(VoiceEvent(
                    type=VoiceEventType.USAGE,
                    session_id=data.get("session_id", ""),
                    usage=VoiceUsage(
                        input_tokens=data.get("input_tokens", 0),
                        output_tokens=data.get("output_tokens", 0),
                    ),
                ))

    async def start(
        self,
        agent_session_id: str,
        *,
        voice_name: str = "Kore",
        language: str = "en",
        model: str = "gemini-3.1-flash-live-preview",
        thinking_level: str = "minimal",
        enable_tools: bool = True,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        system_instruction: Optional[str] = None,
        timeout: float = 10.0,
    ) -> VoiceSession:
        """
        Start a new voice session.

        Args:
            agent_session_id: The agent session to attach voice to (required)
            voice_name: Voice to use — "Aoede", "Charon", "Fenrir", "Kore", "Puck"
            language: Language code (default: "en")
            model: Gemini model (default: "gemini-3.1-flash-live-preview")
            thinking_level: "minimal", "low", "medium", or "high"
            enable_tools: Whether the agent can use tools during voice
            workspace_id: Optional workspace context
            project_id: Optional project context
            system_instruction: Optional system instruction override
            timeout: Seconds to wait for session confirmation

        Returns:
            VoiceSession with send_audio(), send_text(), events(), stop()

        Raises:
            FleeksConnectionError: If Socket.IO connection fails
            FleeksStreamingError: If session creation fails or times out
        """
        await self._ensure_connected()

        self._event_queue = asyncio.Queue()

        loop = asyncio.get_event_loop()
        self._session_started_future = loop.create_future()

        # Emit voice_start
        await self._sio.emit("voice_start", {
            "agent_session_id": agent_session_id,
            "voice_name": voice_name,
            "language": language,
            "model": model,
            "thinking_level": thinking_level,
            "enable_tools": enable_tools,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "system_instruction": system_instruction or "",
        })

        # Wait for voice_session_started
        try:
            data = await asyncio.wait_for(
                self._session_started_future, timeout=timeout
            )
        except asyncio.TimeoutError:
            raise FleeksStreamingError(
                "Voice session failed to start within timeout"
            )

        session_id = data.get("session_id", "")
        session = VoiceSession(
            session_id=session_id,
            sio=self._sio,
            event_queue=self._event_queue,
        )
        self._active_session = session
        return session

    def session(
        self,
        agent_session_id: str,
        **kwargs,
    ):
        """
        Context manager for a voice session (auto-stops on exit).

        Usage:
            >>> async with client.voice.session("agt_xyz") as vs:
            ...     await vs.send_audio(chunk)
            ...     async for event in vs.events():
            ...         print(event)
        """
        return _VoiceSessionContext(self, agent_session_id, kwargs)

    async def disconnect(self) -> None:
        """Disconnect voice Socket.IO connection."""
        if self._active_session and self._active_session.is_active:
            await self._active_session.stop()
        self._active_session = None

        if self._sio and self._connected:
            try:
                await self._sio.disconnect()
            except Exception:
                pass
            self._connected = False
            self._sio = None


class _VoiceSessionContext:
    """Async context manager wrapping VoiceManager.start()."""

    def __init__(self, manager: VoiceManager, agent_session_id: str, kwargs: dict):
        self._manager = manager
        self._agent_session_id = agent_session_id
        self._kwargs = kwargs
        self._session: Optional[VoiceSession] = None

    async def __aenter__(self) -> VoiceSession:
        self._session = await self._manager.start(
            self._agent_session_id, **self._kwargs
        )
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session and self._session.is_active:
            await self._session.stop()

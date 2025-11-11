"""
Real-time streaming client for the Fleeks SDK using Socket.IO.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, AsyncIterator
import socketio
from .exceptions import FleeksStreamingError, FleeksConnectionError
from .config import Config


class StreamingClient:
    """
    Socket.IO client for real-time streaming operations.
    
    Handles:
    - File watching
    - Agent execution streaming
    - Terminal output streaming
    - Automatic reconnection
    """
    
    def __init__(self, fleeks_client):
        """Initialize streaming client."""
        self.fleeks_client = fleeks_client
        self.config: Config = fleeks_client.config
        self.sio: Optional[socketio.AsyncClient] = None
        self.connected = False
        
        # Event callbacks
        self._file_watch_callbacks: Dict[str, Callable] = {}
        self._agent_stream_callbacks: Dict[str, Callable] = {}
        self._terminal_stream_callbacks: Dict[str, Callable] = {}
        
        # Active streams
        self._active_file_watches: Dict[str, Dict[str, Any]] = {}
        self._active_agent_streams: Dict[str, Dict[str, Any]] = {}
        self._active_terminal_streams: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self) -> None:
        """Connect to the Socket.IO server."""
        if self.connected:
            return
            
        try:
            self.sio = socketio.AsyncClient(
                reconnection=self.config.auto_reconnect,
                reconnection_attempts=self.config.reconnect_attempts,
                reconnection_delay=self.config.reconnect_delay,
                logger=False,  # Disable socketio logging for cleaner output
                engineio_logger=False
            )
            
            # Register event handlers
            self._register_event_handlers()
            
            # Connect with authentication
            await self.sio.connect(
                self.config.socketio_url,
                auth={'api_key': self.fleeks_client.api_key},
                namespace=self.config.socketio_namespace
            )
            
            self.connected = True
            
        except Exception as e:
            raise FleeksConnectionError(f"Failed to connect to streaming server: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from the Socket.IO server."""
        if not self.connected or not self.sio:
            return
            
        try:
            # Stop all active streams
            await self._stop_all_streams()
            
            # Disconnect
            await self.sio.disconnect()
            self.connected = False
            self.sio = None
            
        except Exception as e:
            # Log the error but don't raise - disconnection should be graceful
            pass
    
    def _register_event_handlers(self) -> None:
        """Register Socket.IO event handlers."""
        if not self.sio:
            return
            
        @self.sio.event
        async def connect():
            self.connected = True
        
        @self.sio.event
        async def disconnect():
            self.connected = False
        
        @self.sio.event
        async def connect_error(data):
            raise FleeksConnectionError(f"Connection error: {data}")
        
        # File watching events
        @self.sio.event
        async def sdk_file_watch_change(data):
            session_id = data.get('session_id')
            if session_id in self._file_watch_callbacks:
                callback = self._file_watch_callbacks[session_id]
                await callback(data)
        
        @self.sio.event
        async def sdk_file_watch_error(data):
            session_id = data.get('session_id')
            if session_id in self._file_watch_callbacks:
                # Create error event
                error_data = {
                    'type': 'error',
                    'message': data.get('error', 'Unknown error'),
                    'session_id': session_id
                }
                callback = self._file_watch_callbacks[session_id]
                await callback(error_data)
        
        # Agent streaming events
        @self.sio.event
        async def sdk_agent_stream_update(data):
            session_id = data.get('session_id')
            if session_id in self._agent_stream_callbacks:
                callback = self._agent_stream_callbacks[session_id]
                await callback(data)
        
        @self.sio.event
        async def sdk_agent_stream_error(data):
            session_id = data.get('session_id')
            if session_id in self._agent_stream_callbacks:
                error_data = {
                    'type': 'error',
                    'message': data.get('error', 'Unknown error'),
                    'session_id': session_id
                }
                callback = self._agent_stream_callbacks[session_id]
                await callback(error_data)
        
        # Terminal streaming events
        @self.sio.event
        async def sdk_terminal_stream_output(data):
            session_id = data.get('session_id')
            if session_id in self._terminal_stream_callbacks:
                callback = self._terminal_stream_callbacks[session_id]
                await callback(data)
        
        @self.sio.event
        async def sdk_terminal_stream_error(data):
            session_id = data.get('session_id')
            if session_id in self._terminal_stream_callbacks:
                error_data = {
                    'type': 'error',
                    'message': data.get('error', 'Unknown error'),
                    'session_id': session_id
                }
                callback = self._terminal_stream_callbacks[session_id]
                await callback(error_data)
    
    async def watch_files(
        self,
        workspace_id: str,
        patterns: Optional[List[str]] = None,
        callback: Optional[Callable] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Watch for file changes in a workspace.
        
        Args:
            workspace_id: The workspace ID
            patterns: File patterns to watch (e.g., ['**/*.py', '**/*.js'])
            callback: Optional callback function for events
            
        Yields:
            File change events
        """
        await self._ensure_connected()
        
        if patterns is None:
            patterns = ['**/*']
        
        # Generate unique session ID
        session_id = f"file_watch_{workspace_id}_{id(self)}"
        
        # Create event queue for yielding
        event_queue = asyncio.Queue()
        
        async def event_handler(data):
            await event_queue.put(data)
            if callback:
                await callback(data)
        
        # Register callback
        self._file_watch_callbacks[session_id] = event_handler
        self._active_file_watches[session_id] = {
            'workspace_id': workspace_id,
            'patterns': patterns
        }
        
        try:
            # Start file watching
            await self.sio.emit('sdk:file_watch:start', {
                'session_id': session_id,
                'workspace_id': workspace_id,
                'patterns': patterns,
                'api_key': self.fleeks_client.api_key
            })
            
            # Yield events as they come
            while session_id in self._file_watch_callbacks:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield event
                    
                    # Check for error events
                    if event.get('type') == 'error':
                        break
                        
                except asyncio.TimeoutError:
                    # Continue waiting for events
                    continue
                    
        finally:
            # Clean up
            await self._stop_file_watch(session_id)
    
    async def stream_agent(
        self,
        agent_id: str,
        callback: Optional[Callable] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream agent execution updates.
        
        Args:
            agent_id: The agent ID
            callback: Optional callback function for events
            
        Yields:
            Agent execution events
        """
        await self._ensure_connected()
        
        # Generate unique session ID
        session_id = f"agent_stream_{agent_id}_{id(self)}"
        
        # Create event queue
        event_queue = asyncio.Queue()
        
        async def event_handler(data):
            await event_queue.put(data)
            if callback:
                await callback(data)
        
        # Register callback
        self._agent_stream_callbacks[session_id] = event_handler
        self._active_agent_streams[session_id] = {'agent_id': agent_id}
        
        try:
            # Start agent streaming
            await self.sio.emit('sdk:agent_stream:start', {
                'session_id': session_id,
                'agent_id': agent_id,
                'api_key': self.fleeks_client.api_key
            })
            
            # Yield events
            while session_id in self._agent_stream_callbacks:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield event
                    
                    # Check for completion or error
                    if event.get('type') in ['completed', 'failed', 'error']:
                        break
                        
                except asyncio.TimeoutError:
                    continue
                    
        finally:
            await self._stop_agent_stream(session_id)
    
    async def stream_terminal(
        self,
        workspace_id: str,
        terminal_session_id: str,
        callback: Optional[Callable] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream terminal output.
        
        Args:
            workspace_id: The workspace ID
            terminal_session_id: The terminal session ID
            callback: Optional callback function for events
            
        Yields:
            Terminal output events
        """
        await self._ensure_connected()
        
        # Generate unique session ID
        session_id = f"terminal_stream_{workspace_id}_{terminal_session_id}_{id(self)}"
        
        # Create event queue
        event_queue = asyncio.Queue()
        
        async def event_handler(data):
            await event_queue.put(data)
            if callback:
                await callback(data)
        
        # Register callback
        self._terminal_stream_callbacks[session_id] = event_handler
        self._active_terminal_streams[session_id] = {
            'workspace_id': workspace_id,
            'terminal_session_id': terminal_session_id
        }
        
        try:
            # Start terminal streaming
            await self.sio.emit('sdk:terminal_stream:start', {
                'session_id': session_id,
                'workspace_id': workspace_id,
                'terminal_session_id': terminal_session_id,
                'api_key': self.fleeks_client.api_key
            })
            
            # Yield events
            while session_id in self._terminal_stream_callbacks:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield event
                    
                    # Check for session end
                    if event.get('type') == 'session_ended':
                        break
                        
                except asyncio.TimeoutError:
                    continue
                    
        finally:
            await self._stop_terminal_stream(session_id)
    
    async def _ensure_connected(self) -> None:
        """Ensure the client is connected."""
        if not self.connected:
            await self.connect()
    
    async def _stop_file_watch(self, session_id: str) -> None:
        """Stop a file watch session."""
        if session_id in self._file_watch_callbacks:
            if self.sio and self.connected:
                try:
                    await self.sio.emit('sdk:file_watch:stop', {
                        'session_id': session_id,
                        'api_key': self.fleeks_client.api_key
                    })
                except:
                    pass  # Ignore errors during cleanup
            
            del self._file_watch_callbacks[session_id]
            self._active_file_watches.pop(session_id, None)
    
    async def _stop_agent_stream(self, session_id: str) -> None:
        """Stop an agent stream session."""
        if session_id in self._agent_stream_callbacks:
            if self.sio and self.connected:
                try:
                    await self.sio.emit('sdk:agent_stream:stop', {
                        'session_id': session_id,
                        'api_key': self.fleeks_client.api_key
                    })
                except:
                    pass
            
            del self._agent_stream_callbacks[session_id]
            self._active_agent_streams.pop(session_id, None)
    
    async def _stop_terminal_stream(self, session_id: str) -> None:
        """Stop a terminal stream session."""
        if session_id in self._terminal_stream_callbacks:
            if self.sio and self.connected:
                try:
                    await self.sio.emit('sdk:terminal_stream:stop', {
                        'session_id': session_id,
                        'api_key': self.fleeks_client.api_key
                    })
                except:
                    pass
            
            del self._terminal_stream_callbacks[session_id]
            self._active_terminal_streams.pop(session_id, None)
    
    async def _stop_all_streams(self) -> None:
        """Stop all active streams."""
        # Stop file watches
        for session_id in list(self._file_watch_callbacks.keys()):
            await self._stop_file_watch(session_id)
        
        # Stop agent streams
        for session_id in list(self._agent_stream_callbacks.keys()):
            await self._stop_agent_stream(session_id)
        
        # Stop terminal streams
        for session_id in list(self._terminal_stream_callbacks.keys()):
            await self._stop_terminal_stream(session_id)
    
    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self.connected
    
    def get_active_streams(self) -> Dict[str, Any]:
        """Get information about active streams."""
        return {
            'file_watches': len(self._active_file_watches),
            'agent_streams': len(self._active_agent_streams),
            'terminal_streams': len(self._active_terminal_streams),
            'connected': self.connected
        }
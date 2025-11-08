"""
WebSocket connection management for EV Simulator
"""

import asyncio
import websockets
import json
import logging
from typing import Optional, Callable, Dict, Any
from config import CONNECTION_TIMEOUT, RECONNECT_ATTEMPTS

class WebSocketHandler:
    """Handles WebSocket connections and message communication"""
    
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.uri: str = ""
        self.connected: bool = False
        self.message_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        self.logger = logging.getLogger(__name__)
        
    def set_message_callback(self, callback: Callable[[str], None]):
        """Set callback for received messages"""
        self.message_callback = callback
        
    def set_connection_callback(self, callback: Callable[[bool], None]):
        """Set callback for connection status changes"""
        self.connection_callback = callback
        
    async def connect(self, uri: str) -> bool:
        """Connect to WebSocket server"""
        try:
            self.uri = uri
            self.websocket = await websockets.connect(
                uri,
                open_timeout=CONNECTION_TIMEOUT,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            self.logger.info(f"Connected to WebSocket: {uri}")
            
            if self.connection_callback:
                self.connection_callback(True)
                
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket: {e}")
            self.connected = False
            if self.connection_callback:
                self.connection_callback(False)
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        try:
            if self.websocket:
                try:
                    await self.websocket.close()
                except Exception as close_err:
                    # Some client implementations don't expose 'closed'; best effort close
                    self.logger.warning(f"WebSocket close raised: {close_err}")
        finally:
            # Always clear connection state and notify
            self.connected = False
            self.websocket = None
            self.logger.info("Disconnected from WebSocket")
            if self.connection_callback:
                try:
                    self.connection_callback(False)
                except Exception:
                    pass
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send JSON message to WebSocket server"""
        try:
            if not self.connected or not self.websocket:
                self.logger.warning("Not connected to WebSocket")
                return False
                
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            self.logger.info(f"Sent message: {message_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def _listen_for_messages(self):
        """Listen for incoming messages from WebSocket"""
        try:
            async for message in self.websocket:
                if self.message_callback:
                    self.message_callback(message)
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
            self.connected = False
            if self.connection_callback:
                self.connection_callback(False)
        except Exception as e:
            self.logger.error(f"Error listening for messages: {e}")
            self.connected = False
            if self.connection_callback:
                self.connection_callback(False)
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        if not self.connected or not self.websocket:
            return False
        ws = self.websocket
        # Prefer 'closed' if available
        if hasattr(ws, 'closed'):
            try:
                return not ws.closed
            except Exception:
                pass
        # Fallback to 'open' attribute if present
        if hasattr(ws, 'open'):
            try:
                return bool(ws.open)
            except Exception:
                pass
        # As a last resort, rely on internal flag
        return True

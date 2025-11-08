"""
Simple WebSocket test server for EV Simulator testing
"""

import asyncio
import websockets
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EVTestServer:
    """Simple WebSocket server for testing EV Simulator"""
    
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.clients = set()
    
    async def register_client(self, websocket, path):
        """Register new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        # Send welcome message
        welcome_msg = {
            "kind": "serverStatus",
            "payload": {"status": "connected", "message": "EV Test Server Ready"},
            "type": "info"
        }
        await websocket.send(json.dumps(welcome_msg))
    
    async def unregister_client(self, websocket):
        """Unregister client connection"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def handle_message(self, websocket, path):
        """Handle incoming messages from clients"""
        await self.register_client(websocket, path)
        
        try:
            async for message in websocket:
                logger.info(f"Received: {message}")
                
                # Echo the message back with acknowledgment
                try:
                    msg_data = json.loads(message)
                    response = {
                        "kind": "acknowledgment",
                        "payload": {
                            "originalMessage": msg_data,
                            "status": "received",
                            "timestamp": asyncio.get_event_loop().time()
                        },
                        "type": "response"
                    }
                    await websocket.send(json.dumps(response))
                    logger.info(f"Sent acknowledgment for: {msg_data.get('kind', 'unknown')}")
                    
                except json.JSONDecodeError:
                    # Send error response for invalid JSON
                    error_response = {
                        "kind": "error",
                        "payload": {
                            "error": "Invalid JSON format",
                            "originalMessage": message
                        },
                        "type": "error"
                    }
                    await websocket.send(json.dumps(error_response))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting EV Test Server on {self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_message,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        ):
            logger.info("EV Test Server is running...")
            logger.info("Connect your EV Simulator to: ws://localhost:8080")
            logger.info("Press Ctrl+C to stop the server")
            
            # Keep the server running
            await asyncio.Future()  # Run forever

def main():
    """Main entry point"""
    server = EVTestServer()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()

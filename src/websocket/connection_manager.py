"""
WebSocket connection manager for real-time updates
"""
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
from src.utils.logger import logger
from src.monitoring.metrics import active_connections

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by organization
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_info: Dict[WebSocket, Dict] = {}
        # Rate limiting
        self.message_counts: Dict[str, List[datetime]] = {}
        
    async def connect(self, websocket: WebSocket, org_id: str, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Add to organization's connections
        if org_id not in self.active_connections:
            self.active_connections[org_id] = set()
        
        self.active_connections[org_id].add(websocket)
        
        # Store metadata
        self.connection_info[websocket] = {
            'org_id': org_id,
            'user_id': user_id,
            'connected_at': datetime.utcnow(),
            'last_ping': datetime.utcnow()
        }
        
        # Update metrics
        active_connections.inc()
        
        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                'type': 'connection',
                'status': 'connected',
                'message': 'Connected to AI Workflow Agent',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"WebSocket connected: org={org_id}, user={user_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_info:
            info = self.connection_info[websocket]
            org_id = info['org_id']
            
            # Remove from active connections
            if org_id in self.active_connections:
                self.active_connections[org_id].discard(websocket)
                
                # Clean up empty sets
                if not self.active_connections[org_id]:
                    del self.active_connections[org_id]
            
            # Clean up metadata
            del self.connection_info[websocket]
            
            # Update metrics
            active_connections.dec()
            
            logger.info(f"WebSocket disconnected: org={org_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_org(self, org_id: str, message: Dict):
        """Broadcast message to all connections in organization"""
        if org_id not in self.active_connections:
            return
        
        # Add timestamp
        message['timestamp'] = datetime.utcnow().isoformat()
        
        # Send to all connections
        disconnected = []
        
        for websocket in self.active_connections[org_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_email_update(self, org_id: str, email_data: Dict):
        """Send real-time email processing update"""
        message = {
            'type': 'email_update',
            'data': email_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_org(org_id, message)
    
    async def handle_websocket(self, websocket: WebSocket, org_id: str, user_id: str):
        """Handle WebSocket connection lifecycle"""
        try:
            await self.connect(websocket, org_id, user_id)
            
            while True:
                # Receive message
                data = await websocket.receive_json()
                
                # Handle different message types
                if data.get('type') == 'ping':
                    await self.handle_ping(websocket)
                
                elif data.get('type') == 'subscribe':
                    await self.handle_subscription(websocket, data)
                
                elif data.get('type') == 'unsubscribe':
                    await self.handle_unsubscription(websocket, data)
                
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.disconnect(websocket)
    
    async def handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        if websocket in self.connection_info:
            self.connection_info[websocket]['last_ping'] = datetime.utcnow()
        
        await self.send_personal_message(
            websocket,
            {'type': 'pong', 'timestamp': datetime.utcnow().isoformat()}
        )
    
    async def check_connections_health(self):
        """Periodic health check for connections"""
        while True:
            current_time = datetime.utcnow()
            disconnected = []
            
            for websocket, info in self.connection_info.items():
                # Check if connection is stale (no ping in 60 seconds)
                time_diff = (current_time - info['last_ping']).total_seconds()
                
                if time_diff > 60:
                    disconnected.append(websocket)
            
            # Clean up stale connections
            for websocket in disconnected:
                logger.warning("Removing stale connection")
                self.disconnect(websocket)
            
            # Wait 30 seconds before next check
            await asyncio.sleep(30)

# Global connection manager
ws_manager = ConnectionManager()

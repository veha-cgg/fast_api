import json
from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Query
from fastapi import status
from typing import Dict, Optional
from datetime import datetime

from auth.jwt import verify_access_token
from models.users import User
from models.chats import Chat, ChatType
from models.users import UserNotification
from database import engine
from sqlmodel import Session, select


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, list[WebSocket]] = {}
        self.websocket_to_user: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        was_offline = user_id not in self.active_connections or len(self.active_connections.get(user_id, [])) == 0
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.websocket_to_user[websocket] = user_id
        
        # Broadcast online status if user just came online
        if was_offline:
            await self.broadcast_online_status(user_id, True)

    async def disconnect(self, websocket: WebSocket):
        user_id = self.websocket_to_user.get(websocket)
        if user_id:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    # Broadcast offline status
                    await self.broadcast_online_status(user_id, False)
            del self.websocket_to_user[websocket]

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to a specific user (all their connections)"""
        if user_id in self.active_connections:
            message_json = json.dumps(message, default=str)
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    await self.disconnect(connection)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        message_json = json.dumps(message, default=str)
        for user_id, connections in list(self.active_connections.items()):
            for connection in connections[:]: 
                try:
                    await connection.send_text(message_json)
                except Exception:
                    await self.disconnect(connection)

    async def send_chat_notification(self, chat: Chat):
        """Send chat notification to receiver and create notification record"""
        notification_data = {
            "type": "chat_message",
            "chat_id": chat.id,
            "sender_id": chat.sender_id,
            "message": chat.message,
            "created_at": chat.created_at.isoformat() if chat.created_at else None,
        }
        
        if chat.receiver_id:
            await self.send_to_user(chat.receiver_id, {
                "type": "notification",
                "data": notification_data
            })
            
            with Session(engine) as session:
                notification = UserNotification(
                    user_id=chat.receiver_id,
                    title="New Message",
                    message=chat.message[:100],  
                    notification_type="chat",
                    related_chat_id=chat.id,
                    is_read=False
                )
                session.add(notification)
                session.commit()

        if chat.sender_id:
            await self.send_to_user(chat.sender_id, {
                "type": "message_sent",
                "data": notification_data
            })

    def is_user_online(self, user_id: int) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    async def broadcast_online_status(self, user_id: int, is_online: bool):
        """Broadcast user online/offline status to all connected users"""
        await self.broadcast({
            "type": "user_status_update",
            "user_id": user_id,
            "is_online": is_online
        })


router = APIRouter(prefix="/ws", tags=["WebSocket"])
manager = WebSocketManager()


async def get_user_from_token(token: str, session: Session) -> Optional[User]:
    try:
        payload = verify_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            return None
        
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        return user
    except Exception:
        return None


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for chat with authentication"""
    with Session(engine) as session:
        user = await get_user_from_token(token, session)
        
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication")
            return
        
        user.is_online = True
        user.last_seen = datetime.now()
        session.add(user)
        session.commit()
        
        await manager.connect(websocket, user.id)
        
        try:
            await manager.send_to_user(user.id, {
                "type": "connected",
                "message": "Connected to chat",
                "user_id": user.id
            })
            
            while True:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type")
                    
                    if message_type == "ping":
                        await manager.send_to_user(user.id, {"type": "pong"})
                    
                    elif message_type == "chat_message":
                        receiver_id = message_data.get("receiver_id")
                        message_text = message_data.get("message")
                        chat_room_id = message_data.get("chat_room_id")
                        
                        if not message_text:
                            await manager.send_to_user(user.id, {
                                "type": "error",
                                "message": "Message cannot be empty"
                            })
                            continue
                        
                        with Session(engine) as msg_session:
                            chat = Chat(
                                message=message_text,
                                sender_id=user.id,
                                receiver_id=receiver_id,
                                chat_room_id=chat_room_id,
                                message_type=ChatType.PRIVATE if receiver_id else ChatType.GROUP,
                                is_read=False,
                                delivered_at=datetime.now()
                            )
                            msg_session.add(chat)
                            msg_session.commit()
                            msg_session.refresh(chat)
                            
                            await manager.send_chat_notification(chat)
                    
                except json.JSONDecodeError:
                    await manager.send_to_user(user.id, {
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                except Exception as e:
                    await manager.send_to_user(user.id, {
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    })
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            raise e
        finally:
            with Session(engine) as final_session:
                final_user = final_session.get(User, user.id)
                if final_user:
                    final_user.is_online = False
                    final_user.last_seen = datetime.now()
                    final_session.add(final_user)
                    final_session.commit()
            await manager.disconnect(websocket)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))


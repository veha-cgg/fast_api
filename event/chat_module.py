from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from models.chats import Chat, ChatType, ChatRoom, ChatRoomParticipant
from models.users import User, UserNotification
from database import get_session
from auth.dependencies import get_current_active_user
from typing import Annotated

router = APIRouter(prefix="/chat", tags=["websocket"])


@router.get("/messages", response_model=List[dict])
def get_messages(
    receiver_id: Optional[int] = None,
    chat_room_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Get chat messages for the current user"""
    query = select(Chat).where(
        (Chat.sender_id == current_user.id) | (Chat.receiver_id == current_user.id)
    )
    
    if receiver_id:
        query = query.where(
            ((Chat.sender_id == current_user.id) & (Chat.receiver_id == receiver_id)) |
            ((Chat.sender_id == receiver_id) & (Chat.receiver_id == current_user.id))
        )
    
    if chat_room_id:
        query = query.where(Chat.chat_room_id == chat_room_id)
    
    query = query.order_by(Chat.created_at.desc()).limit(limit).offset(offset)
    messages = session.exec(query).all()
    
    return [
        {
            "id": msg.id,
            "message": msg.message,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "chat_room_id": msg.chat_room_id,
            "message_type": msg.message_type,
            "is_read": msg.is_read,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in reversed(messages)
    ]


@router.post("/messages", response_model=dict)
async def create_message(
    message: str,
    receiver_id: Optional[int] = None,
    chat_room_id: Optional[int] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Create a new chat message"""
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    chat = Chat(
        message=message,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        chat_room_id=chat_room_id,
        message_type=ChatType.PRIVATE if receiver_id else ChatType.GROUP,
        is_read=False,
        delivered_at=datetime.now()
    )
    
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    # Send notification via WebSocket if receiver is online
    from websocket import manager
    await manager.send_chat_notification(chat)
    
    return {
        "id": chat.id,
        "message": chat.message,
        "sender_id": chat.sender_id,
        "receiver_id": chat.receiver_id,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
    }


@router.get("/notifications", response_model=List[dict])
def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Get notifications for the current user"""
    query = select(UserNotification).where(UserNotification.user_id == current_user.id)
    
    if unread_only:
        query = query.where(UserNotification.is_read == False)
    
    query = query.order_by(UserNotification.created_at.desc()).limit(limit).offset(offset)
    notifications = session.exec(query).all()
    
    result = []
    for notif in notifications:
        sender_id = None
        if notif.related_chat_id:
            # Get sender_id from the related chat
            chat = session.get(Chat, notif.related_chat_id)
            if chat:
                sender_id = chat.sender_id
        
        result.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "notification_type": notif.notification_type,
            "is_read": notif.is_read,
            "related_chat_id": notif.related_chat_id,
            "sender_id": sender_id,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        })
    
    return result


@router.get("/notifications/unread-count", response_model=dict)
def get_unread_count(
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Get count of unread notifications"""
    count = session.exec(
        select(UserNotification).where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    ).all()
    
    return {"unread_count": len(count)}


@router.put("/notifications/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Mark a notification as read"""
    notification = session.get(UserNotification, notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to mark this notification as read"
        )
    
    notification.is_read = True
    notification.read_at = datetime.now()
    session.add(notification)
    session.commit()
    session.refresh(notification)
    
    return {
        "id": notification.id,
        "is_read": notification.is_read,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
    }


@router.put("/notifications/read-all", response_model=dict)
def mark_all_notifications_read(
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Mark all notifications as read for the current user"""
    notifications = session.exec(
        select(UserNotification).where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    ).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.now()
        session.add(notification)
    
    session.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.get("/users/online", response_model=List[dict])
def get_online_users(
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    session: Session = Depends(get_session)
):
    """Get list of online users"""
    from websocket import manager
    
    online_user_ids = list(manager.active_connections.keys())
    
    if not online_user_ids:
        return []
    
    users = session.exec(
        select(User).where(User.id.in_(online_user_ids))
    ).all()
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_online": True,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        }
        for user in users
    ]


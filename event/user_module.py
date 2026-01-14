from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.users import User, UserCreate, UserUpdate, UserData, UserRole
from database import get_session
from datetime import datetime
from auth import Auth
from auth.dependencies import require_role, get_current_active_user
from typing import Annotated

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/get-users", response_model=list[UserData])  
def get_users(
    current_user: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))],
    session: Session = Depends(get_session)
):
    """Get all users - Admin only"""
    statement = select(User)
    users = session.exec(statement).all()
    return [
        UserData(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]


@router.get("/get-user/{user_id}", response_model=UserData)  
def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))],
    session: Session = Depends(get_session)
):
    """Get a specific user by ID - Admin only"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return UserData(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/create-user", response_model=UserData, status_code=status.HTTP_201_CREATED)  
def create_user(
    user: UserCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))],
    session: Session = Depends(get_session)
):
    """Create a new user - Admin only"""
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user.email} already exists"
        )
    
    hashed_password = Auth.hash_password(user.password)
    
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role if user.role else UserRole.user,
        is_active=user.is_active if user.is_active is not None else True,
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return UserData(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )


@router.put("/update-user/{user_id}", response_model=UserData)  
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.super_admin))],
    session: Session = Depends(get_session)
):
    """Update a user - Admin only"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Check if email is being updated and if it already exists
    if user_update.email and user_update.email != user.email:
        statement = select(User).where(User.email == user_update.email)
        existing_user = session.exec(statement).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_update.email} already exists"
            )
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password"] = Auth.hash_password(update_data["password"])
    
    # Update user fields
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserData(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.delete("/delete-user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)  
def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.super_admin))],
    session: Session = Depends(get_session)
):
    """Delete a user - Admin only"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    session.delete(user)
    session.commit()
    return None


@router.get("/chat-users", response_model=list[dict])  
def get_chat_users(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Session = Depends(get_session)
):
    """Get all users for chat - Available to all authenticated users"""
    from websocket import manager
    
    statement = select(User).where(User.is_active == True)
    users = session.exec(statement).all()
    
    online_user_ids = set(manager.active_connections.keys())
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_online": user.id in online_user_ids,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        }
        for user in users if user.id != current_user.id  # Exclude current user
    ]





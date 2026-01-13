from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.users import User, UserCreate, UserUpdate, UserResponse, UserRole
from database import get_session
from datetime import datetime
from auth import Auth
from auth.dependencies import get_current_user, require_role
from typing import Annotated

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/get-users", response_model=list[UserResponse])  
def get_users(
    session: Session = Depends(get_session)
):
    """Get all users - Admin only"""
    statement = select(User)
    users = session.exec(statement).all()
    return users


@router.get("/get-user/{user_id}", response_model=UserResponse)  
def get_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific user by ID"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user


@router.post("/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)  
def create_user(
    user: UserCreate,
    session: Session = Depends(get_session)
):
    """Create a new user"""
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
        role=user.role,
        is_active=user.is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@router.put("/update-user/{user_id}", response_model=UserResponse)  
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session)
):
    """Update a user"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    if user_update.email and user_update.email != user.email:
        statement = select(User).where(User.email == user_update.email)
        existing_user = session.exec(statement).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_update.email} already exists"
            )
    
    user_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in user_data and user_data["password"]:
        user_data["password"] = Auth.hash_password(user_data["password"])
    
    for field, value in user_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/delete-user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)  
def delete_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Delete a user"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    session.delete(user)
    session.commit()
    return None


# @router.get("/me", response_model=UserResponse)
# def get_current_user_profile(
#     current_user: Annotated[User, Depends(get_current_user)]
# ) -> UserResponse:
#     """Get current user's profile"""
#     return current_user


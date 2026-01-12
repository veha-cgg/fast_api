from fastapi import APIRouter
from models.users import User, UserCreate, UserUpdate, UserDelete
from datetime import datetime
import uuid

router = APIRouter()
router.tags = ["users"]
router.prefix = "/users"

@router.get("")
def get_users() -> list[User]:
    return {"message": "Users fetched successfully"}

@router.post("")
def create_user(user: UserCreate):
    new_user = User(
        id=uuid.uuid4(),
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    return new_user

@router.put("{user_id}")
def update_user(user_id: int, user: UserUpdate):
    user = User(
        id=user_id,
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@router.delete("{user_id}")
def delete_user(user_id: int):
    deleted_user = User(
        id=user_id
    )
    return deleted_user
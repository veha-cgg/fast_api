from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import Annotated
import jwt

from models.users import User, UserResponse, UserData, TokenData
from database import get_session
from .jwt import verify_access_token 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (ValueError, jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        # Log the specific error if needed
        raise credentials_exception
    
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:  
    if current_user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return current_user


def get_current_user_response(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> UserResponse:
    return UserResponse(
        data=UserData(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        ),
        token=TokenData(
            access_token="",
            # refresh_token=None,
            token_type="bearer"
        )
    )

def require_role(*allowed_roles):
    def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        # Extract role values properly
        allowed_role_values = []
        for role in allowed_roles:
            if hasattr(role, 'value'):
                allowed_role_values.append(role.value)
            elif hasattr(role, '__str__'):
                allowed_role_values.append(str(role))
            else:
                allowed_role_values.append(role)
        
        if current_user.role.value not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
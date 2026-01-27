from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import Annotated
from auth.dependencies import get_current_user
from models.users import User, Token, UserResponse, RefreshTokenRequest, UserCreate, UserData, TokenData, LoginRequest
from database import get_session
from auth import Auth
router = APIRouter()

def _authenticate_user(email: str, password: str, session: Session) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password", 
            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is inactive", 
            headers={"WWW-Authenticate": "Bearer"})
    if not Auth.verify_password(plain_password=password, hashed_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password", 
            headers={"WWW-Authenticate": "Bearer"})
    return user

@router.post("/login", response_model=UserResponse, 
             summary="Login with OAuth2 form (for Swagger UI)")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Session = Depends(get_session)) -> UserResponse:
    user = _authenticate_user(form_data.username, form_data.password, session)
    access_token = Auth.create_access_token(data={"sub": user.email, "role": getattr(user.role, "value", user.role)})
    return UserResponse(
        message="Login successfully",
        data=UserData(
            id=user.id, 
            name=user.name,
            email=user.email, 
            role=user.role, 
            is_active=user.is_active,
            created_at=user.created_at, 
            updated_at=user.updated_at), 
            token=TokenData(
                access_token=access_token, 
                token_type="bearer"
            ))

@router.post("/login-json", response_model=UserResponse,
             summary="Login with JSON (for Postman/API clients)")
def login_json(login_data: LoginRequest, session: Session = Depends(get_session)) -> UserResponse:
    """Login endpoint using JSON body (works better with Postman and API clients)"""
    user = _authenticate_user(login_data.email, login_data.password, session)
    access_token = Auth.create_access_token(data={"sub": user.email, "role": getattr(user.role, "value", user.role)})
    return UserResponse(
        message="Login successfully",
        data=UserData(
            id=user.id, 
            name=user.name,
            email=user.email, 
            role=user.role, 
            is_active=user.is_active,
            created_at=user.created_at, 
            updated_at=user.updated_at), 
            token=TokenData(
                access_token=access_token, 
                token_type="bearer"
            ))

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_create: UserCreate,
    session: Session = Depends(get_session)
) -> UserResponse:
    """Register a new user account"""
    existing = session.exec(
        select(User).where(User.email == user_create.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_pwd = Auth.hash_password(user_create.password)

    new_user = User(
        email=user_create.email,
        password=hashed_pwd,
        name=user_create.name,
        role=user_create.role,
        is_active=user_create.is_active,  
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    access_token = Auth.create_access_token(
        data={"sub": new_user.email, "role": getattr(new_user.role, "value", new_user.role)}
    )

    return UserResponse(
        message="Register successfully",
        data=UserData(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        ),
        token=TokenData(
            access_token=access_token,
            token_type="bearer"
        )
    )

@router.post("/refresh", response_model=Token)
def refresh_token(
    token_request: RefreshTokenRequest,
    session: Session = Depends(get_session)
) -> Token:     
    try:
        payload = Auth.verify_refresh_token(token_request.refresh_token)
        email = payload.get("sub")
        if not email:
            raise ValueError("Invalid token subject")

        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise ValueError("User not found")

        new_access = Auth.create_access_token(
            data={"sub": user.email, "role": getattr(user.role, "value", user.role)}
        )
        new_refresh = Auth.create_refresh_token(data={"sub": user.email})

        return Token(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}"
        )

@router.get("/me", response_model=UserData)
def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]    
) -> UserData:
    return UserData(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post("/logout")
def logout() -> dict[str, str]:
    return {
        "message": "Successfully logged out. Please delete tokens on client side."
    }
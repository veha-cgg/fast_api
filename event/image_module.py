from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from models.images import Image, ImageCreate, ImageUpdate, ImageResponse, ImageListResponse
from database import get_session
from auth.dependencies import require_role, oauth2_scheme
from models.users import UserRole, User
from typing import Annotated, Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

router = APIRouter(
    prefix="/images",
    tags=["images"]
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
IMAGES_DIR = STATIC_DIR / "images"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return the URL path"""
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = IMAGES_DIR / unique_filename
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    return f"/static/images/{unique_filename}"

def delete_file(url: str) -> None:
    """Delete file from filesystem"""
    if url.startswith("/static/images/"):
        filename = url.replace("/static/images/", "")
        file_path = IMAGES_DIR / filename
        if file_path.exists():
            os.remove(file_path)

@router.get("/get-images", response_model=ImageListResponse)
def get_images(session: Session = Depends(get_session)):
    """Get all images"""
    statement = select(Image)
    images = session.exec(statement).all()
    return ImageListResponse(
        message="Images fetched successfully",
        data=list(images)   
    )

@router.get("/get-image/{image_id}", response_model=ImageResponse)
def get_image(image_id: int, session: Session = Depends(get_session)):
    """Get a specific image by ID"""
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return ImageResponse(
        message="Image fetched successfully",
        data=image
    )

@router.post("/uploads-image", response_model=ImageResponse,
             status_code=status.HTTP_201_CREATED, dependencies=[Depends(oauth2_scheme)])
async def create_image(
    file: UploadFile = File(...),
    category_id: Optional[int] = Form(None),
    current_user: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))] = None,
    session: Session = Depends(get_session)
):
    """Create a new image by uploading a file"""
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"} 
    file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    file_url = await save_uploaded_file(file)
    
    new_image = Image(
        url=file_url,
        category_id=category_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(new_image)
    session.commit()
    session.refresh(new_image)
    
    return ImageResponse(
        message="Image uploaded successfully",
        data=new_image
    )

@router.put("/update-image/{image_id}", response_model=ImageResponse, 
            dependencies=[Depends(oauth2_scheme)])
async def update_image(
    image_id: int,
    file: Optional[UploadFile] = File(None),
    category_id: Optional[int] = Form(None),
    current_user: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))] = None,
    session: Session = Depends(get_session)
):
    """Update an image"""
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    
    if file:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
        file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        delete_file(image.url)
        
        image.url = await save_uploaded_file(file)
    
    if category_id is not None:
        image.category_id = category_id
    
    image.updated_at = datetime.utcnow()
    session.add(image)
    session.commit()
    session.refresh(image)
    
    return ImageResponse(
        message="Image updated successfully",
        data=image
    )

@router.delete("/delete-image/{image_id}", status_code=status.HTTP_204_NO_CONTENT, 
               dependencies=[Depends(oauth2_scheme)])
def delete_image(
    image_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))] = None,
    session: Session = Depends(get_session)
):
    """Delete an image"""
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    
    delete_file(image.url)
    
    session.delete(image)
    session.commit()
    return None
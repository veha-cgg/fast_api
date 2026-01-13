from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.images import Image, ImageCreate, ImageUpdate, ImageResponse
from database import get_session
from datetime import datetime
from auth.dependencies import require_role, oauth2_scheme
from models.users import UserRole
from typing import Annotated
from models.users import User
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/images",
    tags=["images"])

@router.get("/get-images", response_model=list[ImageResponse])
def get_images(session: Session = Depends(get_session)):
    """Get all images"""
    statement = select(Image)
    images = session.exec(statement).all()
    return images

@router.get("/get-image/{image_id}", response_model=ImageResponse)
def get_image(image_id: int, session: Session = Depends(get_session)):
    """Get a specific image by ID"""
    image = session.get(Image, image_id)

@router.post("/create-image", response_model=ImageResponse,
 status_code=status.HTTP_201_CREATED, dependencies=[Depends(oauth2_scheme)])
def create_image(image: ImageCreate, _: Annotated[User, Depends(require_role(UserRole.admin))], session: Session = Depends(get_session)):
    """Create a new image"""
    new_image = Image(url=image.url, category_id=image.category_id)
    session.add(new_image)
    session.commit()
    session.refresh(new_image)
    return new_image

@router.put("/update-image/{image_id}", response_model=ImageResponse, dependencies=[Depends(oauth2_scheme)])
def update_image(image_id: int, image_update: ImageUpdate, _: Annotated[User, Depends(require_role(UserRole.admin))], session: Session = Depends(get_session)):
    """Update an image"""
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    image_data = image_update.model_dump(exclude_unset=True)
    for field, value in image_data.items():
        setattr(image, field, value)
    session.add(image)
    session.commit()
    session.refresh(image)
    return image

@router.delete("/delete-image/{image_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(oauth2_scheme)])
def delete_image(image_id: int, _: Annotated[User, Depends(require_role(UserRole.admin))], session: Session = Depends(get_session)):
    """Delete an image"""
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    session.delete(image)
    session.commit()
    return None
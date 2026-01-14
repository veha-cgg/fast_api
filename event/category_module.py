from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.categories import Category, CategoryCreate, CategoryUpdate, CategoryResponse
from models.images import Image, ImageData
from database import get_session
from datetime import datetime
from auth.dependencies import require_role, oauth2_scheme
from models.users import UserRole
from typing import Annotated
from models.users import User
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)

@router.get("/get-categories", response_model=list[CategoryResponse])
def get_categories(session: Session = Depends(get_session)):
    categories = session.exec(select(Category)).all()
    category_ids = [cat.id for cat in categories]
    images = session.exec(select(Image).where(Image.category_id.in_(category_ids))).all() if category_ids else []
    images_by_category = {}
    for img in images:
        if img.category_id not in images_by_category:
            images_by_category[img.category_id] = []
        images_by_category[img.category_id].append(img)
    
    # Convert to CategoryResponse with images
    return [
        CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            images=[ImageData(
                id=img.id,
                url=img.url,
                category_id=img.category_id,
                created_at=img.created_at,
                updated_at=img.updated_at
            ) for img in images_by_category.get(cat.id, [])]
        )
        for cat in categories
    ]

@router.get("/get-category/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    # Get images for this category
    images = session.exec(select(Image).where(Image.category_id == category_id)).all()
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
        updated_at=category.updated_at,
        images=[ImageData(
            id=img.id,
            url=img.url,
            category_id=img.category_id,
            created_at=img.created_at,
            updated_at=img.updated_at
        ) for img in images]
    )

@router.post("/create-category", response_model=CategoryResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(oauth2_scheme)]
             )
def create_category(category: CategoryCreate, 
                    _: Annotated[User, Depends(require_role(UserRole.admin , UserRole.super_admin))], 
                    session: Session = Depends(get_session)) -> Category:
    statement = select(Category).where(Category.name == category.name)
    existing_category = session.exec(statement).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name {category.name} already exists"
        )
    
    new_category = Category(
        name=category.name,
        description=category.description,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    # Get images for this category (will be empty for new category)
    images = session.exec(select(Image).where(Image.category_id == new_category.id)).all()
    return CategoryResponse(
        id=new_category.id,
        name=new_category.name,
        description=new_category.description,
        created_at=new_category.created_at,
        updated_at=new_category.updated_at,
        images=[ImageData(
            id=img.id,
            url=img.url,
            category_id=img.category_id,
            created_at=img.created_at,
            updated_at=img.updated_at
        ) for img in images]
    )

@router.put("/update-category/{category_id}", response_model=CategoryResponse,
            dependencies=[Depends(require_role(UserRole.admin , UserRole.super_admin))])
def update_category(category_id: int, category_update: CategoryUpdate, current_user: Annotated[User, Depends(get_current_user)],
                    session: Session = Depends(get_session)) -> Category:
    if current_user.role != UserRole.admin and current_user.role != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update a category"
        )
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    if category_update.name and category_update.name != category.name:
        statement = select(Category).where(Category.name == category_update.name)
        existing_category = session.exec(statement).first()
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name {category_update.name} already exists"
            )
    
    category_data = category_update.model_dump(exclude_unset=True)
    for field, value in category_data.items():
        setattr(category, field, value)
    
    category.updated_at = datetime.now()
    session.add(category)
    session.commit()
    session.refresh(category)
    images = session.exec(select(Image).where(Image.category_id == category.id)).all()
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
        updated_at=category.updated_at,
        images=[ImageData(
            id=img.id,
            url=img.url,
            category_id=img.category_id,
            created_at=img.created_at,
            updated_at=img.updated_at
        ) for img in images]
    )

@router.delete("/delete-category/{category_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(UserRole.admin , UserRole.super_admin))])
def delete_category(category_id: int, current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)):
    if current_user.role != UserRole.admin and current_user.role != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete a category"
        )
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    session.delete(category)
    session.commit()
    return None


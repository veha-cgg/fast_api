from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.categories import Category, CategoryCreate, CategoryUpdate, CategoryResponse
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
    statement = select(Category)
    categories = session.exec(statement).all()
    return categories

@router.get("/get-category/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    return category

@router.post("/create-category", response_model=CategoryResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(oauth2_scheme)]
             )
def create_category(category: CategoryCreate, 
                    _: Annotated[User, Depends(require_role(UserRole.admin))], 
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
    return new_category

@router.put("/update-category/{category_id}", response_model=CategoryResponse,
            dependencies=[Depends(require_role(UserRole.admin))])
def update_category(category_id: int, category_update: CategoryUpdate, current_user: Annotated[User, Depends(get_current_user)],
                    session: Session = Depends(get_session)) -> Category:
    if current_user.role != UserRole.admin:
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
    
    # Check if name is being updated and if it already exists
    if category_update.name and category_update.name != category.name:
        statement = select(Category).where(Category.name == category_update.name)
        existing_category = session.exec(statement).first()
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name {category_update.name} already exists"
            )
    
    # Update fields
    category_data = category_update.model_dump(exclude_unset=True)
    for field, value in category_data.items():
        setattr(category, field, value)
    
    category.updated_at = datetime.now()
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.delete("/delete-category/{category_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(UserRole.admin))])
def delete_category(category_id: int, current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)):
    if current_user.role != UserRole.admin:
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


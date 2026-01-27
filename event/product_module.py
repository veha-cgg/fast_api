from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.products import *
from database import get_session
from auth.dependencies import require_role, oauth2_scheme
from models.users import UserRole
from typing import Annotated
from models.users import User
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/products",
    tags=["products"]   
)

@router.get("/get-products", response_model=list[ProductResponse])
def get_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    return [
        ProductResponse(**product.model_dump()) for product in products
    ]

@router.get("/get-product/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {product_id} not found")
    return ProductResponse(**product.model_dump())

@router.post("/create-product", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    new_product = Product(**product.model_dump())
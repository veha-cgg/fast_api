from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.orders import *
from database import get_session
from auth.dependencies import require_role, oauth2_scheme
from models.users import UserRole
from typing import Annotated
from models.users import User
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)   

@router.get("/get-orders", response_model=list[OrderResponse])
def get_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    return [
        OrderResponse(**order.model_dump()) for order in orders
    ]   

@router.get("/get-order/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(**order.model_dump())

@router.post("/create-order", response_model=OrderResponse)
def create_order(order: OrderCreate, session: Session = Depends(get_session)):
    new_order = Order(**order.model_dump())
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    return OrderResponse(**new_order.model_dump())

@router.put("/update-order/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order: OrderUpdate, session: Session = Depends(get_session)):
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order_data = order.model_dump(exclude_unset=True)
    for key, value in order_data.items():
        setattr(db_order, key, value)

    db_order.updated_at = datetime.now()
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return OrderResponse(**db_order.model_dump())

@router.delete("/delete-order/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, session: Session = Depends(get_session)):
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    session.delete(db_order)
    session.commit()
    return None
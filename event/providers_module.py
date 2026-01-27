from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.providers import *
from database import get_session
from auth.dependencies import require_role
from models.users import UserRole

router = APIRouter(
    prefix="/providers",
    tags=["providers"]

)

@router.get("/get-providers", response_model=list[ProviderResponse])
def get_providers(session: Session = Depends(get_session)):
    providers = session.exec(select(Provider)).all()
    return [
        ProviderResponse(**provider.model_dump()) for provider in providers
    ]

@router.get("/get-provider/{provider_id}", response_model=ProviderResponse)
def get_provider(provider_id: int, session: Session = Depends(get_session)):
    provider = session.get(Provider, provider_id)   
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with id {provider_id} not found")
    return ProviderResponse(**provider.model_dump())

@router.post("/create-provider", 
dependencies=[Depends(require_role(UserRole.admin, UserRole.super_admin))],
response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)

def create_provider(provider: ProviderCreate, session: Session = Depends(get_session)):
    new_provider = Provider(**provider.model_dump())
    session.add(new_provider)
    session.commit()
    session.refresh(new_provider)
    return ProviderResponse(**new_provider.model_dump())

@router.put("/update-provider/{provider_id}", 
dependencies=[Depends(require_role(UserRole.admin, UserRole.super_admin))],
    response_model=ProviderResponse)

def update_provider(provider_id: int, provider: ProviderUpdate, session: Session = Depends(get_session)):
    provider = session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with id {provider_id} not found")
    provider.name = provider.name
    provider.description = provider.description
    session.commit()
    session.refresh(provider)
    return ProviderResponse(**provider.model_dump())

@router.delete("/delete-provider/{provider_id}", 
dependencies=[Depends(require_role(UserRole.admin, UserRole.super_admin))],
status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: int, session: Session = Depends(get_session)):
    provider = session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with id {provider_id} not found")
    session.delete(provider)
    session.commit()
    return {"message": f"Provider with id {provider_id} deleted successfully"}
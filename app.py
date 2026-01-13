from fastapi import APIRouter
from event import user_module_router, category_module_router
from event.auth_module import router as auth_router

# Main API Router
router = APIRouter(prefix="/api/v1")

# Include all module routers
router.include_router(auth_router)
router.include_router(user_module_router)
router.include_router(category_module_router)



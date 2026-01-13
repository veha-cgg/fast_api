from fastapi import APIRouter
from event.auth_module import router as auth_router
from event.user_module import router as user_module_router
from event.category_module import router as category_module_router
from event.image_module import router as image_module_router
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os 

router = APIRouter(prefix="/api/v1")

# Include all module routers
router.include_router(auth_router, tags=["authentication"])
router.include_router(user_module_router, tags=["users"])
router.include_router(category_module_router, tags=["categories"])
router.include_router(image_module_router, tags=["images"])


static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "images"), exist_ok=True)
router.mount(f"/{static_dir}", StaticFiles(directory=static_dir), name="static")

@router.get("/")
def read_root():
    return FileResponse("templates/view/index.html", media_type="text/html")

@router.get("/login")
def read_login():   
    return FileResponse("templates/view/auth/login.html", media_type="text/html")           
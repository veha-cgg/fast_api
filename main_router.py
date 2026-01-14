from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os 

from event.auth_module import router as auth_router
from event.user_module import router as user_module_router
from event.category_module import router as category_module_router
from event.image_module import router as image_module_router
from event.chat_module import router as chat_module_router
from event.product_module import router as product_module_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Initialize templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include all module routers
router = APIRouter(prefix="/api/v1")
router.include_router(auth_router, tags=["authentication"])
router.include_router(user_module_router, tags=["users"])
router.include_router(category_module_router, tags=["categories"])
router.include_router(image_module_router, tags=["images"])
router.include_router(chat_module_router, tags=["websocket"])
router.include_router(product_module_router, tags=["products"])

# Web routes router
web_router = APIRouter()

@web_router.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page": "index"})

@web_router.get("/login")
def read_login(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request, "page": "login"})

@web_router.get("/panel")
def read_panel(request: Request):
    return templates.TemplateResponse("panel.html", {"request": request, "page": "panel"})
      
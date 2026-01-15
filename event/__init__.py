from .user_module import router as user_module_router
from .category_module import router as category_module_router
from .image_module import router as image_module_router
from .product_module import router as product_module_router
from .providers_module import router as providers_module_router
from .orders_module import router as orders_module_router

__all__ = [
    "user_module_router",
    "category_module_router", 
    "image_module_router", 
    "product_module_router",
    "providers_module_router",
    "orders_module_router",
    "web_router"
     ]    

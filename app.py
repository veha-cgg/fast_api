from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import connect_to_database, disconnect_from_database
from main_router import router, web_router
from websocket import router as websocket_router
import time 
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    await connect_to_database()
    yield
    # Shutdown
    await disconnect_from_database()

def custom_openapi():
    """Custom OpenAPI schema configuration"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="API Management",
        version="1.0.0",
        description="""
        API Management is a platform for managing APIs.
        It allows you to create, update, and delete APIs.
        It also allows you to create, update, and delete categories.
        It also allows you to create, update, and delete images.
        """,
        routes=app.routes,
    )
    
    # Ensure components exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Add OAuth2 security scheme
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token (without 'Bearer ' prefix)"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="API Management",
        description="""
        ## API Management
        
        A comprehensive API management system with user authentication,
        category management, and image handling capabilities.
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Set custom OpenAPI schema
    app.openapi = custom_openapi
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include main router
    app.include_router(router)
    
    # Include web router
    app.include_router(web_router)
    
    # Include websocket router
    app.include_router(websocket_router)
    
    # Mount static files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")

    if not os.path.exists(STATIC_DIR):
        os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
        os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
        os.makedirs(os.path.join(STATIC_DIR, "images"), exist_ok=True)
    
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    # Add middleware for process time
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Health check endpoint
    @app.get("/health")
    def health():
        return {
            "status": "healthy",
            "message": "API is running",
            "timestamp": time.time()
        }
    
    return app
    
app = create_application()
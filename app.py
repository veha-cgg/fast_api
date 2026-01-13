from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from database import connect_to_database, disconnect_from_database
from main_router import router
import time 
from fastapi.responses import FileResponse

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
    
    # Add middleware for process time
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Root endpoint
    @app.get("/")
    def root():
        return FileResponse("templates/view/index.html")
    
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
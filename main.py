from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from database import connect_to_database, disconnect_from_database
from app import router
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_database()
    yield
    # Shutdown
    await disconnect_from_database()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Python FastAPI Project",
        version="1.0.0",
        description="""
        ## API with Users and Categories
        
        ### Authentication
        1. Use `/api/v1/auth/login` (form data) or `/api/v1/auth/login-json` (JSON) to get an access token
        2. Click the "Authorize" button above and enter: `Bearer <your_token>`
        3. Or include in headers: `Authorization: Bearer <your_token>`
        """,
        routes=app.routes,
    )
    # Ensure components exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    # Add OAuth2 security scheme (FastAPI should auto-detect, but we ensure it's there)
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

app = FastAPI(
    title="Python FastAPI Project",
    description="""
    ## API with Users and Categories
    
    ### Authentication
    Use the `/api/v1/auth/login` endpoint to get an access token.
    Then use the token in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    lifespan=lifespan
)
app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "Welcome to the API",
        "docs": "/docs",
        "health": "/health"
    }

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/health")
def health():
    return {"status": "healthy", "message": "API is running"}
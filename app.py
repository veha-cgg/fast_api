from fastapi import FastAPI
from fastapi import APIRouter
from event import user_module_router

app = FastAPI()

router = APIRouter()
router.prefix = "/api/v1"
app.include_router(router)

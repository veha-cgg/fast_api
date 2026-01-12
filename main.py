from fastapi import FastAPI
from event import user_module
app = FastAPI()

app.include_router(user_module.router)


# @app.get("/")
# def read_root():
#     return {"message": "Hello, World!"}

# @app.get("/items/{item_id}")
# def read_item(item_id: int):
#     return {"item_id": item_id}

# @app.get("/users/{user_id}")
# def read_user(user_id: str):
#     return {"user_id": user_id}
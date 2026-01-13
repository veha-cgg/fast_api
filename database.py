from sqlmodel import SQLModel, create_engine, Session
from starlette.config import Config
from models.users import User
from models.categories import Category

config = Config(".env")

DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST", default="127.0.0.1")
DB_NAME = config("DB_NAME")
DB_PORT = config("DB_PORT", cast=int, default=3306)

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

async def connect_to_database():
    create_db_and_tables()

async def disconnect_from_database():
    pass

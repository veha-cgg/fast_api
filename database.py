from sqlmodel import SQLModel, create_engine, Session, select
from starlette.config import Config
from models.users import User, UserRole, UserNotification
from models.chats import Chat, UserChat, ChatRoom, ChatRoomParticipant
from models.categories import Category
from models.images import Image
from models.products import Product

# Import all models to ensure SQLAlchemy can resolve relationships
# This must happen before create_db_and_tables() is called

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

def create_default_user():  
    from auth.password import hash_password
    
    with Session(engine) as session:
        existing_admin = session.exec(
            select(User).where(User.email == "admin@cgg.holdings")
        ).first()
        
        if existing_admin:
            return existing_admin
        admin = User(
            name="Administrator",
            email="admin@cgg.holdings",
            password=hash_password("password"),
            role=UserRole.super_admin,
            is_active=True
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin

async def connect_to_database():
    create_db_and_tables()
    try:
        create_default_user()
    except Exception as e:
        raise e
async def disconnect_from_database():
    pass
    


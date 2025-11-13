import os
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Initialize database tables"""
    # Import all models here to ensure they are registered
    from modules.user.model import User  # noqa: F401
    from modules.notes.model import Note  # noqa: F401
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("✓ Database initialized successfully")

def get_session():
    """Get database session for dependency injection"""
    with Session(engine) as session:
        yield session
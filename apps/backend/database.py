import os
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Initialize database tables"""
    SQLModel.metadata.create_all(engine)
    print("✓ Database initialized successfully")

def get_session():
    """Get database session for dependency injection"""
    with Session(engine) as session:
        yield session
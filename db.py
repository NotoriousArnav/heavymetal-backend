"""
Database Controller to make sure that Database is connected and switching is easier as well.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os, uuid

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./db.sqlite3")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)

# Models

class User(Base):
    __tablename__ = "users"

    uuid = Column(
            String,
            primary_key=True,
            index=True,
            default=str(uuid.uuid4())
        )
    name = Column(String, index=True) # username
    hashed_password = Column(String)

"""
Database Controller to make sure that Database is connected and switching is easier as well.
"""

import os
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./db.sqlite3")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base:DeclarativeMeta = declarative_base()


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

    uuid = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    name = Column(String, index=True)  # username
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class Audio(Base):
    __tablename__ = "audio"

    uuid = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    name = Column(String, index=True)
    path = Column(String, index=True)


class Artist(Base):
    __tablename__ = "artists"

    uuid = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    name = Column(String, index=True)


class Album(Base):
    __tablename__ = "albums"

    uuid = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    name = Column(String, index=True)


class Track(Base):
    __tablename__ = "tracks"

    uuid = Column(String, primary_key=True, index=True, default=str(uuid.uuid4()))
    name = Column(String, index=True)
    album = Column(String, ForeignKey("albums.uuid"))
    artist = Column(String, ForeignKey("artists.uuid"))
    audio = Column(String, ForeignKey("audio.uuid"))
    genre = Column(String, index=True)

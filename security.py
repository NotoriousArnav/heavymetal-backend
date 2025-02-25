from argon2 import PasswordHasher
from db import SessionLocal, User
from schemas import *
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from jose import jwt, JWTError
from datetime import datetime, timedelta

hasher = PasswordHasher()

def get_user(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.name == username).first()
    return user

def verify_password(plain_password, hashed_password):
    return hasher.verify(hashed_password, plain_password)

def get_password_hash(password):
    return hasher.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "secret_key", algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = Depends()):
    credentials_exception = HTTPBearer()
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = username
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data)
    if user is None:
        raise credentials_exception
    return user

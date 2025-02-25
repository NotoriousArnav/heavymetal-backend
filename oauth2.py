from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from utils import get_user, verify_password, get_password_hash
from datetime import timedelta
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class OAuth2RequestForm(BaseModel):
    grant_type: str
    username: str
    password: str
    scope: str

class OAuth2Token(BaseModel):
    access_token: str
    token_type: str

def authenticate_user_oauth2(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token_oauth2(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "secret_key", algorithm="HS256")
    return encoded_jwt

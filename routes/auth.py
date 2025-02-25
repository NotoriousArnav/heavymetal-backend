from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from security import authenticate_user, create_access_token, get_current_user, get_current_active_user, get_current_active_superuser
from security import authenticate_user_oauth2, create_access_token_oauth2, get_current_user_oauth2
from datetime import timedelta
from oauth2 import OAuth2RequestForm, OAuth2Token
from db import User
from utils import get_password_hash
from sqlalchemy.orm import Session
from db import SessionLocal

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={
        404: {
                "description":"Not found"
            },
        500: {
                "description":"Internal Server Error"
            },
        400: {
                "description":"Bad Request"
            },
        },
)

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordRequestForm

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user_oauth2(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token_oauth2(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

class RegistrationRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(request: RegistrationRequest):
    user = get_user(request.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = get_password_hash(request.password)
    new_user = User(name=request.username, hashed_password=hashed_password)
    db = SessionLocal()
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@router.get("/profile")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {"username": current_user.name}

@router.get("/superuser")
async def read_superuser(current_user: User = Depends(get_current_active_superuser)):
    return {"username": current_user.name}

@router.get("/oauth2/profile")
async def read_users_me_oauth2(current_user: User = Depends(get_current_user_oauth2)):
    return {"username": current_user.name}

from argon2 import PasswordHasher
from db import SessionLocal, User
from schemas import *

hasher = PasswordHasher()

def get_user(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.name == username).first()
    return user

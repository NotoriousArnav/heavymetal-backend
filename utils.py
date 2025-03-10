from argon2 import PasswordHasher

from db import SessionLocal, User

hasher = PasswordHasher()


def get_user(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.name == username).first()
    return user


def verify_password(plain_password, hashed_password):
    return hasher.verify(hashed_password, plain_password)


def get_password_hash(password):
    return hasher.hash(password)

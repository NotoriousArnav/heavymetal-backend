from pydantic import BaseModel

class User(BaseModel):
    name: str

    class Config:
        orm_mode = True

class UserCreate(User):
    password: str

class UserInDB(User):
    hashed_password: str

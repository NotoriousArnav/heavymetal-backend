from pydantic import BaseModel
from typing import Optional, Literal, Union

class User(BaseModel):
    name: str

    class Config:
        orm_mode = True

class UserCreate(User):
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: Union[Literal["bearer"], None]
    
class TokenData(BaseModel):
    username: Union[str, None]

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str]
    password: Optional[str]

class UserUpdateInDB(UserUpdate):
    hashed_password: Optional[str]

class Album(BaseModel):
    name: str

    class Config:
        orm_mode = True

class Artist(BaseModel):
    name: str

    class Config:
        orm_mode = True

class Audio(BaseModel):
    name: str
    path: str

    class Config:
        orm_mode = True

class Track(BaseModel):
    name: str
    album: Album
    artist: Artist
    audio: Audio
    genre: str

    class Config:
        orm_mode = True

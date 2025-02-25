from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.requests import Request
from typing import List
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import get_db, Audio, Track
from schemas import Track
from security import authenticate_user, create_access_token

router = APIRouter(
    prefix="/songs",
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
    tags=["Songs"],
)

class SongRequest(BaseModel):
    limit: int = 10
    offset: int = 0

async def get_current_user(token: str = Depends()):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@router.get("/list")
async def get_songs(request: SongRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tracks = db.query(Track).limit(request.limit).offset(request.offset).all()
    return tracks

@router.get("/serve/{song_id}")
async def serve_song(song_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    track = db.query(Track).filter(Track.uuid == song_id).first()
    if track is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return FileResponse(track.audio.path, media_type="audio/mpeg")

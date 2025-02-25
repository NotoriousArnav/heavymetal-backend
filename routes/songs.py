from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.requests import Request
from typing import List
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import get_db, Audio, Track
from schemas import Track

router = APIRouter(
    prefix="/api/v1/songs",
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

class SongRequest(BaseModel):
    limit: int = 10
    offset: int = 0

@router.get("/list")
async def get_songs(request: SongRequest, db: Session = Depends(get_db)):
    tracks = db.query(Track).limit(request.limit).offset(request.offset).all()
    return tracks

@router.get("/serve/{song_id}")
async def serve_song(song_id: str, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.uuid == song_id).first()
    if track is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return FileResponse(track.audio.path, media_type="audio/mpeg")

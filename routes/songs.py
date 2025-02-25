from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.requests import Request
from typing import List, Iterator
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import get_db, Audio, Track, Album, Artist
from schemas import User
from schemas import Album as AlbumSchema
from schemas import Artist as ArtistSchema
from schemas import Audio as AudioSchema
from schemas import Track as TrackSchema
from security import get_current_user
import os

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

@router.get("/list")
async def get_songs(
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    request = SongRequest(limit=limit, offset=offset)
    tracks = [{'uuid': track.uuid, 'name': track.name} for track in db.query(Track).limit(request.limit).all()]
    return tracks

@router.get("/info/{song_id}")
async def get_song_info(
        song_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    track = db.query(Track).filter(Track.uuid == song_id).first()
    audio = db.query(Audio).filter(Audio.uuid == track.audio).first()
    album = db.query(Album).filter(Album.uuid == track.album).first()
    artist = db.query(Artist).filter(Artist.uuid == track.artist).first()
    if track is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return TrackSchema(
        uuid=track.uuid,
        name=track.name,
        album=AlbumSchema(
            name=album.name,
        ),
        artist=ArtistSchema(
            name=artist.name,
        ),
        audio=AudioSchema(
            name=audio.name,
            path=audio.path,
        ),
        genre=track.genre if track.genre is not None else "",
    )

@router.get("/search/{song}")
async def search_songs(
        song: str,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    tracks = [{'uuid': track.uuid, 'name': track.name} for track in db.query(Track).filter(Track.name.contains(song)).limit(limit).all()]
    return tracks

@router.get("/search/{artist}")
async def search_songs_by_artist(
        artist: str,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    artists = db.query(Artist).filter(Artist.name.contains(artist)).limit(limit).all()
    return [{'uuid': artist.uuid, 'name': artist.name} for artist in artists]

@router.get("/search/{album}")
async def search_songs_by_album(
        album: str,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    albums = db.query(Album).filter(Album.name.contains(album)).limit(limit).all()
    return [{'uuid': album.uuid, 'name': album.name} for album in albums]

@router.get("/search/{genre}")
async def search_songs_by_genre(
        genre: str,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    tracks = [{'uuid': track.uuid, 'name': track.name} for track in db.query(Track).filter(Track.genre.contains(genre)).limit(limit).all()]
    return tracks

def iter_file(file_path: str, start: int, end: int):
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_to_read = end - start + 1
            while bytes_to_read > 0:
                chunk_size = min(1024 * 1024, bytes_to_read)
                data = f.read(chunk_size)
                if not data:
                    break
                bytes_to_read -= len(data)
                yield data

@router.get("/stream/{song_id}")
async def stream_song(
        song_id: str,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    """
    NOTE: This is a streaming endpoint
    This endpoint is cursed, (but it works somehow, hail satan or god, i dunno, I am atheist and i know it works)
    The working implementation on how to use this in the frontend is given in `$PROJECT_ROOT/stream_audio_example.html`.
    I tried this endpoint with curl too and like this:
    ```bash
     curl -X 'GET' \
  'http://127.0.0.1:8080/api/v1/songs/stream/{SONG_ID}' \   
  -H 'accept: application/json' \
  -H 'Authorization: Bearer TOKEN_HERE' | ffplay -
    ```
    and it works!
    """
    track = db.query(Track).filter(Track.uuid == song_id).first()
    audio = db.query(Audio).filter(Audio.uuid == track.audio).first()
    file_path = audio.path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)

    range_header = request.headers.get("Range")
    start = 0
    end = file_size - 1

    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            if range_match.group(2):
                end = int(range_match.group(2))

    if start >= file_size or end >= file_size:
        raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

    content_length = end - start + 1
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "audio/mpeg",
    }

    return StreamingResponse(iter_file(file_path, start, end), status_code=206, headers=headers)

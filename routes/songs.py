from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from fastapi.requests import Request
from typing import List
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

@router.get("/serve/{song_id}")
async def serve_song(
        song_id: str,
        range: str = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    print(current_user)
    track = db.query(Track).filter(Track.uuid == song_id).first()
    audio = db.query(Audio).filter(Audio.uuid == track.audio).first()
    if track is None:
        raise HTTPException(status_code=404, detail="Song not found")
    # No changes needed here, the import statement was added above.
    else:
        return FileResponse(audio.path, media_type="audio/mpeg")

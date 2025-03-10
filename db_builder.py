import datetime
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional, Tuple, Union

from colorama import Fore, Style, init
from dotenv import load_dotenv
from mutagen import File
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggFileType as OGG
from mutagen.wave import WAVE as WAV
from tqdm import tqdm  # For progress bars

import db

# Define a type alias for audio file classes
AudioFile = Union[MP3, FLAC, WAV, OGG]

# Mapping of file extensions to their corresponding classes
EXTENSION_MAP: dict[str, Callable[[Path], AudioFile]] = {
    ".mp3": MP3,
    ".flac": FLAC,
    ".wv": WAV,
    ".ogg": OGG,
}


# Setup logging
filename = os.getenv(
    "LOGFILE",
    os.path.join(
        tempfile.gettempdir(),
        "library_builder.log"
    )
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=filename,
)
logger = logging.getLogger("HeavyMetal")

load_dotenv()
init(autoreset=True)

MEDIA_FOLDER = Path(os.getenv("MEDIA_FOLDER", None))
BATCH_SIZE = int(
    os.getenv("BATCH_SIZE", "100")
)  # Number of files to process before committing
MAX_WORKERS = int(
    os.getenv("MAX_WORKERS", "4")
)  # Number of parallel workers for metadata extraction
CHECKPOINT_FILE = "library_builder_checkpoint.txt"

CODES = {
    "OK": f"[{Fore.GREEN}+{Style.RESET_ALL}]",
    "INFO": f"[{Fore.BLUE}-{Style.RESET_ALL}]",
    "WARNING": f"[{Fore.YELLOW}*{Style.RESET_ALL}]",
    "ERROR": f"[{Fore.RED}!{Style.RESET_ALL}]",
}

# Cache for artists and albums to reduce database queries
artist_cache = {}
album_cache = {}


def log_and_print(level: str, message: str) -> None:
    """
    Logs a message and prints it to the console

    Args:
        level (str): The log level (INFO, WARNING, ERROR, OK)
        message (str): The message to log
    """
    print(f"{CODES.get(level, CODES['INFO'])} {message}")

    if level == "OK" or level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)


def traverse_directory(
    path: Path, filter_: Optional[Callable[[Path], bool]] = None
) -> Generator[Path, None, None]:
    """
    Recursively traverses a directory and yields files one by one

    Args:
        path (Path): The directory to traverse
        filter (Callable, optional): A function to filter the files. Defaults to None.

    Yields:
        Path: File paths one at a time
    """
    try:
        for entry in path.iterdir():
            if entry.is_dir():
                yield from traverse_directory(entry, filter_)
            elif entry.is_file() and (filter_ is None or filter_(entry)):
                yield entry
    except PermissionError:
        log_and_print("WARNING", f"Permission denied accessing {path}")
    except Exception as e:
        log_and_print("ERROR", f"Error traversing {path}: {e}")


def isAudioFile(path: Path) -> bool:
    """
    Checks if a file is an audio file based on extension first, then metadata

    Args:
        path (Path): The file to check

    Returns:
        bool: True if the file is an audio file, False otherwise
    """
    # Check extension first (much faster than parsing with mutagen)
    audio_extensions = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac", ".wma"}
    if path.suffix.lower() not in audio_extensions:
        return False

    # Then try to parse with mutagen to confirm
    try:
        audio = File(path)
        return bool(audio)
    except Exception:
        return False


def check_format(path: Path) -> Optional[AudioFile]:
    """
    Check if the file is FLAC, MP3, WAV, OGG, etc.

    Args:
        path (Path): The file to check

    Returns:
        An instance of the corresponding audio file class or None if unsupported.
    """
    try:
        # Identify by extension
        ext = path.suffix.lower()
        if ext in EXTENSION_MAP:
            return EXTENSION_MAP[ext](path)

        # Fall back to MIME type detection
        f = File(path)
        if not f:
            return None
        mime_type = "".join(f.mime)
        for ext, cls in EXTENSION_MAP.items():
            if ext.strip('.') in mime_type:
                return cls(path)
        return None
    except Exception as e:
        logger.error(f"Error checking format for {path}: {e}")
        return None


# def check_format(path: Path) -> Union[MP3, FLAC, WAV, OGG, None]:
#     """
#     Will check if the file is FLAC, M4A, MP3, WAV, OGG, etc

#     Args:
#         path (Path): The file to check
#     """
#     try:
#         # Try to identify by extension first (faster)
#         ext = path.suffix.lower()
#         if ext == ".mp3":
#             return MP3(path)
#         elif ext == ".flac":
#             return FLAC(path)
#         elif ext == ".wav":
#             return WAV(path)
#         elif ext == ".ogg":
#             return OGG(path)

#         # Fall back to mime type detection
#         f = File(path)
#         if not f:
#             return None
#         if "mp3" in "".join(f.mime):
#             return MP3(path)
#         elif "wav" in "".join(f.mime):
#             return WAV(path)
#         elif "ogg" in "".join(f.mime):
#             return OGG(path)
#         elif "flac" in "".join(f.mime):
#             return FLAC(path)
#         else:
#             return None
#     except Exception as e:
#         logger.error(f"Error checking format for {path}: {e}")
#         return None


def parseAudioMetadata(path: Path) -> Dict[str, Any]:
    """
    Parses the metadata of an audio file

    Args:
        path (Path): The audio file to parse

    Returns:
        dict: A dictionary containing the metadata
    """
    metadata = {
        "title": None,
        "artist": None,
        "album": None,
        "genre": None,
        "track_number": None,
        "year": None,
        "path": str(path),
        "filename": path.name,
    }

    try:
        audio_file = check_format(path)
        if not audio_file:
            logger.warning(f"Could not parse metadata for {path}")
            return metadata

        # Extract metadata based on file type
        if isinstance(audio_file, MP3):
            tags = audio_file.tags
            if tags:
                if "TIT2" in tags:  # Title
                    metadata["title"] = str(tags["TIT2"])
                if "TPE1" in tags:  # Artist
                    metadata["artist"] = str(tags["TPE1"])
                if "TALB" in tags:  # Album
                    metadata["album"] = str(tags["TALB"])
                if "TCON" in tags:  # Genre
                    metadata["genre"] = str(tags["TCON"])
                if "TRCK" in tags:  # Track number
                    metadata["track_number"] = str(tags["TRCK"])
                if "TDRC" in tags:  # Year
                    metadata["year"] = str(tags["TDRC"])

        # For FLAC, OGG, etc. which use Vorbis comment style tags
        elif hasattr(audio_file, "tags") and audio_file.tags:
            tags = audio_file.tags
            metadata["title"] = tags.get("TITLE", [None])[0]
            metadata["artist"] = tags.get("ARTIST", [None])[0]
            metadata["album"] = tags.get("ALBUM", [None])[0]
            metadata["genre"] = tags.get("GENRE", [None])[0]
            metadata["track_number"] = tags.get("TRACKNUMBER", [None])[0]
            metadata["year"] = tags.get("DATE", [None])[0]

    except Exception as e:
        logger.warning(f"Error parsing metadata for {path}: {e}")

    # Use filename as fallback for title if not found in metadata
    if not metadata["title"]:
        metadata["title"] = path.stem

    return metadata


def get_or_create_artist(session, artist_name: str) -> Tuple[str, bool]:
    """
    Gets or creates an artist in the database

    Args:
        session: SQLAlchemy database session
        artist_name: The name of the artist

    Returns:
        Tuple[str, bool]: The artist UUID and whether it was created
    """
    if not artist_name:
        return None, False

    # Check cache first
    if artist_name in artist_cache:
        return artist_cache[artist_name], False

    # Check database
    artist = session.query(db.Artist).filter(db.Artist.name == artist_name).first()
    if artist:
        # Add to cache
        artist_cache[artist_name] = artist.uuid
        return artist.uuid, False

    # Create new artist
    artist_uuid = str(uuid.uuid4())
    artist = db.Artist(uuid=artist_uuid, name=artist_name)
    session.add(artist)

    # Add to cache
    artist_cache[artist_name] = artist_uuid
    return artist_uuid, True


def get_or_create_album(session, album_name: str) -> Tuple[str, bool]:
    """
    Gets or creates an album in the database

    Args:
        session: SQLAlchemy database session
        album_name: The name of the album

    Returns:
        Tuple[str, bool]: The album UUID and whether it was created
    """
    if not album_name:
        return None, False

    # Check cache first
    if album_name in album_cache:
        return album_cache[album_name], False

    # Check database
    album = session.query(db.Album).filter(db.Album.name == album_name).first()
    if album:
        # Add to cache
        album_cache[album_name] = album.uuid
        return album.uuid, False

    # Create new album
    album_uuid = str(uuid.uuid4())
    album = db.Album(uuid=album_uuid, name=album_name)
    session.add(album)

    # Add to cache
    album_cache[album_name] = album_uuid
    return album_uuid, True


def makeDBEntry(path: Path, session) -> bool:
    """
    Creates a database entry for a file

    Args:
        path (Path): The file to create the database entry for
        session: SQLAlchemy database session

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse metadata
        metadata = parseAudioMetadata(path)

        # Create or get Audio entry
        audio_uuid = str(uuid.uuid4())
        audio = db.Audio(
            uuid=audio_uuid, name=metadata["filename"], path=str(path.absolute())
        )
        session.add(audio)

        # Handle Artist
        artist_uuid, artist_created = get_or_create_artist(session, metadata["artist"])

        # Handle Album
        album_uuid, album_created = get_or_create_album(session, metadata["album"])

        # Create Track entry
        track_uuid = str(uuid.uuid4())
        track = db.Track(
            uuid=track_uuid,
            name=metadata["title"],
            album=album_uuid,
            artist=artist_uuid,
            audio=audio_uuid,
            genre=metadata["genre"],
        )
        session.add(track)

        return True

    except Exception as e:
        logger.error(f"Error creating DB entry for {path}: {e}")
        return False


def process_files_batch(files_batch, session):
    """
    Process a batch of files and add them to the database

    Args:
        files_batch: List of file paths to process
        session: SQLAlchemy database session

    Returns:
        int: Number of successfully processed files
    """
    success_count = 0

    for file_path in files_batch:
        if makeDBEntry(file_path, session):
            success_count += 1

    # Commit the batch
    try:
        session.commit()
    except Exception as e:
        logger.error(f"Error committing batch to database: {e}")
        session.rollback()
        return 0

    return success_count


def get_audio_file_count(directory: Path) -> int:
    """
    Get an estimate of the total number of audio files

    Args:
        directory: Root directory to scan

    Returns:
        int: Estimated number of audio files
    """
    # This could be slow for very large collections
    # For a quick estimate, we can count files with audio extensions
    count = 0
    audio_extensions = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac", ".wma"}

    for ext in audio_extensions:
        count += len(list(directory.glob(f"**/*{ext}")))

    return count


def save_checkpoint(processed_path: str) -> None:
    """
    Save the last processed file path as a checkpoint

    Args:
        processed_path: Path of the last processed file
    """
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(processed_path)


def load_checkpoint() -> Optional[str]:
    """
    Load the last processed file path from checkpoint

    Returns:
        Optional[str]: Path of the last processed file, if any
    """
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return f.read().strip()
    return None


def main():
    start_time = time.time()
    log_and_print("INFO", "Hello from HeavyMetal library builder!")

    # Initialize the database
    db.init_db()

    # Check for checkpoint
    last_processed = load_checkpoint()
    if last_processed:
        log_and_print("INFO", f"Resuming from checkpoint: {last_processed}")

    # Get estimated file count for progress bar
    log_and_print("INFO", f"Estimating number of audio files in {MEDIA_FOLDER}...")
    estimated_total = get_audio_file_count(MEDIA_FOLDER)
    log_and_print("OK", f"Estimated {estimated_total} audio files to process")

    # Initialize session
    session = db.SessionLocal()

    try:
        # Cache existing artists and albums
        log_and_print("INFO", "Caching existing artists and albums...")
        for artist in session.query(db.Artist).all():
            artist_cache[artist.name] = artist.uuid

        for album in session.query(db.Album).all():
            album_cache[album.name] = album.uuid
        log_and_print(
            "OK", f"Cached {len(artist_cache)} artists and {len(album_cache)} albums"
        )

        # Process files
        log_and_print("INFO", f"Scanning {MEDIA_FOLDER} for audio files...")

        file_generator = traverse_directory(MEDIA_FOLDER, filter_=isAudioFile)

        # Skip files until checkpoint if resuming
        if last_processed:
            for i, file_path in enumerate(file_generator):
                if str(file_path.absolute()) == last_processed:
                    log_and_print(
                        "OK", f"Skipped {i+1} previously processed files"
                    )
                    break

        # Process remaining files with progress bar
        batch = []
        processed_count = 0
        success_count = 0

        with tqdm(total=estimated_total, desc="Processing files") as pbar:
            for file_path in file_generator:
                batch.append(file_path)

                if len(batch) >= BATCH_SIZE:
                    batch_success = process_files_batch(batch, session)
                    success_count += batch_success
                    processed_count += len(batch)
                    pbar.update(len(batch))

                    # Save checkpoint
                    save_checkpoint(str(batch[-1].absolute()))

                    # Calculate and display stats
                    elapsed = time.time() - start_time
                    files_per_second = processed_count / elapsed if elapsed > 0 else 0
                    success_rate = (
                        (success_count / processed_count * 100)
                        if processed_count > 0
                        else 0
                    )

                    log_and_print(
                        "INFO",
                        f"Processed {processed_count} files ({files_per_second:.2f} files/sec), {success_rate:.1f}% success",
                    )

                    batch = []

            # Process remaining files
            if batch:
                batch_success = process_files_batch(batch, session)
                success_count += batch_success
                processed_count += len(batch)
                pbar.update(len(batch))
                save_checkpoint(str(batch[-1].absolute()))

        # Final stats
        elapsed = time.time() - start_time
        elapsed_str = str(datetime.timedelta(seconds=int(elapsed)))
        files_per_second = processed_count / elapsed if elapsed > 0 else 0
        success_rate = (
            (success_count / processed_count * 100) if processed_count > 0 else 0
        )

        log_and_print("OK", "Database build complete!")
        log_and_print("OK", f"Processed {processed_count} files in {elapsed_str}")
        log_and_print("OK", f"Average speed: {files_per_second:.2f} files/second")
        log_and_print("OK", f"Success rate: {success_rate:.1f}%")
        log_and_print("OK", f"Successful entries: {success_count}")

        # Clean up checkpoint if completed successfully
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

    except KeyboardInterrupt:
        log_and_print("WARNING", "Process interrupted! Saving progress...")
        if batch:
            process_files_batch(batch, session)
            if batch:
                save_checkpoint(str(batch[-1].absolute()))
    except Exception as e:
        log_and_print("ERROR", f"Error during database build: {e}")
        logger.exception("Fatal error during database build")
    finally:
        session.close()


if __name__ == "__main__":
    if not MEDIA_FOLDER:
        log_and_print(
            "ERROR",
            "Please set MEDIA_FOLDER environment variable either in the .env file or as a system variable.",
        )
        exit(1)
    else:
        log_and_print("OK", f"{MEDIA_FOLDER=}")
    main()
    print(f"{CODES['OK']} Logs have been written to {filename}")

"""Configuration: paths and API key from .env."""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_books_dir() -> Path:
    """Read path to Obsidian books folder from .env."""
    load_dotenv()
    raw = os.getenv("BOOKS_DIR")
    if not raw:
        raise RuntimeError(
            "BOOKS_DIR is not set in .env. "
            "Copy .env.example to .env and fill in the absolute path."
        )
    path = Path(raw)
    if not path.exists():
        raise RuntimeError(f"BOOKS_DIR does not exist: {path}")
    return path


def get_data_dir() -> Path:
    """Read path to data directory from .env. Create if doesn't exist."""
    load_dotenv()
    raw = os.getenv("DATA_DIR")
    if not raw:
        raise RuntimeError("DATA_DIR is not set in .env.")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_google_books_api_key() -> str:
    """Read Google Books API key. Returns empty string if not set (optional)."""
    load_dotenv()
    return os.getenv("GOOGLE_BOOKS_API_KEY", "")


def get_isbndb_api_key() -> str:
    """Read ISBNdb API key from .env.

    Returns empty string if not set. ISBNdb requires a key —
    requests without it will fail with 401 Unauthorized.
    """
    load_dotenv()
    return os.getenv("ISBNDB_API_KEY", "")


if __name__ == "__main__":
    print(f"Books: {get_books_dir()}")
    print(f"Data:  {get_data_dir()}")

    isbndb_key = get_isbndb_api_key()
    print(f"ISBNdb key: {'set (' + str(len(isbndb_key)) + ' chars)' if isbndb_key else 'NOT SET'}")

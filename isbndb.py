"""ISBNdb API client."""

import logging
import time

import requests

from config import get_isbndb_api_key

API_URL = "https://api2.isbndb.com"


def _request(isbn: str) -> dict:
    """Make a single request to ISBNdb API. May raise."""
    api_key = get_isbndb_api_key()
    if not api_key:
        raise RuntimeError("ISBNDB_API_KEY is not set in .env")

    url = f"{API_URL}/book/{isbn}"
    headers = {"Authorization": api_key}

    response = requests.get(url, headers=headers, timeout=(5, 30))
    response.raise_for_status()
    return response.json()


def _clean_response(raw: dict) -> dict | None:
    """Convert raw ISBNdb response to our unified format."""
    book = raw.get("book")
    if not book:
        return None

    return {
        "title": book.get("title", ""),
        "authors": book.get("authors", []),
        "publisher": book.get("publisher", ""),
        "year": book.get("date_published", "")[:4],
        "pages": book.get("pages", 0),
    }


def _request_with_retry(isbn: str, max_attempts: int = 3) -> dict:
    """Request with retries on transient errors."""
    for attempt in range(1, max_attempts + 1):
        try:
            return _request(isbn)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt == max_attempts:
                logging.error("ISBNdb: network exhausted for %s", isbn)
                raise
            wait = 2 ** attempt
            logging.warning(
                "ISBNdb: network attempt %d/%d failed for %s: %s. Waiting %d sec.",
                attempt, max_attempts, isbn, e, wait,
            )
            time.sleep(wait)

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (429, 502, 503, 504):
                status = e.response.status_code
                if attempt == max_attempts:
                    logging.error(
                        "ISBNdb: HTTP %d exhausted after %d attempts for %s",
                        status, max_attempts, isbn,
                    )
                    raise
                wait = 30 * attempt
                logging.warning(
                    "ISBNdb: HTTP %d (attempt %d/%d) for %s. Waiting %d sec.",
                    status, attempt, max_attempts, isbn, wait,
                )
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("Unreachable")


def fetch_from_isbndb(isbn: str) -> dict | None:
    """Get book data from ISBNdb by ISBN. Public API."""
    if not isbn:
        return None

    try:
        raw = _request_with_retry(isbn)
    except requests.exceptions.RequestException as e:
        logging.error("ISBNdb permanent failure for %s: %s", isbn, e)
        return None

    return _clean_response(raw)


if __name__ == "__main__":
    test_isbns = [
        "9781633438538",
        "9781492091196",
        "0000000000",
        "",
    ]

    for isbn in test_isbns:
        print(f"\nFetching {isbn!r}...")
        book = fetch_from_isbndb(isbn)
        if book:
            print(f"  Found: {book['title']}")
            print(f"  Authors: {book['authors']}")
        else:
            print(f"  Not found / failed")
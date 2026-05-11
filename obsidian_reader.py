"""
Read book cards from Obsidian vault.

Each card is a Markdown file with YAML frontmatter in our migrated format:
    Russian title, Title, Authors, ISBN, Year, Pages, Publisher, Edition,
    Russian publisher, Tags, Cover, migrated.

We extract metadata only (frontmatter), ignoring the body.
"""
import logging
from pathlib import Path
import frontmatter
from tabulate import tabulate


def parse_card(path: Path) -> dict | None:
    """
    Parse a single Markdown card with YAML frontmatter.

    Args:
        path: path to the .md file.

    Returns:
        Dict with 'file' (file name) and 'metadata' (parsed YAML),
        or None if parsing failed or no frontmatter present.
    """
    try:
        post = frontmatter.load(str(path))
    except Exception as e:
        logging.warning("Failed to parse %s: %s", path.name, e)
        return None
    if not post.metadata:
        return None
    return {
        "file": path.name,
        "metadata": post.metadata
    }


def read_all_books(books_dir: Path) -> list[dict]:
    """
    Read all .md files from books directory recursively.

    Args:
        books_dir: path to the folder with cards.

    Returns:
        List of parsed cards. Failed files are skipped (not in the list).
    """
    if not books_dir.exists():
        raise RuntimeError(f"Books directory not found: {books_dir}")

    cards = []
    for md_file in books_dir.rglob("*.md"):
        card = parse_card(md_file)
        if card is not None:
            cards.append(card)

    logging.info("Loaded %d book cards from %s", len(cards), books_dir)
    return cards


if __name__ == "__main__":
    from collections import Counter

    from config import get_books_dir

    cards = read_all_books(get_books_dir())

    # === Diagnostic 1: total counts ===
    print(f"\n=== Total ===")
    print(f"Total cards: {len(cards)}")

    migrated = sum(1 for c in cards if "migrated" in c["metadata"])
    not_migrated = len(cards) - migrated
    print(f"Migrated:     {migrated}")
    print(f"Not migrated: {not_migrated}")

    not_migrated_cards = [card["file"] for card in cards if not "migrated" in card["metadata"]]
    print(not_migrated_cards)

    # === Diagnostic 2: missing fields ===
    print(f"\n=== Missing fields ===")
    no_title = sum(1 for c in cards if not c["metadata"].get("Title"))
    no_authors = sum(1 for c in cards if not c["metadata"].get("Authors"))
    no_isbn = sum(1 for c in cards if not c["metadata"].get("ISBN"))
    no_year = sum(1 for c in cards if not c["metadata"].get("Year"))
    no_pages = sum(1 for c in cards if not c["metadata"].get("Pages"))
    no_publisher = sum(1 for c in cards if not c["metadata"].get("Publisher"))
    rows = [
        ["Without Title", no_title],
        ["Without Authors", no_authors],
        ["Without ISBN", no_isbn],
        ["Without Year", no_year],
        ["Without Pages", no_pages],
        ["Without Publisher", no_publisher],
    ]
    print(tabulate(rows, headers=["Название поля", "Количество"], tablefmt="fancy_grid"))

    # === Diagnostic 3: top publishers ===
    print(f"\n=== Top publishers ===")
    publishers = Counter()
    for card in cards:
        publisher = card["metadata"].get("Publisher")
        if publisher:
            publishers[publisher] += 1
    for publisher, count in publishers.most_common(10):
        print(f"  {publisher:35} {count}")

    # === Diagnostic 4: distribution by year ===
    print(f"\n=== Top years ===")
    years = Counter()
    for card in cards:
        year = card["metadata"].get("Year")
        if year:
            years[year] += 1
    for year, count in years.most_common(10):
        print(f"  {year}: {count}")

    # === Diagnostic 5: multiple authors ===
    print(f"\n=== Multi-author books ===")

    multi = [
        card for card in cards
        if isinstance(card["metadata"].get("Authors"), list)
        and len(card["metadata"]["Authors"]) > 1
    ]
    print(f"Books with multiple authors: {len(multi)}")
    for c in multi[:5]:
        authors = c["metadata"]["Authors"]
        print(f"  {c['file'][:50]:50} {authors}")

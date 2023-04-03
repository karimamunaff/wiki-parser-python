import os
from pathlib import Path
from datetime import datetime
from typing import List


def get_date_directories(parent_directory: Path) -> List[str]:
    available_dates = []
    for date_directory in parent_directory.iterdir():
        if not date_directory.is_dir:
            continue
        try:
            data_directory_datetime = datetime.strptime(date_directory.name, "%Y%m%d")
        except ValueError:
            continue
        available_dates.append(data_directory_datetime)
    return available_dates


def get_max_wiki_date(wiki_directory: Path) -> str:
    available_dates = get_date_directories(wiki_directory)
    if not available_dates:
        raise Exception(
            f"No wikipedia data found in {wiki_directory}, \
            download via 'make download_wikipedia' or 'make download_wikidata'"
        )
    max_date = max(available_dates)
    return f"{max_date.year}{max_date.month:02d}{max_date.day:02d}"


PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]

USER_DATA_DIRECTORY = os.environ.get("DATA_DIRECTORY")
DATA_DIRECTORY = Path(USER_DATA_DIRECTORY if USER_DATA_DIRECTORY else "data/")
WIKIPEDIA_DATA_DIRECTORY = DATA_DIRECTORY / "wikipedia"
WIKI_DATE = get_max_wiki_date(WIKIPEDIA_DATA_DIRECTORY)

ENWIKI_ARTICLES_BZ2_FILE = (
    WIKIPEDIA_DATA_DIRECTORY
    / WIKI_DATE
    / "enwiki"
    / f"enwiki-{WIKI_DATE}-pages-articles-multistream.xml.bz2"
)
WIKIDATA_ARTICLES_BZ2_FILE = (
    WIKIPEDIA_DATA_DIRECTORY
    / WIKI_DATE
    / "wikidatawiki"
    / f"wikidatawiki-{WIKI_DATE}-pages-articles-multistream.xml.bz2"
)

TEST_DATA_DIRECTORY = PROJECT_DIRECTORY / "tests" / "data"
SAMPLE_DUMPPAGE_CONTENT_FILE = TEST_DATA_DIRECTORY / "sample_dumppage_content"

# Folder where sqlite3 databases are stored
# contains wikipedia articles metadata information
# this includes redirects, qid lookups and wikidata property lookups
DATABASE_DIRECTORY = WIKIPEDIA_DATA_DIRECTORY / WIKI_DATE / "database"
DATABASE_DIRECTORY.mkdir(exist_ok=True)
METADATA_DATABASE_FILE = DATABASE_DIRECTORY / "wiki_articles_metadata"

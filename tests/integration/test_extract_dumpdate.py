from src.extract_dumpdate import _get_page_links
import datetime
from typing import List


def check_dumpstatus_page_links(dump_type: str, expected_text_links: List[str]) -> None:
    page_links = _get_page_links(f"https://dumps.wikimedia.org/{dump_type}/")
    date_links = (link for link in page_links if link not in expected_text_links)
    assert all(link in page_links for link in expected_text_links)
    for link in date_links:
        datetime.strptime(link, "%Y%m%d/")


def test_get_page_links() -> None:
    check_dumpstatus_page_links(
        dump_type="enwiki", expected_text_links=("../", "latest/")
    )
    check_dumpstatus_page_links(
        dump_type="wikidatawiki", expected_text_links=("../", "latest/", "entities/")
    )

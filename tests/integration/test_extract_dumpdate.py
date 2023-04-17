from src.dumpdate import _get_page_links, _date_to_string
from datetime import datetime, timedelta
from typing import List


def test_dumppage_links() -> None:
    expected_text_links = {
        "enwiki": ["../", "latest/"],
        "wikidatawiki": ["../", "latest/", "entities/"],
    }
    for wiki_project, expected_links in expected_text_links.items():
        page_links = _get_page_links(f"https://dumps.wikimedia.org/{wiki_project}/")
        assert check_expected_text_links(page_links, expected_links)
        assert check_last_month_in_dumpdates(page_links)


def check_expected_text_links(
    page_links: List[str], expected_text_links: List[str]
) -> bool:
    return all(link in page_links for link in expected_text_links)


def check_last_month_in_dumpdates(page_links: List[str]) -> None:
    """20th of last month is expected to be present in dump dates"""
    last_month_date = datetime.now().replace(day=1) - timedelta(days=1)
    last_month_date = last_month_date.replace(day=20)
    expected_dumpdate = _date_to_string(last_month_date) + "/"
    return expected_dumpdate in page_links

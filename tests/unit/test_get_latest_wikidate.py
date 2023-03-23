from src.get_latest_wikidate import (
    get_page_links,
    date_to_string,
    get_all_dates_sorted,
    is_dumpdate_complete,
    get_completed_wikimedia_dumpdate,
    get_date,
)
from datetime import date, datetime
from typing import List
from unittest.mock import patch


def check_dumpstatus_page_links(dump_type: str, expected_text_links: List[str]) -> None:
    page_links = get_page_links(f"https://dumps.wikimedia.org/{dump_type}/")
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


def test_date_to_string() -> None:
    assert date_to_string(date(2023, 3, 20)) == "20230320"


@patch("src.get_latest_wikidate.get_page_links")
def test_get_all_dates_sorted(mocked_get_page_links: callable) -> None:
    mocked_get_page_links.return_value = ["19890320/", "20200220/", "latest/"]
    expected_dates = (
        datetime(1989, 3, 20, 0, 0),
        datetime(2020, 2, 20, 0, 0),
    )
    obtained_dates = get_all_dates_sorted(url="dummy_url")
    assert all(date in obtained_dates for date in expected_dates)
    assert len(obtained_dates) == 2


@patch("requests.get")
def test_is_dumpdate_complete(mocked_requests_get: callable) -> None:
    mocked_requests_get.return_value.json.return_value = {
        "jobs": {"articlesdump": {"status": "done"}}
    }
    assert is_dumpdate_complete("dummy", "dummy")
    mocked_requests_get.return_value.json.return_value = {
        "jobs": {"articlesdump": {"status": "waiting"}}
    }
    assert not is_dumpdate_complete("dummy", "dummy")


@patch("src.get_latest_wikidate.get_all_dates_sorted")
@patch("src.get_latest_wikidate.is_dumpdate_complete")
def test_get_completed_wikimedia_dumpdate(
    mocked_is_dump_complete: callable,
    mocked_get_all_dates_sorted: callable,
) -> None:
    dummy_date = date(2023, 3, 1)
    mocked_get_all_dates_sorted.return_value = [dummy_date]
    mocked_is_dump_complete.return_value = True
    assert get_completed_wikimedia_dumpdate("dummy") == date(2023, 3, 1)
    mocked_is_dump_complete.return_value = False
    assert get_completed_wikimedia_dumpdate("dummy") is None


@patch("src.get_latest_wikidate.get_completed_wikimedia_dumpdate")
def test_get_date(mocked_completed_wikidate: callable) -> None:
    mocked_completed_wikidate.return_value = date(2023, 3, 1)
    assert get_date() == "20230301"

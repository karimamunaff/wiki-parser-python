from src.dumpdate import (
    _get_page_links,
    _date_to_string,
    get_dump_status_url,
    is_upload_done,
    get_dates_from_dumpurl,
    find_completed_dumpdates,
    get_recent,
    get_recent_wikidata,
    get_recent_wikipedia,
)
from datetime import date, datetime
from unittest.mock import patch
from src.paths import SAMPLE_DUMPPAGE_CONTENT_FILE
import pytest


@patch("requests.get")
def test_get_page_links(mocked_requests_get) -> None:
    mocked_requests_get.return_value.text = SAMPLE_DUMPPAGE_CONTENT_FILE.read_text()
    expected_output = [
        "../",
        "20221220/",
        "20230101/",
        "20230120/",
        "20230201/",
        "20230220/",
        "20230301/",
        "20230320/",
        "latest/",
    ]
    returned_output = _get_page_links("https://dummy.wiki/")
    assert returned_output == expected_output


def test_date_to_string() -> None:
    assert _date_to_string(date(2023, 3, 20)) == "20230320"


def test_get_dump_status_url() -> None:
    assert (
        get_dump_status_url("enwiki", date(year=2023, month=3, day=1))
        == "https://dumps.wikimedia.org/enwiki/20230301/dumpstatus.json"
    )


@patch("requests.get")
@patch("src.extract_dumpdate.get_dump_status_url")
def test_is_upload_done(
    mocked_dump_url: callable, mocked_requests_get: callable
) -> None:
    """Test both finished upload and in progress upload"""
    done_response = {"jobs": {"articlesdump": {"status": "done"}}}
    waiting_response = {"jobs": {"articlesdump": {"status": "waiting"}}}
    mocked_dump_url.return_value = "https://dummy.wiki"
    mocked_requests_get.return_value.json.return_value = done_response
    assert is_upload_done("dummy", "dummy")
    mocked_requests_get.return_value.json.return_value = waiting_response
    assert not is_upload_done("dummy", "dummy")


@patch("src.extract_dumpdate._get_page_links")
def test_get_dates_from_dumpurl(mocked_page_links: callable) -> None:
    mocked_page_links.return_value = ["20230301/", "20220301/", "20210201/"]
    expected_dates = [
        datetime.strptime(date_string, "%Y%m%d/")
        for date_string in mocked_page_links.return_value
    ]
    assert get_dates_from_dumpurl("dummy") == expected_dates


@patch("src.extract_dumpdate.is_upload_done")
@patch("src.extract_dumpdate.get_dates_from_dumpurl")
def test_no_dumpdate_found_error(
    mocked_dates: callable, mocked_is_upload_done: callable
) -> None:
    mocked_dates.return_value = [
        date(year=1989, month=5, day=3),
        date(year=1999, month=2, day=3),
    ]
    mocked_is_upload_done.return_value = False
    with pytest.raises(Exception):
        find_completed_dumpdates("dummy")


@patch("src.extract_dumpdate.is_upload_done")
@patch("src.extract_dumpdate.get_dates_from_dumpurl")
def test_find_completed_dumpdates(
    mocked_dates: callable, mocked_is_upload_done: callable
) -> None:
    mocked_dates.return_value = [
        date(year=1989, month=5, day=3),
        date(year=1999, month=2, day=3),
    ]
    mocked_is_upload_done.return_value = True
    assert find_completed_dumpdates("dummy") == mocked_dates.return_value


@patch("src.extract_dumpdate.find_completed_dumpdates")
def test_get_recent(mocked_completed_dates) -> None:
    mocked_completed_dates.return_value = [
        date(year=1989, month=5, day=3),
        date(year=1999, month=2, day=3),
    ]
    assert get_recent("dummy") == date(year=1999, month=2, day=3)
    assert get_recent_wikipedia() == date(year=1999, month=2, day=3)
    assert get_recent_wikidata() == date(year=1999, month=2, day=3)

from src.get_latest_wikidate import get_page_links, date_to_string
from datetime import date, datetime


def check_dumpstatus_page_links(dump_type, expected_text_links):
    page_links = get_page_links(f"https://dumps.wikimedia.org/{dump_type}/")
    date_links = (link for link in page_links if link not in expected_text_links)
    assert all(link in page_links for link in expected_text_links)
    for link in date_links:
        datetime.strptime(link, "%Y%m%d/")


def test_get_page_links():
    check_dumpstatus_page_links("enwiki", ("../", "latest/"))
    check_dumpstatus_page_links("wikidatawiki", ("../", "latest/", "entities/"))


def test_date_to_string():
    assert date_to_string(date(2023, 3, 20)) == "20230320"

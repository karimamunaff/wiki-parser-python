import re
from datetime import datetime
from typing import List
import requests

WIKI_DUMPS_URL = "https://dumps.wikimedia.org"


def _date_to_string(date: datetime) -> str:
    return f"{date.year}{date.month:02d}{date.day:02d}"


def _get_page_links(url: str) -> List[str]:
    url_content = requests.get(url).text
    return re.findall(r'href=[\'"]?([^\'" >]+)', url_content)


def get_dump_status_url(wiki_project: str, date: datetime) -> str:
    return f"{WIKI_DUMPS_URL}/{wiki_project}/{_date_to_string(date)}/dumpstatus.json"


def is_upload_done(wiki_project: str, date: datetime.date) -> bool:
    status_url = get_dump_status_url(wiki_project, date)
    status_json = requests.get(status_url).json()
    completion_status = status_json["jobs"]["articlesdump"]["status"]
    return completion_status == "done"


def get_dates_from_dumpurl(url: str) -> List[datetime]:
    page_links = _get_page_links(url)
    dates = []
    for date_link in page_links:
        try:
            date = datetime.strptime(date_link, "%Y%m%d/")
            dates.append(date)
        except ValueError:
            continue
    return dates


def find_completed_dumpdates(wiki_project: str) -> List[datetime.date]:
    dump_url = f"{WIKI_DUMPS_URL}/{wiki_project}/"
    completed_dumpdates = [
        date
        for date in get_dates_from_dumpurl(dump_url)
        if is_upload_done(wiki_project, date)
    ]
    if not completed_dumpdates:
        raise Exception(
            f"Can't find a valid wikimedia dump date for {wiki_project}."
            "Might be a bug. For a temporary resolution, "
            "Check https://dumps.wikimedia.org/wikidatawiki/ for wikidata"
            "and https://dumps.wikimedia.org/enwiki/ for wikipedia dates"
            "and specify it via env variable WIKI_DUMP_DATE"
        )
    return completed_dumpdates


def get_recent(wiki_project: str) -> str:
    return max(find_completed_dumpdates(wiki_project))


def get_recent_wikipedia() -> str:
    return get_recent("enwiki")


def get_recent_wikidata() -> str:
    return get_recent("wikidatawiki")


def _get_intersection(list_of_lists: List[List[datetime.date]]):
    return set.intersection(*map(set, list_of_lists))


def get_recent_common(wiki_projects: List[str] = ["enwiki", "wikidatawiki"]) -> str:
    """Get most recent completed dump date across all wiki projects"""
    completed_dates_all = [
        [dates for dates in find_completed_dumpdates(wiki_project)]
        for wiki_project in wiki_projects
    ]
    recent_common_date = max(_get_intersection(completed_dates_all))
    return _date_to_string(recent_common_date)

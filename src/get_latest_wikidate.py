import re
from datetime import datetime
from typing import List, Union
from urllib.request import urlopen

import requests


def get_page_links(url: str) -> List[str]:
    url_content = str(urlopen(url).read())
    return re.findall(r'href=[\'"]?([^\'" >]+)', url_content)


def get_all_dates_sorted(url: str) -> List[datetime]:
    page_links = get_page_links(url)
    dates = []
    for date_link in page_links:
        try:
            date = datetime.strptime(date_link, "%Y%m%d/")
            dates.append(date)
        except ValueError:
            continue
    return sorted(dates, reverse=True)


def is_dumpdate_complete(dump_type: str, date: str) -> bool:
    dump_status_url = f"https://dumps.wikimedia.org/{dump_type}/{date}/dumpstatus.json"
    date_status_json = requests.get(dump_status_url).json()
    article_dumps_status = date_status_json["jobs"]["articlesdump"]["status"]
    return article_dumps_status == "done"


def date_to_string(date: datetime) -> str:
    return f"{date.year}{date.month:02d}{date.day:02d}"


def get_completed_wikimedia_dumpdate(dump_type: str) -> Union[datetime.date, None]:
    dump_url = f"https://dumps.wikimedia.org/{dump_type}/"
    available_dates_sorted = get_all_dates_sorted(dump_url)
    completed_dumpdate = None
    for date in available_dates_sorted:
        date_string = date_to_string(date)
        if is_dumpdate_complete(dump_type, date_string):
            completed_dumpdate = date
            break
    return completed_dumpdate


def get_date() -> str:
    wikimedia_dump_types = ["enwiki", "wikidatawiki"]
    wikimedia_completed_dumpdates = []
    for dump_type in wikimedia_dump_types:
        completed_dumpdate = get_completed_wikimedia_dumpdate(dump_type)
        if not completed_dumpdate:
            raise Exception(f"can't find a valid wikimedia dump date for {dump_type}")
        wikimedia_completed_dumpdates.append(completed_dumpdate)
    valid_dump_date = min(wikimedia_completed_dumpdates)
    valid_dump_date = date_to_string(valid_dump_date)
    return valid_dump_date

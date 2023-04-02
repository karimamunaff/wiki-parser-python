import xml.etree.ElementTree as etree
from bz2 import BZ2File
from typing import Protocol
from dataclasses import dataclass
from logger import get_logger
from pathlib import Path

_LOGGER = get_logger(__file__)


@dataclass
class WikipediaArticle:
    title: str
    text: str
    is_redirect: bool


class Bz2Handler(Protocol):
    def iterate_articles():
        ...


class WikipediaBZ2Handler(Bz2Handler):
    @staticmethod
    def cleanup_xml_tag(tag: str) -> str:
        cleanup_till_index = tag.rfind("}")
        return tag[cleanup_till_index + 1 :] if cleanup_till_index != -1 else tag

    def iterate_articles(self, bz2_file: Path) -> WikipediaArticle:
        with BZ2File(bz2_file, "r") as xmlfile:
            current_title = ""
            for event, content in etree.iterparse(xmlfile, events=("start", "end")):
                if event == "start":
                    continue

                tag = self.cleanup_xml_tag(content.tag)

                # title
                if tag == "title":
                    current_title = content.text

                # article text
                elif (
                    tag == "text"
                    and (content.text is not None)
                    and (not content.text.startswith("#REDIRECT"))
                ):
                    yield WikipediaArticle(current_title, content.text, False)

                # redirect
                elif tag == "redirect":
                    yield WikipediaArticle(current_title, content.attrib["title"], True)

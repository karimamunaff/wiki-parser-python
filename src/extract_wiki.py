from lxml import etree
from bz2 import BZ2File
from typing import Protocol
from dataclasses import dataclass
from logger import get_logger
from pathlib import Path
from database import create_database, insert_article_and_redirect
from tqdm import tqdm
from paths import ENWIKI_ARTICLES_BZ2_FILE

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
        with BZ2File(
            bz2_file,
            "r",
        ) as xmlfile:
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
                # current_title is the redirect text
                # content.attrib["title"] is the article title being redirected to
                elif tag == "redirect":
                    yield WikipediaArticle(content.attrib["title"], current_title, True)
                content.clear()


def save_articles(xmlfile: BZ2File) -> None:
    _LOGGER.info("Saving redirects to database")
    create_database()
    bz2_handler = WikipediaBZ2Handler()
    progress_bar = tqdm()
    progress_bar.set_description("Inserting Articles Into Database ...")
    for article in bz2_handler.iterate_articles(xmlfile):
        insert_article_and_redirect(article.title, article.text, article.is_redirect)
        progress_bar.update(1)
    progress_bar.close()


if __name__ == "__main__":
    save_articles(ENWIKI_ARTICLES_BZ2_FILE)

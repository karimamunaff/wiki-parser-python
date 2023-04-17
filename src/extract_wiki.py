from bz2 import BZ2Decompressor, BZ2File
from io import BytesIO
from typing import Any, BinaryIO, List, Tuple

import ray
from lxml import etree
from tqdm import tqdm

from database import ArticlesTableColumns, Table
from paths import ENWIKI_ARTICLES_BZ2_FILE, ENWIKI_INDEX_BZ2_FILE

ray.init(address="auto")


def generate_article_columns(
    article_ids: List[int],
    article_titles: List[str],
    bz2_start_offset: int,
    bz2_end_offset: int,
    articles_chunk_index: int,
) -> List[ArticlesTableColumns]:
    return [
        ArticlesTableColumns(
            id=id,
            title=title,
            bz2_offset_start=bz2_start_offset,
            bz2_offset_end=bz2_end_offset,
            bz2_index_chunk_id=articles_chunk_index,
        )
        for id, title in zip(article_ids, article_titles)
    ]


def iterate_index_file(batch_size=1000) -> List[ArticlesTableColumns]:
    with BZ2File(ENWIKI_INDEX_BZ2_FILE, "r") as index_file:
        previous_offset = -1
        article_columns_collection = []
        article_titles_collection = []
        article_ids_collection = []
        for line_number, line in enumerate(index_file):
            line_splits = line.decode("utf-8").replace("\n", "").split(":")
            current_offset, article_id, article_title = (
                int(line_splits[0]),
                int(line_splits[1]),
                ":".join(line_splits[2:]),
            )
            article_titles_collection.append(article_title)
            article_ids_collection.append(article_id)
            if line_number == 0:
                previous_offset = current_offset
            if current_offset != previous_offset:
                article_columns_collection.extend(
                    generate_article_columns(
                        article_ids_collection,
                        article_titles_collection,
                        previous_offset,
                        current_offset,
                        line_number,
                    )
                )
                article_ids_collection = []
                article_titles_collection = []
                previous_offset = current_offset
            if int(len(article_columns_collection) / batch_size) == 1:
                yield article_columns_collection
                article_columns_collection = []
    # last chunk of articles, offset end in this case is the last byte of the file (-1)
    article_columns_collection.extend(
        generate_article_columns(
            article_ids_collection,
            article_titles_collection,
            previous_offset,
            -1,
            line_number,
        )
    )
    yield article_columns_collection


def store_article_basics(batch_size=1000000):
    """
    Store article basics from pages-articles-multistream-index.txt.bz2
    for each article, this function stores the following data
    - aricle id and title name
    - offset start/end of article chunks (100 articles per chunk),
    - index of article inside a chunk
    """
    database_table = Table(name="articles", columns=ArticlesTableColumns())
    database_table.create()
    progress_bar = tqdm()
    progress_bar.set_description("Inserting article basics to database ...")
    for article_columns_colection in iterate_index_file(batch_size):
        database_table.insert(article_columns_colection, batch_size=batch_size)
        progress_bar.update(batch_size)
    progress_bar.close()


def extract_columns_from_xml(
    xml_string: bytes, return_text: bool = False
) -> List[ArticlesTableColumns]:
    xml_string = b"<root> " + xml_string + b" </root>"
    parsed_xml = etree.parse(BytesIO(xml_string))
    extracted_article_columns = [
        ArticlesTableColumns.from_xml_page(article_page, return_text)
        for article_page in parsed_xml.xpath("page")
    ]
    return extracted_article_columns


def decompress_between_offsets(
    bz2_file: BinaryIO, offset_start: int, offset_end: int
) -> str:
    bz2_file.seek(offset_start)
    article_text_bytes = bz2_file.read(offset_end - offset_start)
    article_text_xml = BZ2Decompressor().decompress(article_text_bytes)
    return article_text_xml


@ray.remote
def get_article_columns_between(
    offset_start: int,
    offset_end: int,
    return_text: bool = False,
) -> List[ArticlesTableColumns]:
    with open(ENWIKI_ARTICLES_BZ2_FILE, "rb") as bz2_file:
        article_texts_xml = decompress_between_offsets(
            bz2_file, offset_start, offset_end
        )
        article_columns_collection = extract_columns_from_xml(
            article_texts_xml, return_text
        )
    return article_columns_collection


def get_batch(data: List[Any], batch_size: int = 1000):
    total_length = len(data)
    for index in range(0, total_length, batch_size):
        yield data[index : min(index + batch_size, total_length)]


def get_article_basics() -> List[Tuple[int, int, int]]:
    articles_database = Table(name="articles", columns=ArticlesTableColumns())
    article_basic_data = articles_database.select_query(
        "select distinct bz2_offset_start, bz2_offset_end from articles"
    )
    return article_basic_data


@ray.remote
def update_article_metadata_batch(
    article_basic_batch: List[Tuple[int, int, int]], store_raw_text: bool = False
) -> None:
    articles_database = Table(name="articles", columns=ArticlesTableColumns())

    article_columns = [
        get_article_columns_between.remote(
            offset_start, offset_end, return_text=store_raw_text
        )
        for (offset_start, offset_end) in article_basic_batch
    ]
    article_columns = ray.get(article_columns)
    article_columns = [column for chunk in article_columns for column in chunk]
    column_names_to_update = ArticlesTableColumns().post_update_columns
    updated_values = [
        [column.__dict__[name] for name in column_names_to_update]
        for column in article_columns
    ]
    articles_database.update(
        column_names=column_names_to_update,
        updated_values=updated_values,
        indices=[column.id for column in article_columns],
    )


def update_article_metadata(
    batch_size: int = 100, store_raw_text: bool = False
) -> None:
    """
    metadata information extracted from pages-articles-multistream.xml.bz2
    This includes the following information stored in database,
    - redirected article title if article is a redirect
    - total number of hyperlinks in article text
    - total characters in article text
    - short description of the article
    - 'good article' tag from wikipedia
    - namespace id of the article
    - total sections + subsections in article text
    - article text if store_raw_text is set to True

    """
    article_basics = get_article_basics()
    print
    ray.get(
        [
            update_article_metadata_batch.remote(batch, store_raw_text)
            for batch in get_batch(article_basics, batch_size=batch_size)
        ]
    )


def store_article_metadata() -> None:
    """
    Store all relevant artile metadata to database
    Wikipedia offers two types of dump files
        1. pages-articles-multistream.xml.bz2
           Huge file containing article text + additional metadata
        2. pages-articles-multistream-index.txt.bz2
           Contains article id, article title and byte offset
           byte offset corresponds to the location of article (chunk) inside 1

    We first store all the basics (id, title and byte offsets).
    We then use the stored article offsets to get more metadata from 1 in parallel
    """
    store_article_basics(batch_size=1000000)
    update_article_metadata(batch_size=100)


if __name__ == "__main__":
    store_article_metadata()

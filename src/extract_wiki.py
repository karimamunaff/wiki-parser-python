from lxml import etree
from bz2 import BZ2File
from paths import ENWIKI_INDEX_BZ2_FILE
from database import ArticlesTableColumns, Table
from tqdm import tqdm
from typing import List


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
    database_table = Table(name="articles", columns=ArticlesTableColumns())
    database_table.create()
    progress_bar = tqdm()
    progress_bar.set_description("Inserting article basics to database ...")
    for article_columns_colection in iterate_index_file(batch_size):
        database_table.insert(article_columns_colection, batch_size=batch_size)
        progress_bar.update(batch_size)
    progress_bar.close()


if __name__ == "__main__":
    store_article_basics(batch_size=1000000)

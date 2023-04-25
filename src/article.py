from typing import List, Tuple, Any, Dict
from database import ArticlesTableColumns, Table
from store import get_article_columns_between
import ray

if not ray.is_initialized():
    ray.init(address="auto")


def get_from_database(
    select_query: str, arguments: List[Any] = []
) -> List[Tuple[str, int, int]]:
    articles_database = Table(name="articles", columns=ArticlesTableColumns())
    return articles_database.execute(select_query, arguments)


@ray.remote
def get_raw_text_from(offset_start: int, offset_end: int) -> str:
    """todo: rewrite this using chunk_id instead of article_id"""
    article_columns_chunk = ray.get(
        get_article_columns_between.remote(offset_start, offset_end, return_text=True)
    )
    return article_columns_chunk


def get_raw_text(titles: List[str]) -> Dict[str, str]:
    offset_chunk_select_query = f"SELECT title, bz2_offset_start, bz2_offset_end FROM articles WHERE title in ({','.join(['?']*len(titles))})"
    offset_chunk_ids = get_from_database(offset_chunk_select_query, titles)
    if not offset_chunk_ids:
        return [""] * len(titles)
    unique_offsets = list(set((offsets[1], offsets[2]) for offsets in offset_chunk_ids))
    article_columns_chunk = [
        get_raw_text_from.remote(offset_start, offset_end)
        for offset_start, offset_end in unique_offsets
    ]
    return {
        columns.title: columns.text
        for columns_chunk in ray.get(article_columns_chunk)
        for columns in columns_chunk
        if columns.title in titles
    }


a = get_raw_text(["Barcelona", "Chevrolet Malibu"])
print(a[1][:2000])

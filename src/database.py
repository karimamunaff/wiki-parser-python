import sqlite3
from typing import List, Tuple, Any
from logger import get_logger
from paths import METADATA_DATABASE_FILE

_LOGGER = get_logger(__file__)


def execute_database(
    sql_statement: str, commit: bool = False, values: List[Any] = []
) -> List[Tuple]:
    connection = sqlite3.Connection(METADATA_DATABASE_FILE)
    cursor = connection.cursor()
    cursor.execute(sql_statement, values)
    result = cursor.fetchall()
    if commit:
        connection.commit()
    connection.close()
    return result


def create_redirects_table() -> None:
    sql_statement = """
          CREATE TABLE IF NOT EXISTS redirects
          ([redirect_id] INTEGER PRIMARY KEY NOT NULL,
          [redirect_name] TEXT NOT NULL UNIQUE,
          [article_id] INTEGER NOT NULL
          )
          """
    execute_database(sql_statement, commit=True)


def create_articles_table() -> None:
    sql_statement = """
          CREATE TABLE IF NOT EXISTS articles
          ([article_id] INTEGER PRIMARY KEY NOT NULL, 
          [article_title] TEXT NOT NULL UNIQUE
          )
          """
    execute_database(sql_statement, commit=True)


def create_database() -> None:
    create_articles_table()
    create_redirects_table()


def insert_article_title(name: str) -> None:
    sql_statement = """INSERT OR IGNORE INTO articles (article_title) VALUES (?)"""
    return execute_database(sql_statement, values=[name], commit=True)


def insert_article_text(text: str) -> None:
    pass


def insert_and_get_article_id(article_title: str, article_text: str) -> int:
    insert_article_title(article_title)
    insert_article_text(article_text)
    sql_statement = """SELECT article_id FROM articles WHERE article_title = (?)"""
    return execute_database(sql_statement, values=[article_title])


def insert_redirect(redirect_name: str, article_id: int) -> None:
    sql_statement = (
        """INSERT INTO redirects (redirect_name, article_id) VALUES (?, ?)"""
    )
    return execute_database(
        sql_statement, values=[redirect_name, article_id], commit=True
    )


def insert_article_and_redirect(
    article_title: str, article_text: str, is_redirect: bool
) -> None:
    article_id = insert_and_get_article_id(article_title, article_text)
    if is_redirect:
        insert_redirect(redirect_name=article_text, article_id=article_id[0][0])

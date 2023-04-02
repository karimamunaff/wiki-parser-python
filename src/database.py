import sqlite3
from extract_wiki import WikipediaBZ2Handler, WikipediaArticle
from bz2 import BZ2File
from typing import List, Tuple, Any, Union


REDIRECTS_DATABASE_NAME = "redirects"


def execute_database(
    sql_statement: str, commit: bool = False, values: List[Any] = []
) -> List[Tuple]:
    connection = sqlite3.Connection(REDIRECTS_DATABASE_NAME)
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
          [article_name] TEXT NOT NULL UNIQUE
          )
          """
    execute_database(sql_statement, commit=True)


def create_database() -> None:
    create_articles_table()
    create_redirects_table()


def insert_article(name: str) -> None:
    sql_statement = """INSERT OR IGNORE INTO articles (article_name) VALUES (?)"""
    return execute_database(sql_statement, values=[name], commit=True)


def insert_and_get_article(article_name: str) -> int:
    insert_article(article_name)
    sql_statement = """SELECT article_id FROM articles WHERE article_name = (?)"""
    return execute_database(sql_statement, values=[article_name])


def insert_redirect(redirect_name: str, article_id: int) -> None:
    sql_statement = (
        """INSERT INTO redirects (redirect_name, article_id) VALUES (?, ?)"""
    )
    return execute_database(
        sql_statement, values=[redirect_name, article_id], commit=True
    )


def insert_article_and_redirect(article: WikipediaArticle) -> None:
    if not article.is_redirect:
        return
    article_id = insert_and_get_article(article_name=article.text)
    insert_redirect(redirect_name=article.title, article_id=article_id[0][0])


def save_redirects(xmlfile: BZ2File):
    create_database()
    bz2_handler = WikipediaBZ2Handler()
    for article in bz2_handler.iterate_articles(xmlfile):
        insert_article_and_redirect(article)

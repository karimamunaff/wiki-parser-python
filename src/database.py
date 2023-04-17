import sqlite3
from typing import List, Tuple, Protocol, Union
from paths import METADATA_DATABASE_FILE
from dataclasses import dataclass, field
from lxml import etree
import re
from regex_collection import (
    LINKS_REGEX,
    SECTIONS_AND_SUBSECTIONS_REGEX,
    SHORT_DESCRPTION_REGEX,
)


@dataclass
class DatabaseQuery:
    query: str
    arguments: List[Tuple] = field(default_factory=lambda: [])
    commit: bool = False
    fetch: bool = False

    @staticmethod
    def get_batch(arguments, batch_size=1):
        total_length = len(arguments)
        for index in range(0, total_length, batch_size):
            yield arguments[index : min(index + batch_size, total_length)]

    def execute_batch(
        self,
        connection: sqlite3.Connection,
        cursor: sqlite3.Cursor,
        arguments_batch: List[Tuple] = [],
    ) -> List[Tuple]:
        result = []
        if not arguments_batch:
            cursor.execute(self.query)
        else:
            cursor.executemany(self.query, arguments_batch)
        if self.fetch:
            result = cursor.fetchall()
        if self.commit:
            connection.commit()
        return result

    def execute(self, batch_size=100) -> List[Tuple]:
        """
        If arguments == [], this just executes the query e.g. create table query
        If arguments != [], this generates query results in batches
        """
        results = []
        connection = sqlite3.Connection(METADATA_DATABASE_FILE)
        cursor = connection.cursor()
        if not self.arguments:
            return self.execute_batch(connection, cursor)
        for arguments_batch in self.get_batch(self.arguments, batch_size):
            results_batch = self.execute_batch(connection, cursor, arguments_batch)
            results.extend(results_batch)
        connection.close()
        return results


@dataclass
class ColumnConfiguration:
    name: str
    data_type: str = "INTEGER"
    primary_key: bool = False
    unique: bool = False
    not_null: bool = False

    def create_query_suffix(self) -> str:
        """
        get suffix needed to create sql table using create query
        e.g. id INTEGER PRIMARY KEY NOT_NULL
        this would then appended to create sql command while creating table
        """
        suffix = f"[{self.name}] {self.data_type}"
        if self.primary_key:
            suffix += " PRIMARY KEY"
        if self.not_null:
            suffix += " NOT NULL"
        if self.unique:
            suffix += " UNIQUE"
        return suffix


class TableColumns(Protocol):
    """
    Common Type Annotation for table columns of all tables
    """

    @property
    def primary_key(self) -> str:
        ...

    @property
    def not_null_columns(self) -> List[str]:
        ...

    @property
    def unique_columns(self) -> List[str]:
        ...

    @property
    def column_names(self) -> Tuple[str]:
        ...

    @property
    def column_values(self):
        ...


@dataclass
class ArticlesTableColumns:
    id: int = None
    title: str = None
    text: str = None
    bz2_offset_start: int = None
    bz2_offset_end: int = None
    bz2_index_chunk_id: int = None
    namespace_id: int = None
    redirected_article_title: str = None
    is_good_article: bool = None
    short_description: str = None
    total_links: int = None
    total_characters: int = None
    total_sections: int = None

    @property
    def primary_key(self) -> str:
        # todo: get this from variable names above
        return "id"

    @property
    def not_null_columns(self) -> List[str]:
        return ["title"]

    @property
    def unique_columns(self) -> List[str]:
        return []

    @property
    def column_names(self) -> Tuple[str]:
        return sorted(list(self.__dict__.keys()))

    @property
    def column_values(self):
        return tuple(self.__dict__[name] for name in self.column_names)

    @classmethod
    def from_xml_page(cls, article_page: etree._Element, return_text: bool = False):
        redirect = article_page.xpath("redirect")
        redirected_title = redirect[0].attrib["title"] if redirect else None
        article_text = article_page.xpath("revision")[0].xpath("text")[0].text
        article_text = "" if article_text is None else article_text
        short_description = re.findall(SHORT_DESCRPTION_REGEX, article_text)
        short_description = short_description[0] if len(short_description) > 0 else None
        return cls(
            id=int(article_page.xpath("id")[0].text),
            title=article_page.xpath("title")[0].text,
            text=article_text if return_text else None,
            redirected_article_title=redirected_title,
            namespace_id=int(article_page.xpath("ns")[0].text),
            is_good_article="{{good article}}" in article_text,
            short_description=short_description,
            total_links=len(re.findall(LINKS_REGEX, article_text)),
            total_characters=len(article_text),
            total_sections=len(
                re.findall(SECTIONS_AND_SUBSECTIONS_REGEX, article_text)
            ),
        )

    @property
    def basic_columns(self):
        """these columns are updated using information from bz2 index file"""
        return [
            "id",
            "title",
            "bz2_offset_start",
            "bz2_offset_end",
            "bz2_index_chunk_id",
        ]

    @property
    def post_update_columns(self):
        """
        these columns are not updated using index bz2 file
        but later using the bigger articles bz2 file
        """
        return [
            column
            for column in self.__annotations__.keys()
            if column not in self.basic_columns
        ]


@dataclass
class Table:
    name: str
    columns: TableColumns

    def generate_column_configurations(self):
        column_configurations = []
        for column_name, column_data_type in self.columns.__annotations__.items():
            sql_data_type = "INTEGER" if column_data_type == int else "TEXT"
            configuration = ColumnConfiguration(
                name=column_name,
                data_type=sql_data_type,
                primary_key=column_name == self.columns.primary_key,
                not_null=column_name in self.columns.not_null_columns,
                unique=column_name in self.columns.unique_columns,
            )
            column_configurations.append(configuration)
        return column_configurations

    def get_create_query(self) -> None:
        column_configurations = self.generate_column_configurations()
        query = f"CREATE TABLE IF NOT EXISTS {self.name} ("
        for column in column_configurations:
            query += f"{column.create_query_suffix()},"
        query = query[:-1]
        query += ")"
        return query

    def create(self) -> None:
        query = self.get_create_query()
        DatabaseQuery(query=query, commit=True).execute()

    def insert(
        self, columns_collection: List[TableColumns], batch_size: int = 1000
    ) -> None:
        column_names = columns_collection[0].column_names
        column_values_collection = [
            columns.column_values for columns in columns_collection
        ]
        DatabaseQuery(
            query=f"INSERT IGNORE INTO {self.name} ({','.join(column_names)}) \
                    VALUES ({','.join(['?']*len(column_names))})",
            arguments=column_values_collection,
            commit=True,
        ).execute(batch_size)

    def update(
        self,
        column_names: List[str],
        updated_values: List[List[Union[int, str]]],
        indices: List[int],
        batch_size: int = 1000,
    ) -> None:
        query_arguments = [values + [id] for values, id in zip(updated_values, indices)]
        set_string = (
            " = ?, ".join(column_names)
            if len(column_names) > 1
            else f"{column_names[0]} = ?"
        )
        set_string += " = ?"
        DatabaseQuery(
            query=f"UPDATE {self.name} SET {set_string} WHERE id = ?;",
            arguments=query_arguments,
            commit=True,
        ).execute(batch_size)

    def select(self, column_names: List[str]) -> None:
        return DatabaseQuery(
            query=f"SELECT {','.join(column_names)} FROM {self.name}", fetch=True
        ).execute()

    def select_query(self, query: str, batch_size: int = 10000) -> None:
        return DatabaseQuery(query=query, fetch=True).execute(batch_size)


def test():
    a = Table(name="articles", columns=ArticlesTableColumns())
    a.create()
    a.insert(
        [
            ArticlesTableColumns(id=1, title="test"),
            ArticlesTableColumns(id=2, title="test2"),
        ]
    )
    a.update(column_names=["title"], updated_values=[["test5"]], indices=[1])
    print(a.select(column_names=["title"]))

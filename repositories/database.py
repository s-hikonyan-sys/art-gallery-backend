"""データベース接続管理.

データベース接続の取得と管理を担当します。
コンテキストマネージャーを使用して、リソースの適切な管理を保証します。"""

from contextlib import contextmanager
from typing import Generator

import psycopg2
from config import Config
from psycopg2.extras import RealDictCursor


class Database:
    """データベース接続管理クラス.

    シングルトンパターン的なアプローチで、データベース接続を管理します。
    コンテキストマネージャーを使用することで、接続の確実なクローズを保証します。"""

    @staticmethod
    @contextmanager
    def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
        """データベース接続を取得するコンテキストマネージャー.

        Usage:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM artworks")
                results = cursor.fetchall()

        Yields:
            psycopg2接続オブジェクト

        Raises:
            psycopg2.Error: データベース接続エラー"""
        conn = None
        try:
            conn = psycopg2.connect(**Config.get_db_config())
            yield conn
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    @contextmanager
    def get_cursor(
        cursor_factory=None,
    ) -> Generator[psycopg2.extensions.cursor, None, None]:
        """カーソルを取得するコンテキストマネージャー.

        Usage:
            with Database.get_cursor(RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM artworks")
                results = cursor.fetchall()

        Args:
            cursor_factory: カーソルファクトリー（デフォルト: RealDictCursor）

        Yields:
            psycopg2カーソルオブジェクト"""
        with Database.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory or RealDictCursor)
            try:
                yield cursor
            finally:
                cursor.close()

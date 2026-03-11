import time
from contextlib import contextmanager
from typing import Generator, Any, Optional
from enum import Enum
import dataclasses

import psycopg2
from psycopg2.extras import RealDictCursor
from my_properties import MyProperties


# 接続試行の結果タイプを定義するEnum
class ConnectionResultType(Enum):
    SUCCESS = "success"
    RETRYABLE_FAILURE = "retryable_failure"
    FATAL_FAILURE = "fatal_failure"

# 接続試行の具体的な結果を格納するデータクラス
@dataclasses.dataclass
class ConnectionAttemptResult:
    type: ConnectionResultType
    connection: Optional[psycopg2.extensions.connection] = None  # 成功時のみ
    exception: Optional[Exception] = None # 失敗時のみ

class ManagedConnection:
    """psycopg2の接続オブジェクトをラップし、トランザクション管理と自動クローズを行うコンテキストマネージャ."""
    def __init__(self, conn: psycopg2.extensions.connection):
        self._conn = conn

    def __enter__(self) -> psycopg2.extensions.connection:
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            # 例外がなければコミット
            self._conn.commit()
        else:
            # 例外があればロールバック
            self._conn.rollback()
        
        # 接続を閉じる
        self._conn.close()
        
        # 例外を再スローするために False を返す
        return False 

class Database:
    """データベース接続管理クラス.

    シングルトンパターン的なアプローチで、データベース接続を管理します。
    コンテキストマネージャーを使用することで、接続の確実なクローズを保証します。"""

    @classmethod
    def _try_get_single_connection(cls) -> ConnectionAttemptResult:
        """一度のデータベース接続試行を行い、結果を ConnectionAttemptResult で返す."""
        try:
            conn = psycopg2.connect(**MyProperties.get_db_config())
            return ConnectionAttemptResult(type=ConnectionResultType.SUCCESS, connection=conn)
        except psycopg2.OperationalError as e:
            # リトライ対象のOperationalErrorかどうかをチェック
            if "could not translate host name" in str(e) or "Is the server running" in str(e):
                return ConnectionAttemptResult(type=ConnectionResultType.RETRYABLE_FAILURE, exception=e)
            else:
                return ConnectionAttemptResult(type=ConnectionResultType.FATAL_FAILURE, exception=e)
        except Exception as e:
            # その他の予期せぬエラー
            return ConnectionAttemptResult(type=ConnectionResultType.FATAL_FAILURE, exception=e)

    @staticmethod
    @contextmanager
    def get_connection(max_retries: int = 10, retry_delay: float = 2.0) -> Generator[psycopg2.extensions.connection, None, None]:
        """データベース接続を取得するコンテキストマネージャー（リトライ付き）.

        Usage:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM artworks")
                results = cursor.fetchall()

        Yields:
            psycopg2接続オブジェクト

        Raises:
            psycopg2.Error: データベース接続エラー"""
        
        for attempt in range(max_retries):
            result = Database._try_get_single_connection()

            match result.type:
                case ConnectionResultType.SUCCESS:
                    # 接続成功。ManagedConnectionのインスタンスをyieldする
                    with ManagedConnection(result.connection) as conn:
                        yield conn
                    return # ManagedConnection.__exit__ 処理後、コンテキストを抜ける

                case ConnectionResultType.RETRYABLE_FAILURE if attempt < max_retries - 1:
                    print(f"DEBUG: データベース接続失敗 (試行 {attempt + 1}/{max_retries}): {result.exception}")
                    time.sleep(retry_delay * (2 ** attempt)) # 指数バックオフ
                    # ここで continue は不要（次のループの反復へ自動的に進む）
                
                case ConnectionResultType.RETRYABLE_FAILURE: # 上のパターンにマッチしなかった場合（リトライ回数超過）
                    print(f"DEBUG: データベース接続最大リトライ回数を超過: {result.exception}")
                    raise psycopg2.OperationalError(
                        f"データベース接続に失敗しました: {result.exception}"
                    ) from result.exception
                
                case ConnectionResultType.FATAL_FAILURE:
                    # リトライ不可能なエラーまたはその他の例外の場合
                    print(f"DEBUG: データベース接続予期せぬエラー (リトライなし): {result.exception}")
                    raise result.exception # 元の例外を再スロー
        
        # ここには到達しないはずだが、念のため（IDEの警告を避けるため）
        raise RuntimeError("get_connectionメソッドが予期せぬ状態で終了しました。")

    @staticmethod
    @contextmanager
    def get_cursor(
        cursor_factory: Any = None,
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
        # get_connection のコンテキストマネージャを利用して接続を取得
        with Database.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory or RealDictCursor)
            try:
                yield cursor
            finally:
                cursor.close()

"""作品リポジトリ.

作品エンティティの永続化を担当します。
リポジトリパターンにより、データアクセスの詳細をドメイン層から分離します。"""

from typing import List, Optional

from domain.artwork import Artwork
from psycopg2.extras import RealDictCursor
from repositories.database import Database


class ArtworkRepository:
    """作品リポジトリクラス.

    作品エンティティのCRUD操作を提供します。
    リポジトリパターンの実装により、ドメイン層とデータアクセス層を分離します。"""

    @staticmethod
    def find_all(
        featured: Optional[bool] = None, sold: Optional[bool] = None
    ) -> List[Artwork]:
        """すべての作品を取得.

        Args:
            featured: おすすめ作品でフィルタリング（Noneの場合はフィルタリングしない）
            sold: 販売済みでフィルタリング（Noneの場合はフィルタリングしない）

        Returns:
            作品エンティティのリスト"""
        query = "SELECT * FROM artworks WHERE 1=1"
        params = []

        if featured is not None:
            query += " AND is_featured = %s"
            params.append(featured)

        if sold is not None:
            query += " AND is_sold = %s"
            params.append(sold)

        query += " ORDER BY created_at DESC"

        with Database.get_cursor(RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [Artwork.from_dict(dict(row)) for row in results]

    @staticmethod
    def find_by_id(artwork_id: int) -> Optional[Artwork]:
        """IDで作品を検索.

        Args:
            artwork_id: 作品ID

        Returns:
            見つかった場合はArtworkエンティティ、見つからない場合はNone"""
        with Database.get_cursor(RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM artworks WHERE id = %s", (artwork_id,))
            result = cursor.fetchone()

            if result:
                return Artwork.from_dict(dict(result))
            return None

    @staticmethod
    def find_title_by_id(artwork_id: int) -> Optional[str]:
        """作品IDからタイトルのみを取得（軽量なクエリ）.

        Args:
            artwork_id: 作品ID

        Returns:
            作品タイトル、見つからない場合はNone"""
        with Database.get_cursor() as cursor:
            cursor.execute("SELECT title FROM artworks WHERE id = %s", (artwork_id,))
            result = cursor.fetchone()

            if result:
                title = result[0]
                return str(title) if title is not None else None
            return None

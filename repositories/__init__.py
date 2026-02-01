"""リポジトリパッケージ.

データアクセス層を定義します。リポジトリパターンにより、
ドメインモデルとデータベースの詳細を分離します。"""

from .artwork_repository import ArtworkRepository
from .database import Database

__all__ = ["ArtworkRepository", "Database"]

"""作品サービス.

作品に関するビジネスロジックを実装します。
リポジトリを利用してデータアクセスを行い、ドメインロジックを実行します。"""

from typing import List, Optional

from domain.artwork import Artwork
from repositories.artwork_repository import ArtworkRepository


class ArtworkService:
    """作品サービスクラス.

    作品に関するビジネスロジックを提供します。
    サービス層は、複数のリポジトリを組み合わせたり、
    トランザクション管理を行ったりする責務を持ちます。"""

    def __init__(self, repository: Optional[ArtworkRepository] = None):
        """コンストラクタ.

        Args:
            repository: 作品リポジトリ（デフォルト: ArtworkRepository）
                      依存性注入により、テスト時にモックを注入可能"""
        self.repository = repository or ArtworkRepository()

    def get_all_artworks(
        self, featured: Optional[bool] = None, sold: Optional[bool] = None
    ) -> List[Artwork]:
        """すべての作品を取得.

        Args:
            featured: おすすめ作品でフィルタリング
            sold: 販売済みでフィルタリング

        Returns:
            作品エンティティのリスト"""
        return self.repository.find_all(featured=featured, sold=sold)

    def get_artwork_by_id(self, artwork_id: int) -> Optional[Artwork]:
        """IDで作品を取得.

        Args:
            artwork_id: 作品ID

        Returns:
            作品エンティティ、見つからない場合はNone

        Raises:
            ValueError: 作品が見つからない場合"""
        artwork = self.repository.find_by_id(artwork_id)
        if not artwork:
            raise ValueError(f"作品ID {artwork_id} が見つかりません")
        return artwork

    def get_featured_artworks(self) -> List[Artwork]:
        """おすすめ作品を取得.

        Returns:
            おすすめ作品のリスト"""
        return self.repository.find_all(featured=True)

    def get_available_artworks(self) -> List[Artwork]:
        """購入可能な作品を取得.

        Returns:
            購入可能な作品のリスト"""
        return self.repository.find_all(sold=False)

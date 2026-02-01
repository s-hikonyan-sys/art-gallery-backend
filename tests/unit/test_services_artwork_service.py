"""
作品サービスのユニットテスト

モックリポジトリを使用してビジネスロジックをテストします。
"""

import pytest
from unittest.mock import Mock, patch
from services.artwork_service import ArtworkService
from domain.artwork import Artwork
from decimal import Decimal


@pytest.mark.unit
class TestArtworkService:
    """作品サービスのテストクラス"""

    def test_get_all_artworks(self):
        """すべての作品を取得する機能をテスト"""
        # モックリポジトリの作成
        mock_repository = Mock()
        mock_artworks = [
            Artwork(
                id=1,
                title="作品1",
                description=None,
                image_url=None,
                price=Decimal("50000"),
                size=None,
                medium=None,
                year=None,
            ),
            Artwork(
                id=2,
                title="作品2",
                description=None,
                image_url=None,
                price=Decimal("80000"),
                size=None,
                medium=None,
                year=None,
            ),
        ]
        mock_repository.find_all.return_value = mock_artworks

        # サービスの作成（モックリポジトリを注入）
        service = ArtworkService(repository=mock_repository)

        # テスト実行
        result = service.get_all_artworks()

        # 検証
        assert len(result) == 2
        assert result[0].title == "作品1"
        assert result[1].title == "作品2"
        mock_repository.find_all.assert_called_once_with(featured=None, sold=None)

    def test_get_all_artworks_with_filters(self):
        """フィルタリング機能をテスト"""
        mock_repository = Mock()
        mock_artworks = [
            Artwork(
                id=1,
                title="おすすめ作品",
                description=None,
                image_url=None,
                price=None,
                size=None,
                medium=None,
                year=None,
                is_featured=True,
            )
        ]
        mock_repository.find_all.return_value = mock_artworks

        service = ArtworkService(repository=mock_repository)

        result = service.get_all_artworks(featured=True)

        assert len(result) == 1
        assert result[0].is_featured is True
        mock_repository.find_all.assert_called_once_with(featured=True, sold=None)

    def test_get_artwork_by_id_success(self):
        """IDで作品を取得する機能をテスト（成功ケース）"""
        mock_repository = Mock()
        mock_artwork = Artwork(
            id=1,
            title="テスト作品",
            description=None,
            image_url=None,
            price=Decimal("50000"),
            size=None,
            medium=None,
            year=None,
        )
        mock_repository.find_by_id.return_value = mock_artwork

        service = ArtworkService(repository=mock_repository)

        result = service.get_artwork_by_id(1)

        assert result.id == 1
        assert result.title == "テスト作品"
        mock_repository.find_by_id.assert_called_once_with(1)

    def test_get_artwork_by_id_not_found(self):
        """IDで作品を取得する機能をテスト（見つからないケース）"""
        mock_repository = Mock()
        mock_repository.find_by_id.return_value = None

        service = ArtworkService(repository=mock_repository)

        with pytest.raises(ValueError, match="作品ID 1 が見つかりません"):
            service.get_artwork_by_id(1)

    def test_get_featured_artworks(self):
        """おすすめ作品を取得する機能をテスト"""
        mock_repository = Mock()
        mock_artworks = [
            Artwork(
                id=1,
                title="おすすめ作品",
                description=None,
                image_url=None,
                price=None,
                size=None,
                medium=None,
                year=None,
                is_featured=True,
            )
        ]
        mock_repository.find_all.return_value = mock_artworks

        service = ArtworkService(repository=mock_repository)

        result = service.get_featured_artworks()

        assert len(result) == 1
        assert result[0].is_featured is True
        mock_repository.find_all.assert_called_once_with(featured=True)

    def test_get_available_artworks(self):
        """購入可能な作品を取得する機能をテスト"""
        mock_repository = Mock()
        mock_artworks = [
            Artwork(
                id=1,
                title="購入可能作品",
                description=None,
                image_url=None,
                price=None,
                size=None,
                medium=None,
                year=None,
                is_sold=False,
            )
        ]
        mock_repository.find_all.return_value = mock_artworks

        service = ArtworkService(repository=mock_repository)

        result = service.get_available_artworks()

        assert len(result) == 1
        assert result[0].is_sold is False
        mock_repository.find_all.assert_called_once_with(sold=False)

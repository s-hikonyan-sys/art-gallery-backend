"""
作品エンティティのユニットテスト

ドメインロジックの動作を検証します。
"""

import pytest
from decimal import Decimal
from domain.artwork import Artwork


@pytest.mark.unit
class TestArtwork:
    """作品エンティティのテストクラス"""

    def test_is_available_when_not_sold(self):
        """販売済みでない場合、購入可能であることを確認"""
        artwork = Artwork(
            id=1,
            title="テスト作品",
            description=None,
            image_url=None,
            price=None,
            size=None,
            medium=None,
            year=None,
            is_sold=False,
        )
        assert artwork.is_available() is True

    def test_is_available_when_sold(self):
        """販売済みの場合、購入不可能であることを確認"""
        artwork = Artwork(
            id=1,
            title="テスト作品",
            description=None,
            image_url=None,
            price=None,
            size=None,
            medium=None,
            year=None,
            is_sold=True,
        )
        assert artwork.is_available() is False

    def test_can_be_featured_when_not_sold(self):
        """販売済みでない場合、おすすめに設定可能であることを確認"""
        artwork = Artwork(
            id=1,
            title="テスト作品",
            description=None,
            image_url=None,
            price=None,
            size=None,
            medium=None,
            year=None,
            is_sold=False,
        )
        assert artwork.can_be_featured() is True

    def test_can_be_featured_when_sold(self):
        """販売済みの場合、おすすめに設定不可能であることを確認"""
        artwork = Artwork(
            id=1,
            title="テスト作品",
            description=None,
            image_url=None,
            price=None,
            size=None,
            medium=None,
            year=None,
            is_sold=True,
        )
        assert artwork.can_be_featured() is False

    def test_mark_as_sold(self):
        """販売済みとしてマークする機能をテスト"""
        artwork = Artwork(
            id=1,
            title="テスト作品",
            description=None,
            image_url=None,
            price=None,
            size=None,
            medium=None,
            year=None,
            is_featured=True,
            is_sold=False,
        )

        artwork.mark_as_sold()

        assert artwork.is_sold is True
        assert (
            artwork.is_featured is False
        )  # ビジネスルール: 販売済みはおすすめから外す

    def test_from_dict(self, sample_artwork_dict):
        """辞書データからエンティティを生成する機能をテスト"""
        artwork = Artwork.from_dict(sample_artwork_dict)

        assert artwork.id == 1
        assert artwork.title == "テスト作品"
        assert artwork.price == Decimal("50000")
        assert artwork.is_featured is True
        assert artwork.is_sold is False

    def test_to_dict(self, sample_artwork):
        """エンティティを辞書形式に変換する機能をテスト"""
        result = sample_artwork.to_dict()

        assert result["id"] == 1
        assert result["title"] == "テスト作品"
        assert result["price"] == 50000.0
        assert result["is_featured"] is True
        assert result["is_sold"] is False

"""作品（Artwork）ドメインモデル.

作品エンティティを定義します。エンティティは一意のIDを持ち、
ビジネスロジックを含むドメインオブジェクトです。"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Artwork:
    """作品エンティティ.

    エンティティは以下の特徴を持ちます：
    - 一意のID（識別子）を持つ
    - ライフサイクルを通じて同一性を維持する
    - ビジネスルールを含む

    Attributes:
        id: 作品の一意の識別子
        title: 作品タイトル
        description: 作品の説明
        image_url: 画像URL
        price: 価格
        size: サイズ（例: "50x60cm"）
        medium: 画材（例: "油絵"）
        year: 制作年
        is_featured: おすすめ作品かどうか
        is_sold: 販売済みかどうか
        created_at: 作成日時
        updated_at: 更新日時"""

    id: Optional[int]
    title: str
    description: Optional[str]
    image_url: Optional[str]
    price: Optional[Decimal]
    size: Optional[str]
    medium: Optional[str]
    year: Optional[int]
    is_featured: bool = False
    is_sold: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_available(self) -> bool:
        """作品が購入可能かどうかを判定するビジネスロジック.

        Returns:
            販売済みでない場合True"""
        return not self.is_sold

    def can_be_featured(self) -> bool:
        """おすすめ作品として設定可能かどうかを判定.

        Returns:
            販売済みでない場合True"""
        return not self.is_sold

    def mark_as_sold(self) -> None:
        """作品を販売済みとしてマークする.

        ビジネスルール: 販売済みの作品はおすすめから外す"""
        self.is_sold = True
        if self.is_featured:
            self.is_featured = False

    @classmethod
    def from_dict(cls, data: dict) -> "Artwork":
        """辞書データからArtworkエンティティを生成するファクトリメソッド.

        Args:
            data: データベースから取得した辞書データ

        Returns:
            Artworkエンティティのインスタンス"""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description"),
            image_url=data.get("image_url"),
            price=Decimal(str(data["price"])) if data.get("price") else None,
            size=data.get("size"),
            medium=data.get("medium"),
            year=data.get("year"),
            is_featured=data.get("is_featured", False),
            is_sold=data.get("is_sold", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        """エンティティを辞書形式に変換.

        Returns:
            辞書形式のデータ"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "price": float(self.price) if self.price else None,
            "size": self.size,
            "medium": self.medium,
            "year": self.year,
            "is_featured": self.is_featured,
            "is_sold": self.is_sold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

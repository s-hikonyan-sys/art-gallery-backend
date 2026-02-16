"""pytest設定ファイル
プロジェクト全体のテストで共通利用するフィクスチャを定義します。
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from app import create_app
from repositories.artwork_repository import ArtworkRepository
from repositories.database import Database
from domain.artwork import Artwork


@pytest.fixture(scope="session")
def app():
    """テスト用Flaskアプリケーションインスタンスを作成."""
    # secrets-apiの呼び出しをモック化
    # アプリケーション初期化時にConfig._load_config()が呼ばれるため、
    # create_app()の前にモックを設定する必要がある。
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"password": "test_db_password"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Configクラスの読み込み（_load_config）でrequests.getが呼ばれる
        # また、TOKEN_FILEが存在しないとエラーになるため、モック化も必要かもしれないが、
        # ここではConfig._load_configが一度だけ実行されることを期待する。
        # すでにインポート済みの場合は、再ロードが必要になる可能性がある。

        app = create_app()
        app.config["TESTING"] = True  # テストモードを有効にする
        yield app


@pytest.fixture
def client(app):
    """テストクライアントインスタンスを作成."""
    return app.test_client()


@pytest.fixture
def artwork_repository():
    """ArtworkRepositoryのモックインスタンスを作成."""
    return Mock(spec=ArtworkRepository)


@pytest.fixture
def sample_artwork_dict():
    """テスト用の作品データ（辞書形式）"""
    return {
        "id": 1,
        "title": "テスト作品",
        "description": "これはテスト作品です。",
        "image_url": "http://example.com/image.jpg",
        "price": Decimal("50000"),
        "size": "F10",
        "medium": "油彩",
        "year": 2023,
        "is_featured": True,
        "is_sold": False,
    }


@pytest.fixture
def sample_artwork(sample_artwork_dict):
    """テスト用の作品エンティティ"""
    return Artwork.from_dict(sample_artwork_dict)

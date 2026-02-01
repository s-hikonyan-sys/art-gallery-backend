"""pytest設定ファイル
プロジェクト全体のテストで共通利用するフィクスチャを定義します。
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import logging.handlers

# ログディレクトリ作成処理をモック（CI環境でのPermissionErrorを回避）
# app.py がモジュールレベルで create_app() を呼ぶ前にモックを適用する必要があるため、
# conftest.py のインポート前にパッチを適用
_patcher_mkdir = patch.object(Path, 'mkdir')
_patcher_mkdir.start()

# RotatingFileHandlerの初期化をモック（FileNotFoundErrorを回避）
# ログファイルへの実際の書き込みを回避するため
_mock_file_handler_instance = MagicMock()
_patcher_file_handler = patch.object(
    logging.handlers, 'RotatingFileHandler',
    return_value=_mock_file_handler_instance
)
_patcher_file_handler.start()

from app import create_app
from repositories.artwork_repository import ArtworkRepository
from repositories.database import Database
from domain.artwork import Artwork


@pytest.fixture(scope="session")
def app():
    """テスト用Flaskアプリケーションインスタンスを作成."""
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

"""pytest設定ファイル
プロジェクト全体のテストで共通利用するフィクスチャを定義します。
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os

from app import create_app
from repositories.artwork_repository import ArtworkRepository
from repositories.database import Database
from domain.artwork import Artwork

# configモジュールからTOKEN_FILEをインポートするためにインポート
import config.__init__ as app_config

# テスト用トークンの固定文言
TEST_TOKEN_CONTENT = "test_backend_token_12345"


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """テスト用Flaskアプリケーションインスタンスを作成."""

    # 1. 一時的なトークンディレクトリを作成
    temp_token_dir = tmp_path_factory.mktemp("tokens")

    # テスト用トークンファイルのパス
    test_token_file_path = temp_token_dir / "backend_token.txt"

    # 2. トークンファイルの作成をスキップするロジックを追加
    if not test_token_file_path.exists():
        # ダミーのトークンファイルを生成
        test_token_file_path.write_text(TEST_TOKEN_CONTENT)
        test_token_file_path.chmod(0o600)  # 適切な権限を設定
        print(f"Generated test token file: {test_token_file_path}")
    else:
        print(
            f"Test token file already exists, skipping creation: {test_token_file_path}"
        )

    # 3. config.__init__.py の TOKEN_FILE を上書き
    # sessionスコープのフィクスチャでは monkeypatch は使えないため patch を使用する
    with patch.object(app_config, "TOKEN_FILE", test_token_file_path):
        # secrets-apiのHTTPリクエストをモック化
        # アプリケーション初期化時にConfig._load_config()が呼ばれるため、
        # create_app()の前にモックを設定する必要がある。
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"password": "test_db_password"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # すでに Config クラスがインポート時に初期化されている可能性があるため、
            # 明示的に再読み込みを行う（もし create_app が load_app_config を呼ばない場合）
            from config import Config

            app = create_app()
            app.config["TESTING"] = True  # テストモードを有効にする

            # データベース接続などが初期化時に Config を参照する場合、
            # ここで Config.load_app_config() を呼ぶ必要がある
            Config.load_app_config()

            yield app

    # 4. クリーンアップ処理 (yieldの後)
    # tmp_path_factory を使用しているため、一時ディレクトリは自動的に削除されるが、
    # ファイル内容のチェックを行う場合は、念のためここに追加。
    # ただし、通常は tmp_path_factory の自動クリーンアップで十分。
    if test_token_file_path.exists():
        try:
            current_content = test_token_file_path.read_text().strip()
            if current_content == TEST_TOKEN_CONTENT:
                test_token_file_path.unlink()
                print(
                    f"Deleted test token file with matching content: {test_token_file_path}"
                )
            else:
                print(
                    f"Skipping deletion of test token file (content mismatch): {test_token_file_path}"
                )
        except Exception as e:
            print(f"Error during test token file cleanup: {e}")


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

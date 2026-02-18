"""pytest設定ファイル
プロジェクト全体のテストで共通利用するフィクスチャを定義します。
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os
import shutil

# テスト用トークンの固定文言
TEST_TOKEN_CONTENT = "test_backend_token_12345"


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """テスト用Flaskアプリケーションインスタンスを作成."""

    # 1. 一時的なトークンディレクトリを作成
    temp_token_dir = tmp_path_factory.mktemp("tokens")

    # テスト用トークンファイルのパス
    test_token_file_path = temp_token_dir / "backend_token.txt"

    # 2. トークンファイルの作成
    if not test_token_file_path.exists():
        test_token_file_path.write_text(TEST_TOKEN_CONTENT)
        test_token_file_path.chmod(0o600)
        print(f"Generated test token file: {test_token_file_path}")

    # 3. config.TOKEN_FILE をパッチで上書き
    # 文字列指定でパッチを当てることで、configモジュールのTOKEN_FILEを確実に差し替える
    with patch("config.TOKEN_FILE", test_token_file_path):
        # secrets-apiのHTTPリクエストをモック化
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"password": "test_db_password"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # すべてのモックが有効な状態でインポートを実行
            from app import create_app

            # アプリケーション作成（Config.load_app_config()が内部で呼ばれる）
            app = create_app()
            app.config["TESTING"] = True

            yield app

    # 4. クリーンアップ処理 (yieldの後)
    # tmp_path_factory を使用しているため、一時ディレクトリは自動的に削除されるが、
    # ファイル内容のチェックを行う場合は、念のためここに追加。
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
    from repositories.artwork_repository import ArtworkRepository

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
    from domain.artwork import Artwork

    return Artwork.from_dict(sample_artwork_dict)

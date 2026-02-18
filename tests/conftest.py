import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os
import shutil

# configモジュール自体をインポート（モックするために必要）
import config

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

    # config モジュール全体をモックする
    # from app import create_app が実行される前に、config モジュールがロードされる。
    # そのため、config モジュール内の Config クラスやモジュールレベルの変数をモックする必要がある。
    # patch.dict() で sys.modules を操作する方法もあるが、ここでは patch() を使う
    with patch("config") as mock_config_module:
        # Config クラスの振る舞いをモックする
        # create_app() 内で Config.load_app_config() が呼ばれるため、これをモックする
        mock_config_module.Config = MagicMock()
        mock_config_module.Config.FRONTEND_URL = "http://localhost:3000" # flask_cors用
        mock_config_module.Config.PORT = 5000
        mock_config_module.Config.DEBUG = True
        mock_config_module.Config.get_db_config.return_value = {
            "host": "mock_db_host",
            "port": 5432,
            "database": "mock_db",
            "user": "mock_user",
            "password": "mock_password",
        }
        # load_app_config が呼ばれても何も起きないようにする
        mock_config_module.Config.load_app_config.return_value = None

        # config モジュールレベルの TOKEN_FILE もモックする
        # _get_token_from_file が config.TOKEN_FILE を直接参照するため
        mock_config_module.TOKEN_FILE = test_token_file_path

        # _get_token_from_file および _get_password_from_api がモジュールレベル関数であるため、
        # これらも config モジュール内の適切な場所でモックされるようにする
        # ただし、Config.load_app_config() をモックするため、これらの内部関数が直接呼ばれることはない想定

        # secrets-apiのHTTPリクエストをモック化
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"password": "test_db_password"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # すべてのモックが有効な状態で app をインポートし、作成
            from app import create_app

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

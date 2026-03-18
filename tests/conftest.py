import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os
import shutil
import sys # sys モジュールをインポート

# my_propertiesモジュール自体はトップレベルでインポートしない。
# 必要に応じて、sys.modules['my_properties'] 経由でモックする。

# テスト用トークンの固定文言
TEST_TOKEN_CONTENT = "test_backend_token_12345"


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """テスト用Flaskアプリケーションインスタンスを作成."""

    # 1. 一時的なトークンディレクトリを作成
    temp_token_dir = tmp_path_factory.mktemp("tokens")

    # テスト用トークンファイルのパス
    test_token_file_path = temp_token_dir / "backend_token.txt"

    # 2. ダミーのトークンファイルを作成
    if not test_token_file_path.exists():
        test_token_file_path.write_text(TEST_TOKEN_CONTENT)
        test_token_file_path.chmod(0o600)
        print(f"Generated test token file: {test_token_file_path}")

    # my_properties モジュールを完全にモックする
    # app.py がロードされる際に my_properties モジュールが参照されるため、
    # sys.modules を操作して my_properties モジュール全体を MagicMock に置き換える
    # このモックはセッション全体で有効になる
    original_my_properties_module = sys.modules.get('my_properties')
    mock_my_properties_module = MagicMock()
    sys.modules['my_properties'] = mock_my_properties_module

    # mock_my_properties_module の中の MyProperties クラスとモジュールレベルの TOKEN_FILE を設定
    mock_my_properties_module.MyProperties = MagicMock()
    # flask_cors の TypeError を避けるため、MyProperties.FRONTEND_URL は直接文字列を返すようにする
    mock_my_properties_module.MyProperties.FRONTEND_URL.return_value = "http://localhost:3000"
    mock_my_properties_module.MyProperties.PORT.return_value = 5000
    mock_my_properties_module.MyProperties.DEBUG.return_value = True
    mock_my_properties_module.MyProperties.get_db_config.return_value = {
        "host": "mock_db_host",
        "port": 5432,
        "database": "mock_db",
        "user": "mock_user",
        "password": "mock_password",
    }
    # MyProperties.load_app_config が呼ばれても何も起きないようにする
    mock_my_properties_module.MyProperties.load_app_config.return_value = None

    # my_properties モジュールレベルの TOKEN_FILE もモックする
    # _get_token_from_file が my_properties.TOKEN_FILE を直接参照するため
    mock_my_properties_module.TOKEN_FILE = test_token_file_path

    # secrets-apiのHTTPリクエストをモック化
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"password": "test_db_password"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # すべてのモックが有効な状態で app をインポートし、作成
        from app import create_app

        app = create_app()
        # Flask 標準のテストフラグを有効化
        app.config["TESTING"] = True

        yield app

    # テスト終了後、my_properties モジュールを元の状態に戻す
    if original_my_properties_module:
        sys.modules['my_properties'] = original_my_properties_module
    else:
        del sys.modules['my_properties']

    # 4. クリーンアップ処理 (yieldの後)
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
    """テスト用の作品データ (辞書形式)"""
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

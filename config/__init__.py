"""設定管理モジュール.

設定ファイル（config.yaml）から設定を読み込み、アプリケーション全体で使用する設定を提供します。
機密情報（パスワードなど）は専用の復号APIコンテナから取得します。"""

from pathlib import Path
from typing import Any

import requests
import yaml

# 設定ファイルのパス
CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# トークンファイルのパス（Dockerボリューム経由で secrets-api から提供される）
TOKEN_FILE = Path("/app/tokens/backend_token.txt")


def _get_token_from_file(max_retries: int = 5, retry_interval: int = 1) -> str:
    """トークンファイルからワンタイムトークンを読み込む（リトライあり）. """
    import time

    for attempt in range(max_retries):
        if TOKEN_FILE.exists():
            try:
                token = TOKEN_FILE.read_text().strip()
                if token:
                    return token
            except Exception as e:
                # print を維持しつつ、エラー時は継続
                print(f"Error reading token file (attempt {attempt + 1}): {e}")

        if attempt < max_retries - 1:
            time.sleep(retry_interval)

    raise RuntimeError(
        f"トークンファイルが見つかりません: {TOKEN_FILE} ({max_retries}回試行後)\n"
        "secrets-apiコンテナが正常に起動し、トークンを生成しているか確認してください。"
    )


def _get_password_from_api(config: dict) -> str:
    """復号化APIからデータベースパスワードを取得する."""
    api_config = config.get("secrets_api", {})
    api_url = api_config.get("url", "http://art-gallery-secrets-api:5000")

    # secrets-api 認証用トークンの取得
    auth_token = _get_token_from_file()

    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{api_url}/secrets/database/password", headers=headers, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        password = data.get("password")
        if not password:
            raise ValueError("復号APIからパスワードを取得できませんでした。")
        return password
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"復号APIからのパスワード取得に失敗しました: {e}")


def _load_config_file() -> dict:
    """config.yaml を読み込む."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {CONFIG_FILE}")

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            if not config:
                raise ValueError(f"{CONFIG_FILE} が空です。")
            return config
    except Exception as e:
        raise RuntimeError(f"設定ファイルの読み込みに失敗しました: {e}")


def _load_config() -> dict:
    """全設定（ファイル + API経由の秘密情報）をロードする."""
    # 1. config.yaml を読み込む
    config = _load_config_file()

    # 2. 復号APIからパスワードを取得し、config に統合
    db_password = _get_password_from_api(config)

    if "database" not in config:
        config["database"] = {}
    config["database"]["password"] = db_password

    # 3. 必須項目の検証
    required_keys = ["server", "database", "secrets_api"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"config.yamlに必須項目 '{key}' がありません。")

    return config


class Config:
    """アプリケーション設定クラス.

    シングルトン的に一度だけ設定をロードし、プロパティ経由で型安全なアクセスを提供します。"""

    _config: dict = {}

    @classmethod
    def _get_config(cls) -> dict:
        """設定をロードして返す（未ロードの場合はロードする）."""
        if not cls._config:
            cls._config = _load_config()
        return cls._config

    @classmethod
    def load_app_config(cls) -> None:
        """アプリケーション起動時に設定を明示的に読み込む."""
        cls._config = _load_config()

    @classmethod
    def get_db_config(cls) -> dict:
        """データベース接続設定を辞書形式で返す."""
        config = cls._get_config()
        db = config["database"]
        return {
            "host": db["host"],
            "port": db["port"],
            "database": db["name"],
            "user": db["user"],
            "password": db["password"],
        }

    @property
    def PORT(self) -> int:
        return self._get_config()["server"]["port"]

    @property
    def FLASK_ENV(self) -> str:
        return self._get_config()["server"]["flask_env"]

    @property
    def DEBUG(self) -> bool:
        config = self._get_config()
        server = config["server"]
        return server.get("debug", server["flask_env"] == "development")

    @property
    def FRONTEND_URL(self) -> str:
        return self._get_config()["frontend"]["url"]

    @property
    def DB_HOST(self) -> str:
        return self._get_config()["database"]["host"]

    @property
    def DB_PORT(self) -> int:
        return self._get_config()["database"]["port"]

    @property
    def DB_NAME(self) -> str:
        return self._get_config()["database"]["name"]

    @property
    def DB_USER(self) -> str:
        return self._get_config()["database"]["user"]

    @property
    def DB_PASSWORD(self) -> str:
        return self._get_config()["database"]["password"]

    @property
    def SECRETS_API_URL(self) -> str:
        return self._get_config()["secrets_api"]["url"]

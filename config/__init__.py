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

# トークンファイルのパス (tests/conftest.py でモックされることを想定)
TOKEN_FILE = Path("/app/tokens/backend_token.txt")


def _get_token_from_file(max_retries: int = 30, retry_interval: int = 1) -> str:
    """トークンファイルからトークンを取得（リトライあり）. """
    import time  # 遅延インポート

    for attempt in range(max_retries):
        if TOKEN_FILE.exists():
            try:
                token = TOKEN_FILE.read_text().strip()
                if token:
                    return token
            except Exception as e:
                print(f"Error reading token file (attempt {attempt + 1}): {e}")

        if attempt < max_retries - 1:
            time.sleep(retry_interval)

    raise RuntimeError(
        f"Token file not found after {max_retries} attempts. "
        "Secrets API may not have started yet or failed to generate tokens."
    )


def _get_password_from_api(config: dict) -> str:
    """復号化APIからデータベースパスワードを取得する."""
    api_config = config.get("secrets_api", {})
    api_url = api_config.get("url")

    if not api_url:
        # デフォルトは Docker 内部ネットワークの固定名
        api_url = "http://art-gallery-secrets-api:5000"

    # backend_token.txt からトークンを読み込む
    auth_token = _get_token_from_file()

    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        # ここでは Config を使わず、取得した api_url を使用する
        response = requests.get(
            f"{api_url}/secrets/database/password", headers=headers, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        password = data.get("password")
        if not password:
            raise ValueError("復号APIからパスワードを取得できませんでした")
        return password
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"復号APIからのパスワード取得に失敗しました: {e}") from e


def _load_config_file() -> dict:
    """設定ファイルを読み込む（必須）."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"必須ファイルが見つかりません: {CONFIG_FILE}\n"
            "config.yamlが見つかりません。Ansibleデプロイ時に自動生成されるはずです。"
        )

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            if not config:
                raise ValueError(f"{CONFIG_FILE} が空です")
            return config
    except (FileNotFoundError, yaml.YAMLError, PermissionError) as e:
        raise RuntimeError(f"{CONFIG_FILE} の読み込みに失敗しました: {e}") from e


def _load_secrets(config: dict) -> dict:
    """復号APIから機密情報を取得（必須）または空の辞書を返す."""
    secrets = {}
    # 復号APIからDBパスワードを取得
    db_password = _get_password_from_api(config)
    if db_password:
        secrets["database"] = {"password": db_password}

    # NOTE: secrets_api が backend には存在しないため、ここでは使用しない。
    # 環境変数 SECRETS_API_URL を介して設定されることを想定。
    # db_password は直接取得された値として扱う。

    # secrets は常に空のdictを返すか、db_passwordが取得できた場合のみ'database'キーを持つ
    return secrets


def _load_config() -> dict:
    """設定ファイルを読み込む（必須）."""
    # config.yamlを読み込む（プレーンテキスト、必須）
    config = _load_config_file()

    # 復号APIから機密情報を取得（必須）
    secrets = _load_secrets(config)

    # 機密情報をconfigにマージ
    if "database" in secrets and isinstance(secrets["database"], dict):
        if "database" not in config:
            config["database"] = {}
        if isinstance(config["database"], dict):
            config["database"].update(secrets["database"])

    # 必須項目の検証
    required_keys = ["server", "database", "secrets_api"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"config.yamlに必須項目 '{key}' がありません")

    # database.passwordは必須（APIから取得）
    if "database" in config and "password" not in config["database"]:
        raise ValueError(
            "config.yamlにdatabase.passwordがありません（復号APIから取得される必要があります）"
        )

    return config


class Config:
    """アプリケーション設定クラス.

    設定ファイル（config.yaml）から設定値を読み込み、型安全にアクセスできるようにします。
    機密情報（パスワードなど）は設定ファイルまたは外部APIから読み込みます。"""

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
        return {
            "host": config["database"]["host"],
            "port": config["database"]["port"],
            "database": config["database"]["name"],
            "user": config["database"]["user"],
            "password": config["database"]["password"],
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
        return config["server"].get(
            "debug", config["server"]["flask_env"] == "development"
        )

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

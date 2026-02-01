"""
アプリケーションエントリーポイント.

Flaskアプリケーションの初期化と設定を行います。
各ブループリントを登録し、アプリケーションを起動します。
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from config import Config
from flask import Flask
from flask_cors import CORS
from routes import artwork_bp, health_bp
from services.artwork_service import ArtworkService


def create_app() -> Flask:
    """
    Flaskアプリケーションのファクトリ関数.

    アプリケーションの設定とブループリントの登録を行います。
    テスト時に異なる設定を注入できるように、ファクトリーパターンを使用します。

    Returns:
        設定済みのFlaskアプリケーションインスタンス
    """
    # アプリケーション起動時にConfigクラスを明示的に初期化
    Config.load_app_config()

    app = Flask(__name__)

    # サービスの初期化（appインスタンスに保持し、テスト時に差し替え可能にする）
    app.artwork_service = ArtworkService()

    # CORS設定
    CORS(app, origins=[Config.FRONTEND_URL])

    # ブループリントの登録
    app.register_blueprint(health_bp)
    app.register_blueprint(artwork_bp)

    # ログ設定（常にファイルに出力）
    log_dir = Path("/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # アプリケーションログ
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.addHandler(file_handler)

    # エラーログ
    error_handler = RotatingFileHandler(
        log_dir / "error.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.addHandler(error_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Application startup")

    return app


# アプリケーションインスタンスの作成
app = create_app()


if __name__ == "__main__":
    # Note: host='0.0.0.0' is for development only
    # In production, use a reverse proxy (nginx) and bind to localhost
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)  # nosec B104

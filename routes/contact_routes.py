"""お問い合わせルート.

POST /api/contact を受け付け、キューファイルに保存する。
Slack への送信は release-tools の GitHub Actions が非同期で行う。

セキュリティ対策:
  - レートリミット（同一IP 1分に3回まで）
  - ハニーポットフィールドによるボット検知
  - JSON スキーマバリデーション（services/contact_service.py）
  - CORS は app.py の CORS 設定に委ねる
"""

import logging
import time
from collections import defaultdict
from threading import Lock

from flask import Blueprint, jsonify, request
from services.contact_service import ContactValidationError, process_contact

logger = logging.getLogger(__name__)

contact_bp = Blueprint("contact", __name__)

# ---------------------------------------------------------------------------
# シンプルなインメモリ レートリミット（本番では Redis 推奨）
# ---------------------------------------------------------------------------
_rate_store: dict[str, list[float]] = defaultdict(list)
_rate_lock = Lock()
RATE_LIMIT_COUNT  = 3   # 許可リクエスト数
RATE_LIMIT_WINDOW = 60  # 秒


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    with _rate_lock:
        timestamps = [t for t in _rate_store[ip] if now - t < RATE_LIMIT_WINDOW]
        _rate_store[ip] = timestamps
        if len(timestamps) >= RATE_LIMIT_COUNT:
            return True
        _rate_store[ip].append(now)
    return False


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------

@contact_bp.route("/api/contact", methods=["POST"])
def contact():
    """お問い合わせ受付エンドポイント.

    リクエストボディ（JSON）:
        name     (str): お名前
        email    (str): メールアドレス
        subject  (str): purchase | exhibit | commission | engineer | other
        message  (str): メッセージ本文
        _hp      (str): ハニーポット（ボットが埋めると弾く）

    Returns:
        200: {"status": "ok"}
        400: {"status": "error", "message": "..."}
        429: {"status": "error", "message": "Too many requests"}
    """
    # レートリミット
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    if _is_rate_limited(ip):
        logger.warning("Rate limited: %s", ip)
        return jsonify({"status": "error", "message": "Too many requests. Please try again later."}), 429

    # Content-Type チェック
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json."}), 400

    data = request.get_json(silent=True) or {}

    # ハニーポット（ボットはサイレント OK）
    if data.get("_hp"):
        logger.info("Honeypot triggered from %s", ip)
        return jsonify({"status": "ok"}), 200

    success, error_msg = process_contact(data)

    if not success:
        return jsonify({"status": "error", "message": error_msg}), 400

    return jsonify({"status": "ok"}), 200

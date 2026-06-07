"""お問い合わせルート.

POST /api/contact を受け付け、Slack Webhook に転送する。
セキュリティ対策：
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
from my_properties import MyProperties
from services.contact_service import ContactValidationError, process_contact

logger = logging.getLogger(__name__)

contact_bp = Blueprint("contact", __name__)

# ---------------------------------------------------------------------------
# シンプルなインメモリ レートリミット（本番では Redis 推奨）
# ---------------------------------------------------------------------------
_rate_store: dict[str, list[float]] = defaultdict(list)
_rate_lock = Lock()
RATE_LIMIT_COUNT   = 3    # 許可リクエスト数
RATE_LIMIT_WINDOW  = 60   # 秒


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
        500: {"status": "error", "message": "Server error"}
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

    # ハニーポット（非表示フィールド）がある場合はボットと判断してサイレント OK
    if data.get("_hp"):
        logger.info("Honeypot triggered from %s", ip)
        return jsonify({"status": "ok"}), 200

    # Slack Webhook URL は設定から取得
    try:
        webhook_url = MyProperties.SLACK_WEBHOOK_URL()
    except Exception:
        logger.error("SLACK_WEBHOOK_URL is not configured.")
        return jsonify({"status": "error", "message": "Server configuration error."}), 500

    success, error_msg = process_contact(webhook_url, data)

    if not success:
        if error_msg:
            return jsonify({"status": "error", "message": error_msg}), 400
        return jsonify({"status": "error", "message": "Failed to send message."}), 500

    return jsonify({"status": "ok"}), 200

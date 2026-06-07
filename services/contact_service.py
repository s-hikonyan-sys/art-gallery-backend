"""お問い合わせ送信サービス.

Slack Incoming Webhook へ送信し、失敗時はファイルキューに保存する。
cron による再送は scripts/retry_contact.py が担う。
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# キューディレクトリ（Dockerボリュームで永続化することを推奨）
QUEUE_DIR = Path("/app/contact_queue")

# 許可するフィールドと最大長
ALLOWED_SUBJECTS = {
    "purchase", "exhibit", "commission", "engineer", "other",
}
MAX_LENGTHS = {
    "name":    80,
    "email":   254,
    "subject": 30,
    "message": 2000,
}

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# バリデーション
# ---------------------------------------------------------------------------

class ContactValidationError(ValueError):
    pass


def validate_contact(data: dict) -> dict:
    """入力データを検証し、サニタイズ済みの辞書を返す。

    Args:
        data: リクエストから受け取った辞書

    Returns:
        サニタイズ済み辞書

    Raises:
        ContactValidationError: バリデーション失敗時
    """
    if not isinstance(data, dict):
        raise ContactValidationError("Invalid payload format.")

    name    = str(data.get("name", "")).strip()
    email   = str(data.get("email", "")).strip()
    subject = str(data.get("subject", "")).strip()
    message = str(data.get("message", "")).strip()

    if not name:
        raise ContactValidationError("name is required.")
    if not email or not EMAIL_PATTERN.match(email):
        raise ContactValidationError("Invalid email address.")
    if subject not in ALLOWED_SUBJECTS:
        raise ContactValidationError(f"Invalid subject: {subject!r}")
    if not message:
        raise ContactValidationError("message is required.")

    for field, val in [("name", name), ("email", email), ("subject", subject), ("message", message)]:
        if len(val) > MAX_LENGTHS[field]:
            raise ContactValidationError(f"{field} exceeds maximum length ({MAX_LENGTHS[field]}).")

    return {"name": name, "email": email, "subject": subject, "message": message}


# ---------------------------------------------------------------------------
# Slack 送信
# ---------------------------------------------------------------------------

def _build_slack_payload(contact: dict) -> dict:
    subject_labels = {
        "purchase":   "作品の購入について",
        "exhibit":    "展示・掲載のご依頼",
        "commission": "制作依頼・スケッチ指導",
        "engineer":   "エンジニアとしてのお仕事",
        "other":      "その他",
    }
    label = subject_labels.get(contact["subject"], contact["subject"])
    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "text": f"📬 お問い合わせが届きました（{ts}）",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📬 新しいお問い合わせ", "emoji": True},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*お名前*\n{contact['name']}"},
                    {"type": "mrkdwn", "text": f"*メールアドレス*\n{contact['email']}"},
                    {"type": "mrkdwn", "text": f"*件名*\n{label}"},
                    {"type": "mrkdwn", "text": f"*受信日時*\n{ts}"},
                ],
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*メッセージ*\n{contact['message']}"},
            },
        ],
    }


def send_to_slack(webhook_url: str, contact: dict, timeout: int = 8) -> bool:
    """Slack Incoming Webhook にメッセージを送信する。

    Returns:
        True: 送信成功、False: 送信失敗
    """
    payload = _build_slack_payload(contact)
    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 200 and resp.text == "ok":
            logger.info("Slack notification sent successfully.")
            return True
        logger.error("Slack returned unexpected response: %s %s", resp.status_code, resp.text)
        return False
    except requests.RequestException as exc:
        logger.error("Failed to send Slack notification: %s", exc)
        return False


# ---------------------------------------------------------------------------
# ファイルキュー（Slack 失敗時の保存）
# ---------------------------------------------------------------------------

def enqueue_contact(contact: dict) -> Path:
    """失敗したお問い合わせをファイルキューに保存する。

    Returns:
        保存したファイルのパス
    """
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.json"
    path = QUEUE_DIR / filename
    payload = {
        **contact,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "retry_count": 0,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.warning("Contact queued to file: %s", path)
    return path


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------

def process_contact(webhook_url: str, raw_data: dict) -> tuple[bool, str]:
    """バリデーション → Slack 送信 → 失敗時キュー保存。

    Returns:
        (success: bool, error_message: str)
    """
    try:
        contact = validate_contact(raw_data)
    except ContactValidationError as exc:
        return False, str(exc)

    sent = send_to_slack(webhook_url, contact)
    if not sent:
        enqueue_contact(contact)

    return True, ""

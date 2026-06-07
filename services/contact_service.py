"""お問い合わせ受付サービス.

リクエストをバリデーションしてキューファイルに保存する。
Slack への送信は release-tools の GitHub Actions（send_contact_queue.yml）が担う。
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

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
# キュー書き込み
# ---------------------------------------------------------------------------

def enqueue_contact(contact: dict) -> Path:
    """お問い合わせをキューファイルに保存する。

    送信処理は release-tools の GitHub Actions が行う。
    """
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.json"
    path = QUEUE_DIR / filename
    payload = {
        **contact,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Contact queued: %s", path.name)
    return path


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------

def process_contact(raw_data: dict) -> tuple[bool, str]:
    """バリデーション → キュー書き込み。

    Returns:
        (success: bool, error_message: str)
    """
    try:
        contact = validate_contact(raw_data)
    except ContactValidationError as exc:
        return False, str(exc)

    enqueue_contact(contact)
    return True, ""

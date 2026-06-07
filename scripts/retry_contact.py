#!/usr/bin/env python3
"""キューに溜まったお問い合わせを Slack に再送する cron スクリプト.

推奨 cron 設定（例：5分おき）:
    */5 * * * * /usr/local/bin/python3 /app/scripts/retry_contact.py >> /app/logs/retry_contact.log 2>&1

環境変数:
    SLACK_WEBHOOK_URL : Slack Incoming Webhook URL
    CONTACT_QUEUE_DIR : キューディレクトリ（デフォルト /app/contact_queue）
"""

import json
import logging
import os
import sys
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
QUEUE_DIR   = Path(os.environ.get("CONTACT_QUEUE_DIR", "/app/contact_queue"))
MAX_RETRIES = 5
TIMEOUT     = 8


def send(webhook_url: str, contact: dict) -> bool:
    payload = {
        "text": f"📬 [再送] お問い合わせ from {contact.get('name')} <{contact.get('email')}>",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "📬 お問い合わせ（キューより再送）", "emoji": True}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*お名前*\n{contact.get('name')}"},
                {"type": "mrkdwn", "text": f"*メール*\n{contact.get('email')}"},
                {"type": "mrkdwn", "text": f"*件名*\n{contact.get('subject')}"},
                {"type": "mrkdwn", "text": f"*受信*\n{contact.get('queued_at', '不明')}"},
            ]},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*メッセージ*\n{contact.get('message')}"}},
        ],
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=TIMEOUT,
                             headers={"Content-Type": "application/json"})
        return resp.status_code == 200 and resp.text == "ok"
    except requests.RequestException as exc:
        logger.error("Request failed: %s", exc)
        return False


def main() -> None:
    if not WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL is not set. Exiting.")
        sys.exit(1)

    if not QUEUE_DIR.exists():
        logger.info("Queue directory does not exist: %s", QUEUE_DIR)
        return

    files = sorted(QUEUE_DIR.glob("*.json"))
    if not files:
        logger.info("No queued contacts.")
        return

    logger.info("Processing %d queued contact(s).", len(files))

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Cannot read %s: %s", path, exc)
            continue

        retry_count = data.get("retry_count", 0)
        if retry_count >= MAX_RETRIES:
            logger.warning("Max retries reached for %s — moving to dead letter.", path.name)
            dead = QUEUE_DIR / "dead_letter" / path.name
            dead.parent.mkdir(exist_ok=True)
            path.rename(dead)
            continue

        if send(WEBHOOK_URL, data):
            logger.info("Successfully re-sent and removing: %s", path.name)
            path.unlink()
        else:
            data["retry_count"] = retry_count + 1
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.warning("Retry failed for %s (count=%d)", path.name, data["retry_count"])


if __name__ == "__main__":
    main()

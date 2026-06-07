# お問い合わせフォーム API セットアップ

詳細な環境構築は [BETA_SETUP.md §2](../../portfolio/2_gallery_sample/docs/BETA_SETUP.md) を参照してください。

---

## API 仕様

### エンドポイント

```
POST /api/contact
Content-Type: application/json
```

### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | string | ✓ | お名前（最大 80 文字） |
| `email` | string | ✓ | メールアドレス（最大 254 文字） |
| `subject` | string | ✓ | `purchase` / `exhibit` / `commission` / `engineer` / `other` |
| `message` | string | ✓ | メッセージ本文（最大 2000 文字） |
| `_hp` | string | | ハニーポット（必ず空で送る） |

### レスポンス

| コード | 内容 |
|---|---|
| 200 | `{"status": "ok"}` — キューに保存成功 |
| 400 | `{"status": "error", "message": "..."}` — バリデーションエラー |
| 429 | `{"status": "error", "message": "Too many requests"}` — レートリミット |

---

## 処理フロー

```
[ブラウザ] POST /api/contact (JSON)
    ↓
[Nginx] /api → backend (Flask)
    ↓
[routes/contact_routes.py]
    ├─ レートリミット（同一IP 1分に3回まで）
    ├─ ハニーポット検査
    ├─ JSON バリデーション
    └─ /app/contact_queue/{timestamp}_{id}.json に保存
        → 即時 200 OK を返す（Slack 送信はここでは行わない）

[GitHub Actions: send_contact_queue.yml] 5分おき
    ├─ VPS の /app/contact_queue/ を rsync で取得
    ├─ Slack Incoming Webhook に送信
    ├─ 成功 → ファイル削除
    ├─ 失敗 → ファイルはそのまま（次回 Actions で再試行、retry_count++）
    └─ MAX_RETRIES(5) 超過 → dead_letter/ に移動
```

> **Slack 送信は backend では行いません。** `art-gallery-release-tools` の GitHub Actions が担います。

---

## Docker ボリューム設定（推奨）

`contact_queue` ディレクトリは Docker ボリュームで永続化することを推奨します。

```yaml
# docker-compose.yml（抜粋）
services:
  backend:
    volumes:
      - contact_queue:/app/contact_queue

volumes:
  contact_queue:
```

---

## セキュリティ対策

| 対策 | 実装場所 |
|---|---|
| レートリミット | `routes/contact_routes.py` — 同一 IP 1 分 3 回まで |
| ハニーポット | `routes/contact_routes.py` — `_hp` フィールドが埋まっていると弾く |
| JSON スキーマバリデーション | `services/contact_service.py` — 型・長さ・メール形式・subject 許容値 |
| ブラウザ側バリデーション | `lp/main.js` — HTML5 required + JS チェック |
| CORS | `app.py` — allowed origins を本番ドメインに絞ること |

---

## ファイル構成

```
art-gallery-backend/
├── routes/
│   └── contact_routes.py      POST /api/contact
├── services/
│   └── contact_service.py     バリデーション + キュー書き込み
└── docs/
    └── CONTACT_SETUP.md       このファイル

art-gallery-release-tools/
├── scripts/
│   └── send_contact_queue.py  キュー処理 + Slack 送信
└── .github/workflows/
    └── send_contact_queue.yml 5分おき実行
```

---

*最終更新: 2026-06-07*

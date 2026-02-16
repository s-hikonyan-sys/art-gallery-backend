# Art Gallery Backend テストドキュメント

## 概要

このドキュメントは、Art Gallery Backend アプリケーションのテスト構成、実行方法、および関連情報を提供します。
Secrets APIとの連携に伴い、テスト環境におけるパスワード取得のモック化についても詳述します。

## テスト構成

本プロジェクトでは **pytest** を使用し、以下の2種類のテストを実行します。

1.  **ユニットテスト** (`tests/unit/`)
    *   ドメインモデルおよびサービスのビジネスロジックを独立してテストします（モックリポジトリを使用）。
2.  **結合テスト** (`tests/integration/`)
    *   APIエンドポイントとデータベースの連携をテストします。

## テストの実行

### すべてのテストを実行

```bash
pytest
```

### 特定のテストを実行

*   **ユニットテストのみ**:
    ```bash
    pytest -m unit
    ```
*   **結合テストのみ**:
    ```bash
    pytest -m integration
    ```
*   **特定のファイル**:
    ```bash
    pytest tests/unit/test_domain_artwork.py
    ```

### カバレッジレポートの生成

```bash
pytest --cov=. --cov-report=html:htmlcov
```

レポートは `htmlcov/index.html` に生成されます。

## テストマーカー

以下のマーカーを使用してテストをフィルタリングできます。

*   `@pytest.mark.unit`: ユニットテスト
*   `@pytest.mark.integration`: 結合テスト
*   `@pytest.mark.slow`: 実行に時間がかかるテスト

## フィクスチャ (`tests/conftest.py`)

`tests/conftest.py` には、テストで共通利用される以下のフィクスチャが定義されています。

*   **`app` フィクスチャ**:
    *   Flask アプリケーションインスタンスを作成します。
    *   アプリケーションの初期化時に Secrets API からパスワードを取得する処理を**モック**します。これにより、テスト実行時に実際の Secrets API サービスは不要になります。
    *   テスト用のダミー `backend_token.txt` ファイルを一時ディレクトリに生成し、`config.__init__.TOKEN_FILE` をそのパスにパッチします。
    *   テスト終了時に、作成したダミーファイルがテスト用の内容と一致する場合のみ削除します。
*   `client`: テストクライアントインスタンス
*   `artwork_repository`: `ArtworkRepository` のモックインスタンス
*   `sample_artwork_dict`, `sample_artwork`: サンプル作品データ（辞書形式とエンティティ）

## CI/CDでのテスト実行

GitHub Actions などの CI/CD パイプラインでテストを実行する際は、`secrets-api` への依存関係を適切にモックする設定が必要です。

```yaml
- name: Backend テストの実行 (pytest)
  run: |
    pytest tests/ --import-mode=append --import-test-modules=mock_secrets_api
```

上記は `art-gallery-backend/.github/workflows/ci.yml` に既に実装されているモック化ステップと連携します。

## トラブルシューティング

### トークンファイル関連のエラー

テスト中に `RuntimeError: Token file not found after X attempts.` のようなエラーが発生した場合、`tests/conftest.py` でトークンファイルのモック化が正しく機能しているか確認してください。

### その他の一般的なエラー

*   **インポートエラー**: `PYTHONPATH` が正しく設定されているか確認してください。
*   **データベース接続エラー**: 結合テストでは実際のデータベースに接続します。`docker-compose up -d` でデータベースコンテナが起動しているか確認してください。

## 補足：デプロイ後検証テストについて

本リポジトリには、Ansibleを使用した「デプロイ後検証テスト」が `release-tools/ansible/tests/` ディレクトリに存在します。これは、アプリケーションの単体・結合テストとは異なり、デプロイされたインフラストラクチャおよびアプリケーションが本番環境で期待通りに動作しているかを確認することを目的としています。

デプロイ後検証テストの詳細については、`release-tools/ansible/tests/README.md` を参照してください。

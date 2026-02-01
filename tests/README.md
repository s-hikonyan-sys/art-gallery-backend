# テストドキュメント

## テスト構成

このプロジェクトでは、**pytest**を使用してユニットテストと結合テストを実行します。

### テストの種類

1. **ユニットテスト** (`tests/unit/`)
   - ドメインモデルのテスト
   - サービスのテスト（モックリポジトリを使用）
   - 各コンポーネントを独立してテスト

2. **結合テスト** (`tests/integration/`)
   - APIエンドポイントのテスト
   - データベースとの統合テスト
   - 複数のコンポーネントを組み合わせたテスト

## テストの実行

### すべてのテストを実行

```bash
# コンテナ内で実行（推奨）
docker compose exec backend pytest

# またはローカルで実行（プロジェクトルートから）
pytest
```

**注意**: テストはプロジェクトルートから実行してください。`pytest.ini`で`src/backend`をPythonパスに追加しています。

### ユニットテストのみ実行

```bash
pytest tests/unit/ -m unit
```

### 結合テストのみ実行

```bash
pytest tests/integration/ -m integration
```

### カバレッジレポートを生成

```bash
pytest --cov=src/backend --cov-report=html:tests/htmlcov
```

カバレッジレポートは `tests/htmlcov/index.html` に生成されます。

### 特定のテストファイルを実行

```bash
pytest tests/unit/test_domain_artwork.py
```

### 特定のテストクラスを実行

```bash
pytest tests/unit/test_domain_artwork.py::TestArtwork
```

### 特定のテストメソッドを実行

```bash
pytest tests/unit/test_domain_artwork.py::TestArtwork::test_is_available_when_not_sold
```

## テストマーカー

テストには以下のマーカーが設定されています：

- `@pytest.mark.unit`: ユニットテスト
- `@pytest.mark.integration`: 結合テスト
- `@pytest.mark.slow`: 実行に時間がかかるテスト

マーカーでフィルタリング：

```bash
# ユニットテストのみ
pytest -m unit

# 結合テストのみ
pytest -m integration

# スローテストを除外
pytest -m "not slow"
```

## テストの追加

### 新しいユニットテストを追加

1. `tests/unit/` ディレクトリに `test_*.py` ファイルを作成
2. `@pytest.mark.unit` マーカーを追加
3. テストクラスまたはテスト関数を実装

例：

```python
import pytest
from domain.artwork import Artwork

@pytest.mark.unit
class TestArtwork:
    def test_something(self):
        artwork = Artwork(id=1, title="テスト")
        assert artwork.title == "テスト"
```

### 新しい結合テストを追加

1. `tests/integration/` ディレクトリに `test_*.py` ファイルを作成
2. `@pytest.mark.integration` マーカーを追加
3. Flask test clientを使用してAPIをテスト

例：

```python
import pytest
from app import create_app

@pytest.mark.integration
class TestAPI:
    def test_endpoint(self):
        app = create_app()
        client = app.test_client()
        response = client.get('/api/health')
        assert response.status_code == 200
```

## フィクスチャ

共通のテストデータは `tests/conftest.py` で定義されています：

- `sample_artwork`: サンプル作品エンティティ
- `sample_artwork_dict`: サンプル作品の辞書データ
- `sample_order`: サンプル注文エンティティ
- `sample_order_dict`: サンプル注文の辞書データ

## CI/CDでの実行

GitHub ActionsなどのCI/CDパイプラインでテストを実行する場合：

```yaml
- name: Run tests
  run: |
    docker compose exec -T backend pytest
```

## トラブルシューティング

### インポートエラーが発生する場合

Pythonパスが正しく設定されているか確認：

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### データベース接続エラーが発生する場合

結合テストでは実際のデータベースに接続します。コンテナが起動していることを確認：

```bash
docker compose up -d
```

## 補足：デプロイ後検証テストについて

本リポジトリには、Ansibleを使用した「デプロイ後検証テスト」が `release-tools/ansible/tests/` ディレクトリに存在します。これは、アプリケーションの単体・結合テストとは異なり、デプロイされたインフラストラクチャおよびアプリケーションが本番環境で期待通りに動作しているかを確認することを目的としています。

デプロイ後検証テストの詳細については、`release-tools/ansible/tests/README.md` を参照してください。


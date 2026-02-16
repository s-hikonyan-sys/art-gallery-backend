# バックエンドコード構成の解説

## 概要

このドキュメントは、現在のバックエンドコードの構成と各コンポーネントの役割を詳しく解説します。

## ディレクトリ構成

```
backend/
├── app.py                      # アプリケーションエントリーポイント
├── config.py                   # 設定管理
├── requirements.txt            # Python依存関係
├── Dockerfile                  # Dockerイメージ定義
├── pytest.ini                 # pytest設定
├── .coveragerc                 # カバレッジ設定
│
├── domain/                     # ドメインモデル層
│   ├── __init__.py
│   ├── artwork.py              # 作品エンティティ
│
├── repositories/               # データアクセス層
│   ├── __init__.py
│   ├── database.py             # データベース接続管理
│   ├── artwork_repository.py  # 作品リポジトリ
│   └── order_repository.py    # 注文リポジトリ
│
├── services/                   # ビジネスロジック層
│   ├── __init__.py
│   ├── artwork_service.py     # 作品サービス
│   └── order_service.py       # 注文サービス
│
├── routes/                     # HTTPルーティング層
│   ├── __init__.py
│   ├── health.py               # ヘルスチェックルート
│   ├── artwork_routes.py      # 作品ルート
│   └── order_routes.py        # 注文ルート
│
└── tests/                      # テストコード
    ├── __init__.py
    ├── conftest.py             # pytest共通フィクスチャ
    ├── unit/                   # ユニットテスト
    │   ├── test_domain_artwork.py
    │   ├── test_services_artwork_service.py
    │   └── test_services_order_service.py
    └── integration/            # 結合テスト
        ├── test_health_routes.py
        ├── test_artwork_routes.py
        └── test_order_routes.py
```

## レイヤードアーキテクチャ

アプリケーションは以下の4層に分離されています：

```
┌─────────────────────────────────┐
│   Routes (ルーティング層)         │  HTTPリクエストの処理
├─────────────────────────────────┤
│   Services (サービス層)           │  ビジネスロジック
├─────────────────────────────────┤
│   Domain (ドメイン層)             │  エンティティとドメインロジック
├─────────────────────────────────┤
│   Repositories (リポジトリ層)    │  データアクセス
└─────────────────────────────────┘
```

### 依存関係の方向

```
Routes → Services → Domain ← Repositories
```

- 上位層は下位層に依存する
- 下位層は上位層を知らない
- Domain層は独立（他の層に依存しない）

## 各ファイルの詳細解説

### 1. app.py - アプリケーションエントリーポイント

**責務**: Flaskアプリケーションの初期化と設定

**主な機能**:
- Flaskアプリケーションインスタンスの作成
- CORS設定
- ブループリントの登録
- アプリケーションの起動

**コード構造**:
```python
def create_app() -> Flask:
    """ファクトリーパターンによるアプリケーション作成"""
    app = Flask(__name__)
    CORS(app, origins=[Config.FRONTEND_URL])
    app.register_blueprint(health_bp)
    app.register_blueprint(artwork_bp)
    app.register_blueprint(order_bp)
    return app
```

**設計パターン**: ファクトリーパターン
- テスト時に異なる設定を注入可能
- アプリケーションの再利用性が向上

### 2. config/ - 設定管理

**責務**: 設定ファイル（`config.yaml`）からの設定読み込みと、`art-gallery-secrets-api`からの機密情報取得

**主な機能**:
- YAML設定ファイルの読み込み
- `art-gallery-secrets-api` からのデータベースパスワード取得
- 設定値の型変換（文字列→整数など）
- デフォルト値の提供
- データベース接続設定の提供

**設計の特徴**:
- クラス変数による設定値の管理
- `art-gallery-secrets-api` による機密情報の集中管理
- `art-gallery-secrets-api` への認証トークンによるAPIアクセス制御
- 型ヒントによる型安全性
- クラスメソッドによる設定の提供
- 環境変数による API URL の動的な設定

### 3. domain/ - ドメインモデル層

**責務**: ビジネスロジックの中核となるエンティティとドメインロジック

#### 3.1. domain/artwork.py - 作品エンティティ

**責務**: 作品に関するドメインモデルとビジネスロジック

**主な機能**:
- 作品エンティティの定義（`@dataclass`を使用）
- ドメインロジックの実装
- データ変換メソッド（`from_dict`, `to_dict`）

**エンティティの属性**:
```python
@dataclass
class Artwork:
    id: Optional[int]              # 一意の識別子
    title: str                     # 作品タイトル
    description: Optional[str]     # 説明
    image_url: Optional[str]       # 画像URL
    price: Optional[Decimal]       # 価格
    size: Optional[str]            # サイズ
    medium: Optional[str]          # 画材
    year: Optional[int]            # 制作年
    is_featured: bool = False      # おすすめフラグ
    is_sold: bool = False         # 販売済みフラグ
    created_at: Optional[datetime] # 作成日時
    updated_at: Optional[datetime] # 更新日時
```

**ドメインロジック**:
- `is_available()`: 購入可能かどうかを判定
- `can_be_featured()`: おすすめに設定可能かどうかを判定
- `mark_as_sold()`: 販売済みとしてマーク（ビジネスルール: 販売済みはおすすめから外す）

**データ変換**:
- `from_dict()`: 辞書データからエンティティを生成（ファクトリーメソッド）
- `to_dict()`: エンティティを辞書形式に変換（APIレスポンス用）

#### 3.2. domain/order.py - 注文エンティティ

**責務**: 注文に関するドメインモデルとビジネスロジック

**主な機能**:
- 注文エンティティの定義
- 注文データの検証ロジック

**エンティティの属性**:
```python
@dataclass
class Order:
    id: Optional[int]
    artwork_id: int               # 注文された作品ID
    artwork_title: str            # 作品タイトル（スナップショット）
    name: str                     # 顧客名
    email: str                    # メールアドレス
    phone: Optional[str]          # 電話番号
    message: Optional[str]        # メッセージ
    created_at: Optional[datetime] # 注文日時
```

**ドメインロジック**:
- `validate()`: 注文データの妥当性を検証
  - 顧客名の必須チェック
  - メールアドレスの必須チェックと形式検証
  - 作品IDの必須チェック

### 4. repositories/ - データアクセス層

**責務**: データベースへのアクセスとエンティティへの変換

#### 4.1. repositories/database.py - データベース接続管理

**責務**: データベース接続の取得と管理

**主な機能**:
- データベース接続の取得（コンテキストマネージャー）
- カーソルの取得（コンテキストマネージャー）
- トランザクション管理（自動コミット/ロールバック）

**コード構造**:
```python
class Database:
    @staticmethod
    @contextmanager
    def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
        """データベース接続を取得するコンテキストマネージャー"""
        conn = psycopg2.connect(**Config.get_db_config())
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
```

**設計の特徴**:
- コンテキストマネージャーによるリソース管理
- 自動的なトランザクション管理
- 例外時の自動ロールバック

#### 4.2. repositories/artwork_repository.py - 作品リポジトリ

**責務**: 作品エンティティの永続化

**主な機能**:
- 作品一覧の取得（フィルタリング対応）
- IDによる作品の検索
- 作品タイトルの取得（軽量クエリ）

**コード構造**:
```python
class ArtworkRepository:
    @staticmethod
    def find_all(featured: Optional[bool] = None, sold: Optional[bool] = None) -> List[Artwork]:
        """すべての作品を取得（フィルタリング対応）"""
        query = "SELECT * FROM artworks WHERE 1=1"
        # フィルタ条件の追加
        # データベースレコードをArtworkエンティティに変換
        return [Artwork.from_dict(dict(row)) for row in results]
    
    @staticmethod
    def find_by_id(artwork_id: int) -> Optional[Artwork]:
        """IDで作品を検索"""
        # ...
    
    @staticmethod
    def find_title_by_id(artwork_id: int) -> Optional[str]:
        """作品タイトルのみを取得（軽量クエリ）"""
        # ...
```

**設計の特徴**:
- 静的メソッドによる実装（インスタンス化不要）
- データベースレコードとエンティティの変換
- フィルタリング機能の提供

#### 4.3. repositories/order_repository.py - 注文リポジトリ

**責務**: 注文エンティティの永続化

**主な機能**:
- 注文の作成
- IDによる注文の検索
- 注文一覧の取得

**コード構造**:
```python
class OrderRepository:
    @staticmethod
    def create(order: Order, artwork_title: str) -> Order:
        """新しい注文を作成"""
        # 作品タイトルをスナップショットとして保存
        # 注文をデータベースに保存
        # 作成された注文エンティティを返す
    
    @staticmethod
    def find_by_id(order_id: int) -> Optional[Order]:
        """IDで注文を検索"""
        # ...
```

**設計の特徴**:
- 作品タイトルをスナップショットとして保存（作品が削除されても注文履歴は保持）
- トランザクション管理（Databaseクラスが担当）

### 5. services/ - ビジネスロジック層

**責務**: ビジネスロジックの実装と複数のリポジトリの組み合わせ

#### 5.1. services/artwork_service.py - 作品サービス

**責務**: 作品に関するビジネスロジック

**主な機能**:
- 作品一覧の取得（フィルタリング）
- IDによる作品の取得
- おすすめ作品の取得
- 購入可能な作品の取得

**コード構造**:
```python
class ArtworkService:
    def __init__(self, repository: ArtworkRepository = None):
        """依存性注入によるリポジトリの注入"""
        self.repository = repository or ArtworkRepository()
    
    def get_all_artworks(self, featured: Optional[bool] = None, sold: Optional[bool] = None) -> List[Artwork]:
        """すべての作品を取得"""
        return self.repository.find_all(featured=featured, sold=sold)
    
    def get_artwork_by_id(self, artwork_id: int) -> Optional[Artwork]:
        """IDで作品を取得（見つからない場合は例外）"""
        artwork = self.repository.find_by_id(artwork_id)
        if not artwork:
            raise ValueError(f"作品ID {artwork_id} が見つかりません")
        return artwork
```

**設計の特徴**:
- 依存性注入によるテスト容易性
- リポジトリの抽象化
- エラーハンドリング（見つからない場合の例外）

#### 5.2. services/order_service.py - 注文サービス

**責務**: 注文に関するビジネスロジック

**主な機能**:
- 注文の作成（検証とビジネスルールの適用）
- IDによる注文の取得

**コード構造**:
```python
class OrderService:
    def __init__(self, order_repository: OrderRepository = None, artwork_repository: ArtworkRepository = None):
        """複数のリポジトリを注入"""
        self.order_repository = order_repository or OrderRepository()
        self.artwork_repository = artwork_repository or ArtworkRepository()
    
    def create_order(self, order_data: dict) -> Order:
        """注文を作成（ビジネスロジックを含む）"""
        # 1. 注文エンティティの作成
        order = Order(...)
        
        # 2. ドメインロジックによる検証
        validation_errors = order.validate()
        if validation_errors:
            raise ValueError('; '.join(validation_errors))
        
        # 3. 作品の存在確認
        artwork = self.artwork_repository.find_by_id(order.artwork_id)
        if not artwork:
            raise ValueError(f"作品ID {order.artwork_id} が見つかりません")
        
        # 4. ビジネスルール: 販売済みの作品には注文できない
        if artwork.is_sold:
            raise ValueError("この作品は既に販売済みです")
        
        # 5. 注文の作成
        return self.order_repository.create(order, artwork.title)
```

**設計の特徴**:
- 複数のリポジトリの組み合わせ
- ビジネスルールの適用
- ドメインロジックの呼び出し

### 6. routes/ - HTTPルーティング層

**責務**: HTTPリクエストの処理とレスポンスの生成

#### 6.1. routes/health.py - ヘルスチェックルート

**責務**: アプリケーションの動作確認

**エンドポイント**:
- `GET /health`
- `GET /api/health`

**コード構造**:
```python
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
@health_bp.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK', 'message': 'Art Gallery API is running'})
```

#### 6.2. routes/artwork_routes.py - 作品ルート

**責務**: 作品に関するHTTPエンドポイント

**エンドポイント**:
- `GET /api/artworks` - 作品一覧取得（フィルタリング対応）
- `GET /api/artworks/<id>` - 作品詳細取得

**コード構造**:
```python
artwork_bp = Blueprint('artworks', __name__, url_prefix='/api/artworks')
service = ArtworkService()

@artwork_bp.route('', methods=['GET'])
def get_artworks():
    # クエリパラメータの取得と変換
    featured = request.args.get('featured')
    featured = featured.lower() == 'true' if featured is not None else None
    
    # サービス層を呼び出し
    artworks = service.get_all_artworks(featured=featured, sold=sold)
    
    # エンティティを辞書に変換してJSONレスポンス
    return jsonify([artwork.to_dict() for artwork in artworks])
```

**設計の特徴**:
- ブループリントによるルーティングの分離
- クエリパラメータの処理
- サービス層の呼び出し
- エンティティからJSONへの変換

#### 6.3. routes/order_routes.py - 注文ルート

**責務**: 注文に関するHTTPエンドポイント

**エンドポイント**:
- `POST /api/orders` - 注文作成

**コード構造**:
```python
order_bp = Blueprint('orders', __name__, url_prefix='/api/orders')
service = OrderService()

@order_bp.route('', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({'error': 'リクエストボディが空です'}), 400
        
        # サービス層を呼び出し（ビジネスロジックと検証を含む）
        order = service.create_order(data)
        
        return jsonify({'id': order.id, 'message': 'Order created successfully'}), 201
    except ValueError as e:
        # ビジネスロジックエラー
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # 予期しないエラー
        return jsonify({'error': str(e)}), 500
```

**設計の特徴**:
- エラーハンドリングの階層化
- ビジネスロジックエラーとシステムエラーの区別
- HTTPステータスコードの適切な設定

## データフロー

### 作品一覧取得の例

```
1. HTTPリクエスト: GET /api/artworks?featured=true
   ↓
2. routes/artwork_routes.py: get_artworks()
   - クエリパラメータの取得と変換
   ↓
3. services/artwork_service.py: get_all_artworks(featured=True)
   - ビジネスロジックの実行
   ↓
4. repositories/artwork_repository.py: find_all(featured=True)
   - データベースクエリの実行
   ↓
5. domain/artwork.py: Artwork.from_dict()
   - データベースレコードをエンティティに変換
   ↓
6. エンティティのリストを返す
   ↓
7. routes/artwork_routes.py: artwork.to_dict()
   - エンティティを辞書に変換
   ↓
8. HTTPレスポンス: JSON形式の作品リスト
```

### 注文作成の例

```
1. HTTPリクエスト: POST /api/orders
   { "artwork_id": 1, "name": "太郎", "email": "test@example.com" }
   ↓
2. routes/order_routes.py: create_order()
   - リクエストボディの取得
   ↓
3. services/order_service.py: create_order(order_data)
   - 注文エンティティの作成
   - ドメインロジックによる検証（order.validate()）
   - 作品の存在確認（artwork_repository.find_by_id()）
   - ビジネスルールの適用（artwork.is_sold のチェック）
   ↓
4. repositories/order_repository.py: create(order, artwork_title)
   - データベースへの保存
   ↓
5. 作成された注文エンティティを返す
   ↓
6. routes/order_routes.py: JSONレスポンス
   { "id": 1, "message": "Order created successfully" }
```

## 設計パターンの使用

### 1. リポジトリパターン

**目的**: データアクセスの抽象化

**実装**:
- `ArtworkRepository`, `OrderRepository`クラス
- データベースの詳細をドメイン層から分離

**利点**:
- テスト容易性（モックリポジトリを注入可能）
- データベースの変更に対する耐性

### 2. サービスパターン

**目的**: ビジネスロジックの集約

**実装**:
- `ArtworkService`, `OrderService`クラス
- 複数のリポジトリの組み合わせ

**利点**:
- ビジネスロジックの再利用性
- トランザクション管理の一元化

### 3. ファクトリーパターン

**目的**: アプリケーションの作成を抽象化

**実装**:
- `create_app()`関数

**利点**:
- テスト時の設定注入が容易
- アプリケーションの再利用性

### 4. 依存性注入

**目的**: テスト容易性の向上

**実装**:
```python
class ArtworkService:
    def __init__(self, repository: ArtworkRepository = None):
        self.repository = repository or ArtworkRepository()
```

**利点**:
- モックリポジトリを注入可能
- テスト時の柔軟性

## Pythonの機能の活用

### 1. dataclass

**使用箇所**: `domain/artwork.py`

**利点**:
- 型安全性の向上
- コードの簡潔性
- 自動的な`__init__`、`__repr__`の生成

### 2. 型ヒント

**使用箇所**: すべてのファイル

**利点**:
- コードの可読性向上
- IDEの補完機能の向上
- 型チェックツール（mypy）との統合

### 3. コンテキストマネージャー

**使用箇所**: `repositories/database.py`

**利点**:
- リソース管理の自動化
- 例外時の確実なクリーンアップ

### 4. デコレータ

**使用箇所**: 
- `@dataclass`: エンティティの定義
- `@app.route()`: ルーティング
- `@contextmanager`: コンテキストマネージャー

## エラーハンドリング

### 階層的なエラーハンドリング

1. **ドメイン層**: ビジネスルール違反の検出
   - `Order.validate()`: 検証エラーのリストを返す

2. **サービス層**: ビジネスロジックエラー
   - `ValueError`を発生（作品が見つからない、販売済みなど）

3. **ルーティング層**: HTTPエラーレスポンス
   - `ValueError` → 400 Bad Request
   - その他の例外 → 500 Internal Server Error

## テスト容易性

このアーキテクチャにより、各層を独立してテストできます：

1. **ドメイン層**: ビジネスロジックの単体テスト（データベース不要）
2. **リポジトリ層**: データアクセスの統合テスト（実際のデータベースを使用）
3. **サービス層**: ビジネスロジックの統合テスト（モックリポジトリを使用）
4. **ルーティング層**: HTTPエンドポイントのテスト（モックサービスを使用）

## 拡張性

この構成により、以下の拡張が容易です：

1. **新しいエンティティの追加**:
   - `domain/`にエンティティを追加
   - `repositories/`にリポジトリを追加
   - `services/`にサービスを追加
   - `routes/`にルートを追加

2. **新しい機能の追加**:
   - 既存の層を拡張するだけで対応可能
   - 他の層への影響を最小限に抑制

3. **データベースの変更**:
   - リポジトリ層のみを変更すれば対応可能
   - ドメイン層とサービス層は影響を受けない

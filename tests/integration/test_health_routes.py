"""
ヘルスチェックエンドポイントの結合テスト

Flask test clientを使用してHTTPリクエストをテストします。
"""

import pytest
# from app import create_app # テスト収集時の意図しないアプリ生成を防ぐため削除

@pytest.mark.integration
class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_endpoint(self, client): # clientフィクスチャを直接使用
        """ヘルスチェックエンドポイントが正常に動作することを確認"""
        # app = create_app() # appフィクスチャを使用するため不要
        # client = app.test_client() # clientフィクスチャを直接使用するため不要

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "OK"
        assert "message" in data

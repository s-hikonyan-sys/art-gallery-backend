"""
ヘルスチェックエンドポイントの結合テスト

Flask test clientを使用してHTTPリクエストをテストします。
"""

import pytest
from app import create_app


@pytest.mark.integration
class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_endpoint(self):
        """ヘルスチェックエンドポイントが正常に動作することを確認"""
        app = create_app()
        client = app.test_client()

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "OK"
        assert "message" in data

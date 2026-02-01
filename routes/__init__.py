"""
ルーティングパッケージ.

各機能ごとのブループリントをまとめ、外部から利用しやすくします。
"""

from .artwork_routes import artwork_bp
from .health import health_bp

__all__ = ["artwork_bp", "health_bp"]

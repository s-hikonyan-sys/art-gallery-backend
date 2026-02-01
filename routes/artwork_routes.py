"""作品ルート.

作品に関するHTTPエンドポイントを定義します。"""

from flask import Blueprint, current_app, jsonify, request
from services.artwork_service import ArtworkService

artwork_bp = Blueprint("artworks", __name__, url_prefix="/api/artworks")


@artwork_bp.route("", methods=["GET"])
def get_artworks():
    """作品一覧を取得.

    クエリパラメータ:
        featured: true/false - おすすめ作品でフィルタリング
        sold: true/false - 販売済みでフィルタリング

    Returns:
        JSON形式の作品リスト"""
    try:
        # クエリパラメータの取得と変換
        featured_param = request.args.get("featured")
        sold_param = request.args.get("sold")

        featured = None
        if featured_param is not None:
            featured = featured_param.lower() == "true"

        sold = None
        if sold_param is not None:
            sold = sold_param.lower() == "true"

        # サービス層を呼び出し
        artworks = current_app.artwork_service.get_all_artworks(
            featured=featured, sold=sold
        )

        # エンティティを辞書に変換
        return jsonify([artwork.to_dict() for artwork in artworks])
    except Exception as e:
        # トレースバックを含めてエラーログを出力
        current_app.logger.error(
            f"作品一覧取得中にエラーが発生しました: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@artwork_bp.route("/<int:artwork_id>", methods=["GET"])
def get_artwork(artwork_id: int):
    """作品詳細を取得.

    Args:
        artwork_id: 作品ID

    Returns:
        JSON形式の作品情報"""
    try:
        artwork = current_app.artwork_service.get_artwork_by_id(artwork_id)
        if artwork is None:
            return jsonify({"error": f"作品ID {artwork_id} が見つかりません"}), 404
        return jsonify(artwork.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # トレースバックを含めてエラーログを出力
        current_app.logger.error(
            f"作品詳細(ID: {artwork_id})取得中にエラーが発生しました: {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500

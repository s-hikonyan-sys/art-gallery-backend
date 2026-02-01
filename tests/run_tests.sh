#!/bin/bash
# テスト実行スクリプト

echo "=== テスト実行スクリプト ==="
echo ""

# カラー出力の設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テストタイプの選択
echo "テストタイプを選択してください:"
echo "1) すべてのテスト"
echo "2) ユニットテストのみ"
echo "3) 結合テストのみ"
echo "4) カバレッジレポート付き"
read -p "選択 (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}すべてのテストを実行します...${NC}"
        pytest
        ;;
    2)
        echo -e "${GREEN}ユニットテストを実行します...${NC}"
        pytest tests/unit/ -m unit -v
        ;;
    3)
        echo -e "${GREEN}結合テストを実行します...${NC}"
        pytest tests/integration/ -m integration -v
        ;;
    4)
        echo -e "${GREEN}カバレッジレポート付きでテストを実行します...${NC}"
        pytest --cov=src/backend --cov-report=html:tests/htmlcov --cov-report=term-missing
        echo -e "${YELLOW}カバレッジレポート: tests/htmlcov/index.html${NC}"
        ;;
    *)
        echo "無効な選択です。すべてのテストを実行します。"
        pytest
        ;;
esac

echo ""
echo "=== テスト完了 ==="


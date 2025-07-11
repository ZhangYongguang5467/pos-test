#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Navigate to the commons directory
cd "$SCRIPT_DIR/../services/commons"

# __about__.py のパス
ABOUT_FILE="src/kugel_common/__about__.py"

# 現在のバージョンを読み取る
CURRENT_VERSION=$(grep "__version__" $ABOUT_FILE | cut -d '"' -f 2)
echo "現在のバージョン: $CURRENT_VERSION"

# バージョンをインクリメント（macOS bash互換性のため修正）
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
LAST_INDEX=$((${#VERSION_PARTS[@]} - 1))
VERSION_PARTS[$LAST_INDEX]=$((VERSION_PARTS[$LAST_INDEX] + 1))
NEW_VERSION="${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.${VERSION_PARTS[2]}"
echo "新しいバージョン: $NEW_VERSION"

# __about__.py を新しいバージョンで更新（macOS対応）
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" "$ABOUT_FILE"
else
    # Linux
    sed -i "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" "$ABOUT_FILE"
fi

# プロジェクトをビルド
# ここにビルドコマンドを挿入（例: python setup.py bdist_wheel）
hatch build
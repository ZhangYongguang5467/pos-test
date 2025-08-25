#!/bin/bash

# Usage: ./run_copy.sh [service_name]
# If service_name is provided, copy only to that service
# If no service_name is provided, copy to all services

# __about__.py のパス
ABOUT_FILE="src/kugel_common/__about__.py"

# 現在のバージョンを読み取る
CURRENT_VERSION=$(grep "__version__" $ABOUT_FILE | cut -d '"' -f 2)
echo "現在のバージョン: $CURRENT_VERSION"

# ビルドされたホイールファイルの名前を更新
FILENAME="dist/kugel_common-${CURRENT_VERSION}-py3-none-any.whl"

# Check if wheel file exists
if [ ! -f "$FILENAME" ]; then
    echo "Error: Wheel file $FILENAME not found"
    echo "Please run run_build.sh first"
    exit 1
fi

# ログファイルのパス
LOGFILE="copy_log.txt"

# Initialize log file
echo "コピー処理開始: $(date)" > "$LOGFILE"

if [ -n "$1" ]; then
    # Copy to specific service
    SERVICE="$1"
    DEST_DIR="../${SERVICE}/commons/dist"
    
    echo "Copying to service: $SERVICE"
    
    # Create directory if it doesn't exist
    mkdir -p "$DEST_DIR"
    
    if cp "$FILENAME" "$DEST_DIR"; then
        echo "$(date): $FILENAME を $DEST_DIR にコピーしました。" >> "$LOGFILE"
        echo "✅ Successfully copied to $SERVICE"
    else
        echo "$(date): Error copying $FILENAME to $DEST_DIR" >> "$LOGFILE"
        echo "❌ Failed to copy to $SERVICE"
        exit 1
    fi
else
    # Copy to all services
    echo "Copying to all services"
    
    # コピー先のディレクトリを配列に格納
    DEST_DIRS=(
        "../cart/commons/dist"
        "../master-data/commons/dist"
        "../account/commons/dist"
        "../terminal/commons/dist"
        "../report/commons/dist"
        "../journal/commons/dist"
        "../stock/commons/dist"
    )

    # 各ディレクトリに対して処理を実行
    for DIR in "${DEST_DIRS[@]}"; do
        # Create directory if it doesn't exist
        mkdir -p "$DIR"
        
        if cp "$FILENAME" "$DIR"; then
            echo "$(date): $FILENAME を $DIR にコピーしました。" >> "$LOGFILE"
            echo "✅ Copied to $DIR"
        else
            echo "$(date): Error copying $FILENAME to $DIR" >> "$LOGFILE"
            echo "❌ Failed to copy to $DIR"
        fi
    done
fi

echo "コピー処理終了: $(date)" >> "$LOGFILE"

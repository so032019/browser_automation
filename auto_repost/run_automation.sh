#!/bin/bash

# X自動化ツール実行スクリプト
# cron実行用シェルスクリプト（ヘッドレスモードON/OFF切り替え対応）

# スクリプトの設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"
LOG_DIR="$SCRIPT_DIR/logs"
ENV_FILE="$PROJECT_ROOT/.env"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# ログディレクトリの作成
mkdir -p "$LOG_DIR"

# 使用方法の表示
show_usage() {
    echo "使用方法: $0 [OPTIONS]"
    echo ""
    echo "オプション:"
    echo "  --headless          ヘッドレスモードで実行（デフォルト）"
    echo "  --visible           ブラウザを表示して実行"
    echo "  --max-posts NUM     最大処理ポスト数（デフォルト: 10）"
    echo "  --debug             デバッグモードで実行"
    echo "  --skip-slack        Slack通知をスキップ"
    echo "  --help              このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 --headless --max-posts 20"
    echo "  $0 --visible --debug"
    echo "  $0 --skip-slack     # Slack通知なしで実行"
    echo "  $0  # デフォルト（ヘッドレス、10ポスト、Slack通知あり）"
}

# デフォルト設定
HEADLESS_MODE="--headless"
MAX_POSTS="10"
DEBUG_MODE=""
SKIP_SLACK=""

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --headless)
            HEADLESS_MODE="--headless"
            shift
            ;;
        --visible)
            HEADLESS_MODE=""
            shift
            ;;
        --max-posts)
            MAX_POSTS="$2"
            shift 2
            ;;
        --debug)
            DEBUG_MODE="--debug"
            shift
            ;;
        --skip-slack)
            SKIP_SLACK="--skip-slack"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "不明なオプション: $1"
            show_usage
            exit 1
            ;;
    esac
done

# ログファイルの設定
EXECUTION_LOG="$LOG_DIR/execution_$TIMESTAMP.log"
ERROR_LOG="$LOG_DIR/error_$TIMESTAMP.log"

# 実行開始ログ
echo "$(date '+%Y-%m-%d %H:%M:%S') - X自動化ツール実行開始" | tee -a "$EXECUTION_LOG"
echo "設定:" | tee -a "$EXECUTION_LOG"
echo "  - ヘッドレスモード: $([ -n "$HEADLESS_MODE" ] && echo "ON" || echo "OFF")" | tee -a "$EXECUTION_LOG"
echo "  - 最大ポスト数: $MAX_POSTS" | tee -a "$EXECUTION_LOG"
echo "  - デバッグモード: $([ -n "$DEBUG_MODE" ] && echo "ON" || echo "OFF")" | tee -a "$EXECUTION_LOG"
echo "  - Slack通知: $([ -n "$SKIP_SLACK" ] && echo "OFF" || echo "ON")" | tee -a "$EXECUTION_LOG"
echo "  - プロジェクトルート: $PROJECT_ROOT" | tee -a "$EXECUTION_LOG"
echo "  - 仮想環境: $VENV_PATH" | tee -a "$EXECUTION_LOG"
echo "  - Pythonスクリプト: $PYTHON_SCRIPT" | tee -a "$EXECUTION_LOG"
echo "  - 設定ファイル: $ENV_FILE" | tee -a "$EXECUTION_LOG"

# 前提条件のチェック
check_prerequisites() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 前提条件をチェック中..." | tee -a "$EXECUTION_LOG"

    # 仮想環境の存在確認（複数の候補をチェック）
    if [ ! -d "$VENV_PATH" ]; then
        # 代替パス1: スクリプトと同じディレクトリ
        ALT_VENV_PATH1="$SCRIPT_DIR/venv"
        # 代替パス2: 現在のディレクトリ
        ALT_VENV_PATH2="$(pwd)/venv"

        if [ -d "$ALT_VENV_PATH1" ]; then
            VENV_PATH="$ALT_VENV_PATH1"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 仮想環境を発見: $VENV_PATH" | tee -a "$EXECUTION_LOG"
        elif [ -d "$ALT_VENV_PATH2" ]; then
            VENV_PATH="$ALT_VENV_PATH2"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 仮想環境を発見: $VENV_PATH" | tee -a "$EXECUTION_LOG"
        else
            echo "エラー: 仮想環境が見つかりません。以下の場所を確認しました:" | tee -a "$ERROR_LOG"
            echo "  - $VENV_PATH" | tee -a "$ERROR_LOG"
            echo "  - $ALT_VENV_PATH1" | tee -a "$ERROR_LOG"
            echo "  - $ALT_VENV_PATH2" | tee -a "$ERROR_LOG"
            return 1
        fi
    fi

    # Pythonスクリプトの存在確認
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo "エラー: Pythonスクリプトが見つかりません: $PYTHON_SCRIPT" | tee -a "$ERROR_LOG"
        return 1
    fi

    # .envファイルの存在確認（複数の候補をチェック）
    if [ ! -f "$ENV_FILE" ]; then
        # 代替パス1: スクリプトと同じディレクトリ
        ALT_ENV_FILE1="$SCRIPT_DIR/.env"
        # 代替パス2: 現在のディレクトリ
        ALT_ENV_FILE2="$(pwd)/.env"

        if [ -f "$ALT_ENV_FILE1" ]; then
            ENV_FILE="$ALT_ENV_FILE1"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - .envファイルを発見: $ENV_FILE" | tee -a "$EXECUTION_LOG"
        elif [ -f "$ALT_ENV_FILE2" ]; then
            ENV_FILE="$ALT_ENV_FILE2"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - .envファイルを発見: $ENV_FILE" | tee -a "$EXECUTION_LOG"
        else
            echo "エラー: .envファイルが見つかりません。以下の場所を確認しました:" | tee -a "$ERROR_LOG"
            echo "  - $ENV_FILE" | tee -a "$ERROR_LOG"
            echo "  - $ALT_ENV_FILE1" | tee -a "$ERROR_LOG"
            echo "  - $ALT_ENV_FILE2" | tee -a "$ERROR_LOG"
            return 1
        fi
    fi

    echo "$(date '+%Y-%m-%d %H:%M:%S') - 前提条件チェック完了" | tee -a "$EXECUTION_LOG"
    return 0
}

# 仮想環境のアクティベート
activate_venv() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 仮想環境をアクティベート中..." | tee -a "$EXECUTION_LOG"

    # 仮想環境のアクティベートスクリプトを実行
    source "$VENV_PATH/bin/activate"

    if [ $? -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 仮想環境のアクティベート完了" | tee -a "$EXECUTION_LOG"
        return 0
    else
        echo "エラー: 仮想環境のアクティベートに失敗しました" | tee -a "$ERROR_LOG"
        return 1
    fi
}

# Pythonスクリプトの実行
execute_python_script() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Pythonスクリプト実行開始..." | tee -a "$EXECUTION_LOG"

    # 環境変数の設定
    export ENV_FILE_PATH="$ENV_FILE"

    # Pythonスクリプトの実行
    cd "$SCRIPT_DIR"
    python3 "$PYTHON_SCRIPT" $HEADLESS_MODE --max-posts "$MAX_POSTS" $DEBUG_MODE $SKIP_SLACK 2>&1 | tee -a "$EXECUTION_LOG"

    local exit_code=${PIPESTATUS[0]}

    if [ $exit_code -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Pythonスクリプト実行完了（成功）" | tee -a "$EXECUTION_LOG"
        return 0
    else
        echo "エラー: Pythonスクリプトの実行に失敗しました（終了コード: $exit_code）" | tee -a "$ERROR_LOG"
        return $exit_code
    fi
}

# クリーンアップ処理
cleanup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - クリーンアップ処理中..." | tee -a "$EXECUTION_LOG"

    # 仮想環境の非アクティベート
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi

    # 古いログファイルの削除（30日以上古いもの）
    find "$LOG_DIR" -name "*.log" -type f -mtime +30 -delete 2>/dev/null

    echo "$(date '+%Y-%m-%d %H:%M:%S') - クリーンアップ完了" | tee -a "$EXECUTION_LOG"
}

# メイン実行処理
main() {
    local exit_code=0

    # 前提条件チェック
    if ! check_prerequisites; then
        exit_code=1
    fi

    # 仮想環境アクティベート
    if [ $exit_code -eq 0 ] && ! activate_venv; then
        exit_code=1
    fi

    # Pythonスクリプト実行
    if [ $exit_code -eq 0 ] && ! execute_python_script; then
        exit_code=$?
    fi

    # クリーンアップ
    cleanup

    # 実行結果ログ
    if [ $exit_code -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - X自動化ツール実行完了（成功）" | tee -a "$EXECUTION_LOG"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - X自動化ツール実行完了（失敗: 終了コード $exit_code）" | tee -a "$ERROR_LOG"
    fi

    return $exit_code
}

# スクリプト実行
main
exit $?

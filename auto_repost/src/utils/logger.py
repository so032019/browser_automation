"""
ログ管理クラス
詳細なログ記録、エラーログとデバッグログの分類、ログファイルのローテーション
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """ログ管理クラス"""

    def __init__(self, debug: bool = False, log_dir: str = "logs"):
        """
        ログ管理の初期化

        Args:
            debug: デバッグモードの有効化
            log_dir: ログディレクトリのパス
        """
        self.debug_mode = debug
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # ロガーの設定
        self.logger = logging.getLogger('x_automation')
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # 既存のハンドラーをクリア
        self.logger.handlers.clear()

        # フォーマッターの設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # ファイルハンドラー（一般ログ）
        log_file = self.log_dir / f"x_automation_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # エラーログファイルハンドラー
        error_log_file = self.log_dir / f"x_automation_error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

        # デバッグログファイルハンドラー（デバッグモード時のみ）
        if debug:
            debug_log_file = self.log_dir / f"x_automation_debug_{datetime.now().strftime('%Y%m%d')}.log"
            debug_handler = logging.handlers.RotatingFileHandler(
                debug_log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=3,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(formatter)
            self.logger.addHandler(debug_handler)

    def info(self, message: str, extra_data: Optional[dict] = None):
        """
        情報ログの記録

        Args:
            message: ログメッセージ
            extra_data: 追加データ
        """
        if extra_data:
            message = f"{message} | Extra: {extra_data}"
        self.logger.info(message)

    def debug(self, message: str, extra_data: Optional[dict] = None):
        """
        デバッグログの記録

        Args:
            message: ログメッセージ
            extra_data: 追加データ
        """
        if extra_data:
            message = f"{message} | Extra: {extra_data}"
        self.logger.debug(message)

    def warning(self, message: str, extra_data: Optional[dict] = None):
        """
        警告ログの記録

        Args:
            message: ログメッセージ
            extra_data: 追加データ
        """
        if extra_data:
            message = f"{message} | Extra: {extra_data}"
        self.logger.warning(message)

    def error(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[dict] = None):
        """
        エラーログの記録

        Args:
            message: ログメッセージ
            exception: 例外オブジェクト
            extra_data: 追加データ
        """
        if extra_data:
            message = f"{message} | Extra: {extra_data}"

        if exception:
            message = f"{message} | Exception: {str(exception)}"
            self.logger.error(message, exc_info=True)
        else:
            self.logger.error(message)

    def critical(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[dict] = None):
        """
        重大エラーログの記録

        Args:
            message: ログメッセージ
            exception: 例外オブジェクト
            extra_data: 追加データ
        """
        if extra_data:
            message = f"{message} | Extra: {extra_data}"

        if exception:
            message = f"{message} | Exception: {str(exception)}"
            self.logger.critical(message, exc_info=True)
        else:
            self.logger.critical(message)

    def log_action(self, action: str, url: str = None, success: bool = True, details: str = None):
        """
        アクション実行ログの記録

        Args:
            action: アクション名
            url: 対象URL
            success: 成功/失敗
            details: 詳細情報
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"ACTION: {action} | STATUS: {status}"

        if url:
            message += f" | URL: {url}"

        if details:
            message += f" | DETAILS: {details}"

        if success:
            self.info(message)
        else:
            self.error(message)

    def log_performance(self, operation: str, duration: float, details: Optional[dict] = None):
        """
        パフォーマンスログの記録

        Args:
            operation: 操作名
            duration: 実行時間（秒）
            details: 詳細情報
        """
        message = f"PERFORMANCE: {operation} | DURATION: {duration:.2f}s"

        if details:
            message += f" | DETAILS: {details}"

        self.info(message)

    def get_log_summary(self) -> dict:
        """
        ログサマリーの取得

        Returns:
            dict: ログサマリー
        """
        return {
            'log_dir': str(self.log_dir),
            'debug_mode': self.debug_mode,
            'handlers_count': len(self.logger.handlers),
            'log_level': self.logger.level
        }

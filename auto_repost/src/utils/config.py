"""
設定管理クラス
.envファイルから認証情報を読み込み、実行パラメータを管理
"""

import os
from dataclasses import dataclass
from typing import Tuple
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """設定管理クラス"""
    username: str
    password: str
    max_posts_per_session: int = 10
    delay_between_actions: Tuple[int, int] = (2, 5)
    headless: bool = True
    stealth_mode: bool = True
    max_scroll_attempts: int = 10
    element_timeout: int = 10000
    browser_path: str = None  # カスタムブラウザパス
    # Slack通知設定
    slack_api_url: str = None
    slack_api_key: str = None
    slack_workspace: str = "default"
    # ログ設定
    log_dir: str = "logs"

    @classmethod
    def from_env(cls, env_path: str = None) -> 'Config':
        """
        .envファイルから設定を読み込み

        Args:
            env_path: .envファイルのパス（自動検出）

        Returns:
            Config: 設定インスタンス
        """
        if env_path is None:
            # 環境変数から.envファイルのパスを取得
            env_path = os.getenv('ENV_FILE_PATH')

            if env_path is None:
                # 自動検出: 複数の候補をチェック
                current_dir = Path.cwd()
                script_dir = Path(__file__).parent.parent.parent

                candidates = [
                    current_dir / '.env',
                    script_dir / '.env',
                    script_dir.parent / '.env',
                    Path.home() / 'dev/test/android_automate/x/.env'  # 開発環境用フォールバック
                ]

                for candidate in candidates:
                    if candidate.exists():
                        env_path = str(candidate)
                        break

                if env_path is None:
                    raise FileNotFoundError(f".envファイルが見つかりません。以下の場所を確認しました: {[str(c) for c in candidates]}")

        # .envファイルの読み込み
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            raise FileNotFoundError(f".envファイルが見つかりません: {env_path}")

        # 必須項目の取得
        username = os.getenv('X_USERNAME')
        password = os.getenv('X_PASSWORD')

        if not username or not password:
            raise ValueError("X_USERNAMEとX_PASSWORDが.envファイルに設定されている必要があります")

        # オプション項目の取得
        max_posts = int(os.getenv('MAX_POSTS_PER_SESSION', '10'))
        delay_min = int(os.getenv('DELAY_MIN', '2'))
        delay_max = int(os.getenv('DELAY_MAX', '5'))
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        stealth_mode = os.getenv('STEALTH_MODE', 'true').lower() == 'true'
        max_scroll_attempts = int(os.getenv('MAX_SCROLL_ATTEMPTS', '10'))
        element_timeout = int(os.getenv('ELEMENT_TIMEOUT', '10000'))
        browser_path = os.getenv('BROWSER_PATH')  # カスタムブラウザパス

        # Slack通知設定
        slack_api_url = os.getenv('SLACK_API_URL')
        slack_api_key = os.getenv('SLACK_API_KEY')
        slack_workspace = os.getenv('SLACK_WORKSPACE', 'default')

        # ログ設定
        log_dir = os.getenv('LOG_DIR', 'logs')

        return cls(
            username=username,
            password=password,
            max_posts_per_session=max_posts,
            delay_between_actions=(delay_min, delay_max),
            headless=headless,
            stealth_mode=stealth_mode,
            max_scroll_attempts=max_scroll_attempts,
            element_timeout=element_timeout,
            browser_path=browser_path,
            slack_api_url=slack_api_url,
            slack_api_key=slack_api_key,
            slack_workspace=slack_workspace,
            log_dir=log_dir
        )

    def validate(self) -> bool:
        """
        設定値のバリデーション

        Returns:
            bool: バリデーション結果
        """
        if not self.username or not self.password:
            return False

        if self.max_posts_per_session <= 0:
            return False

        if self.delay_between_actions[0] < 0 or self.delay_between_actions[1] < self.delay_between_actions[0]:
            return False

        if self.max_scroll_attempts <= 0:
            return False

        if self.element_timeout <= 0:
            return False

        return True

    def to_dict(self) -> dict:
        """
        設定を辞書形式で返す

        Returns:
            dict: 設定辞書
        """
        return {
            'username': self.username,
            'password': '***',  # パスワードはマスク
            'max_posts_per_session': self.max_posts_per_session,
            'delay_between_actions': self.delay_between_actions,
            'headless': self.headless,
            'stealth_mode': self.stealth_mode,
            'max_scroll_attempts': self.max_scroll_attempts,
            'element_timeout': self.element_timeout,
            'browser_path': self.browser_path,
            'slack_api_url': self.slack_api_url,
            'slack_api_key': '***' if self.slack_api_key else None,  # APIキーはマスク
            'slack_workspace': self.slack_workspace,
            'log_dir': self.log_dir
        }

"""
ログイン処理クラス
X.comへのナビゲーション、ログインフォームの要素検出と入力処理
"""

import asyncio
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from src.utils.config import Config
from src.utils.logger import Logger
from src.utils.selectors import SelectorManager


class LoginHandler:
    """ログイン処理クラス"""

    def __init__(self, page: Page, config: Config):
        """
        ログイン処理の初期化

        Args:
            page: Playwrightページインスタンス
            config: 設定インスタンス
        """
        self.page = page
        self.config = config
        self.logger = Logger()
        self.selector_manager = SelectorManager()
        self.login_selectors = self.selector_manager.get_login_selectors()

    async def login(self, username: str, password: str) -> bool:
        """
        X.comにログイン

        Args:
            username: ユーザー名
            password: パスワード

        Returns:
            bool: ログイン成功/失敗
        """
        try:
            # 既にX.comにアクセス済みかチェック
            current_url = self.page.url
            if 'x.com' not in current_url:
                self.logger.info("X.comにアクセス中...")
                # タイムアウトを60秒に延長し、domcontentloadedで待機
                await self.page.goto('https://x.com/', wait_until='domcontentloaded', timeout=60000)
                self.logger.info("ページの基本読み込み完了、追加読み込みを待機中...")
                await asyncio.sleep(3)

                # ページが完全に読み込まれるまで少し待機
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                    self.logger.info("ネットワーク活動が安定しました")
                except PlaywrightTimeoutError:
                    self.logger.info("ネットワーク活動のタイムアウト（続行します）")
            else:
                self.logger.info("既にX.comにアクセス済みです")

            # 既にログイン済みかチェック
            if await self._is_already_logged_in():
                self.logger.info("既にログイン済みです ✅")
                return True

            # ログインボタンをクリック
            if not await self._click_login_button():
                return False

            # ユーザー名入力
            if not await self._input_username(username):
                return False

            # 次へボタンをクリック
            if not await self._click_next_button():
                return False

            # パスワード入力
            if not await self._input_password(password):
                return False

            # ログイン完了を待機
            if not await self.wait_for_login_success():
                return False

            self.logger.info("ログインに成功しました")
            return True

        except Exception as e:
            self.logger.error("ログイン処理中にエラーが発生しました", exception=e)
            return False

    async def _click_login_button(self) -> bool:
        """
        ログインボタンをクリック

        Returns:
            bool: 成功/失敗
        """
        try:
            for selector in self.login_selectors['login_button']:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    self.logger.info(f"ログインボタンをクリックしました: {selector}")
                    await asyncio.sleep(2)
                    return True
                except PlaywrightTimeoutError:
                    continue

            self.logger.error("ログインボタンが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("ログインボタンのクリックに失敗しました", exception=e)
            return False

    async def _input_username(self, username: str) -> bool:
        """
        ユーザー名を入力

        Args:
            username: ユーザー名

        Returns:
            bool: 成功/失敗
        """
        try:
            for selector in self.login_selectors['username_input']:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    await self.page.fill(selector, username)
                    self.logger.info(f"ユーザー名を入力しました: {selector}")
                    await asyncio.sleep(1)
                    return True
                except PlaywrightTimeoutError:
                    continue

            self.logger.error("ユーザー名入力フィールドが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("ユーザー名の入力に失敗しました", exception=e)
            return False

    async def _click_next_button(self) -> bool:
        """
        次へボタンをクリック

        Returns:
            bool: 成功/失敗
        """
        try:
            for selector in self.login_selectors['next_button']:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    self.logger.info(f"次へボタンをクリックしました: {selector}")
                    await asyncio.sleep(2)
                    return True
                except PlaywrightTimeoutError:
                    continue

            # フォールバック: テキストベースの検索
            try:
                await self.page.click("button:has-text('次へ')")
                self.logger.info("次へボタンをクリックしました (テキストベース)")
                await asyncio.sleep(2)
                return True
            except:
                pass

            self.logger.error("次へボタンが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("次へボタンのクリックに失敗しました", exception=e)
            return False

    async def _input_password(self, password: str) -> bool:
        """
        パスワードを入力

        Args:
            password: パスワード

        Returns:
            bool: 成功/失敗
        """
        try:
            for selector in self.login_selectors['password_input']:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    await self.page.fill(selector, password)
                    self.logger.info(f"パスワードを入力しました: {selector}")

                    # Enterキーでログイン実行
                    await self.page.press(selector, 'Enter')
                    await asyncio.sleep(3)
                    return True
                except PlaywrightTimeoutError:
                    continue

            self.logger.error("パスワード入力フィールドが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("パスワードの入力に失敗しました", exception=e)
            return False

    async def wait_for_login_success(self, timeout: int = 30000) -> bool:
        """
        ログイン成功を待機

        Args:
            timeout: タイムアウト時間（ミリ秒）

        Returns:
            bool: ログイン成功/失敗
        """
        try:
            # ホーム画面の要素を待機（複数の候補）
            success_indicators = [
                "[data-testid='primaryColumn']",
                "[data-testid='SideNav_NewTweet_Button']",
                "nav[role='navigation']",
                "[aria-label='ホーム']"
            ]

            for indicator in success_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=timeout)
                    self.logger.info(f"ログイン成功を確認しました: {indicator}")
                    return True
                except PlaywrightTimeoutError:
                    continue

            # URLベースの確認
            current_url = self.page.url
            if 'home' in current_url or current_url == 'https://x.com/':
                self.logger.info("ログイン成功を確認しました (URL)")
                return True

            # エラーメッセージの確認
            error_message = await self.handle_login_errors()
            if error_message:
                self.logger.error(f"ログインエラー: {error_message}")

            return False

        except Exception as e:
            self.logger.error("ログイン成功の確認中にエラーが発生しました", exception=e)
            return False

    async def _is_already_logged_in(self) -> bool:
        """
        既にログイン済みかチェック

        Returns:
            bool: ログイン済みかどうか
        """
        try:
            self.logger.info("ログイン状態を確認中...")

            # 現在のURLを確認
            current_url = self.page.url
            self.logger.info(f"現在のURL: {current_url}")

            # ログインページかどうかを確認
            login_page_indicators = [
                '/i/flow/login',
                '/login',
                '/oauth/authenticate'
            ]

            for indicator in login_page_indicators:
                if indicator in current_url:
                    self.logger.info(f"ログインページを検出: {indicator}")
                    return False

            # ログイン済み要素の確認（URLチェック後）
            login_indicators = [
                "[data-testid='SideNav_NewTweet_Button']",
                "[data-testid='primaryColumn']",
                "[data-testid='AppTabBar_Home_Link']",  # モバイル用ホームリンク
                "[data-testid='DashButton_ProfileIcon_Link']"  # プロフィールアイコン
            ]

            for selector in login_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        self.logger.info(f"ログイン済み要素を発見: {selector}")
                        return True
                except PlaywrightTimeoutError:
                    continue

            # ログインページ特有の要素をチェック（二重確認）
            login_page_elements = [
                "[data-testid='loginButton']",
                "[data-testid='signupButton']",
                "input[name='text']",  # ユーザー名入力フィールド
                "input[name='password']",  # パスワード入力フィールド
                "[data-testid='google_sign_in_container']",  # Google サインイン
                "[data-testid='apple_sign_in_button']"  # Apple サインイン
            ]

            for selector in login_page_elements:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        self.logger.info(f"ログインページ要素を発見: {selector}")
                        return False
                except PlaywrightTimeoutError:
                    continue

            self.logger.info("ログイン状態の判定が困難です。ログインが必要と判断します。")
            return False

        except Exception as e:
            self.logger.error("ログイン状態確認中にエラーが発生しました", exception=e)
            return False

    async def handle_login_errors(self) -> Optional[str]:
        """
        ログインエラーの処理

        Returns:
            str: エラーメッセージ（エラーがない場合はNone）
        """
        try:
            # エラーメッセージの候補
            error_selectors = [
                "[data-testid='error-message']",
                "[role='alert']",
                ".error-message",
                "[data-testid='LoginForm_Login_Button']:disabled"
            ]

            for selector in error_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        error_text = await element.text_content()
                        if error_text and error_text.strip():
                            return error_text.strip()
                except PlaywrightTimeoutError:
                    continue

            # 特定のエラーテキストを検索
            error_texts = [
                "パスワードが間違っています",
                "ユーザー名が見つかりません",
                "アカウントがロックされています",
                "認証に失敗しました"
            ]

            page_content = await self.page.content()
            for error_text in error_texts:
                if error_text in page_content:
                    return error_text

            return None

        except Exception as e:
            self.logger.error("エラーメッセージの確認中にエラーが発生しました", exception=e)
            return "エラーメッセージの確認に失敗しました"

    async def is_logged_in(self) -> bool:
        """
        ログイン状態の確認

        Returns:
            bool: ログイン済みかどうか
        """
        try:
            # 現在のURLを確認
            current_url = self.page.url
            self.logger.info(f"現在のURL: {current_url}")

            # ログインページかどうかを確認
            login_page_indicators = [
                '/i/flow/login',
                '/login',
                '/oauth/authenticate'
            ]

            for indicator in login_page_indicators:
                if indicator in current_url:
                    self.logger.info(f"ログインページを検出: {indicator}")
                    return False

            # ログイン状態を示す要素の確認
            login_indicators = [
                "[data-testid='SideNav_NewTweet_Button']",
                "[data-testid='primaryColumn']",
                "[data-testid='AppTabBar_Home_Link']",
                "[data-testid='DashButton_ProfileIcon_Link']"
            ]

            for indicator in login_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=3000)
                    self.logger.info(f"ログイン済み要素を発見: {indicator}")
                    return True
                except PlaywrightTimeoutError:
                    continue

            return False

        except Exception as e:
            self.logger.error("ログイン状態の確認中にエラーが発生しました", exception=e)
            return False

"""
ブラウザ管理クラス
Playwrightブラウザの起動・終了、ブラウザコンテキストの作成・管理
"""

import random
from typing import Optional
from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright
from src.utils.logger import Logger


class BrowserManager:
    """ブラウザ管理クラス"""

    def __init__(self, headless: bool = True, stealth: bool = True, browser_path: Optional[str] = None):
        """
        ブラウザ管理の初期化

        Args:
            headless: ヘッドレスモードの有効化
            stealth: ステルスモードの有効化
            browser_path: カスタムブラウザのパス（例: /usr/bin/brave-browser）
        """
        self.headless = headless
        self.stealth = stealth
        self.browser_path = browser_path
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.logger = Logger()

        # Cookie保存用のディレクトリ
        self.user_data_dir = "/tmp/x_automation_profile"

        # User-Agentのリスト
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]

    async def launch_browser(self) -> Browser:
        """
        ブラウザの起動

        Returns:
            Browser: ブラウザインスタンス
        """
        try:
            self.playwright = await async_playwright().start()

            # ブラウザ起動オプション
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',

                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            }

            # カスタムブラウザパスの指定
            if self.browser_path:
                launch_options['executable_path'] = self.browser_path
                self.logger.info(f"カスタムブラウザを使用: {self.browser_path}")

            # ステルスモード用の追加オプション
            if self.stealth:
                launch_options['args'].extend([
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-ipc-flooding-protection',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-client-side-phishing-detection',
                    '--disable-sync',
                    '--disable-default-apps',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-extensions-file-access-check',
                    '--disable-extensions-http-throttling'
                ])

            self.browser = await self.playwright.chromium.launch(**launch_options)
            self.logger.info(f"ブラウザを起動しました (headless: {self.headless}, stealth: {self.stealth})")

            return self.browser

        except Exception as e:
            self.logger.error("ブラウザの起動に失敗しました", exception=e)
            raise

    async def create_context(self) -> BrowserContext:
        """
        ブラウザコンテキストの作成（Cookie保存対応）

        Returns:
            BrowserContext: ブラウザコンテキスト
        """
        if not self.browser:
            raise RuntimeError("ブラウザが起動されていません")

        try:
            # Cookie保存ディレクトリの作成
            import os
            os.makedirs(self.user_data_dir, exist_ok=True)

            # コンテキスト作成オプション
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': random.choice(self.user_agents),
                'java_script_enabled': True,
                'accept_downloads': False,
                'ignore_https_errors': True,
                'bypass_csp': True,
                'storage_state': f"{self.user_data_dir}/state.json",  # Cookie保存
                'extra_http_headers': {
                    'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    'Cache-Control': 'no-cache'
                }
            }

            # 既存のCookieファイルがあるかチェック
            state_file = f"{self.user_data_dir}/state.json"
            if not os.path.exists(state_file):
                # 初回実行時はstorage_stateを指定しない
                context_options.pop('storage_state')
                self.logger.info("初回実行: 新しいブラウザコンテキストを作成")
            else:
                self.logger.info("既存のCookie情報を読み込み")

            self.context = await self.browser.new_context(**context_options)

            # ステルスモード設定
            if self.stealth:
                await self.setup_stealth_mode(self.context)

            self.logger.info("ブラウザコンテキストを作成しました")
            return self.context

        except Exception as e:
            self.logger.error("ブラウザコンテキストの作成に失敗しました", exception=e)
            raise

    async def setup_stealth_mode(self, context: BrowserContext):
        """
        ステルスモードの設定

        Args:
            context: ブラウザコンテキスト
        """
        try:
            # WebDriverフラグの無効化とその他のステルス設定
            await context.add_init_script("""
                // WebDriverフラグの削除
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Chrome検出の回避
                window.chrome = {
                    runtime: {},
                };

                // プラグイン情報の偽装
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // 言語設定
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ja-JP', 'ja', 'en'],
                });

                // プラットフォーム情報
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });

                // 権限API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // WebGL情報の偽装
                const getParameter = WebGLRenderingContext.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel(R) Iris(TM) Graphics 6100';
                    }
                    return getParameter(parameter);
                };

                // 拡張機能検出の回避
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                });

                // プライバシー拡張機能の検出を回避
                delete window.onerror;
                delete window.onunhandledrejection;
            """)

            self.logger.info("ステルスモードを設定しました")

        except Exception as e:
            self.logger.error("ステルスモードの設定に失敗しました", exception=e)
            raise

    async def save_cookies(self):
        """Cookie情報を保存"""
        try:
            if self.context:
                state_file = f"{self.user_data_dir}/state.json"
                await self.context.storage_state(path=state_file)
                self.logger.info("Cookie情報を保存しました")
        except Exception as e:
            self.logger.error("Cookie保存中にエラーが発生しました", exception=e)

    async def close(self):
        """ブラウザとコンテキストの終了"""
        try:
            # Cookie保存
            await self.save_cookies()

            if self.context:
                await self.context.close()
                self.context = None
                self.logger.info("ブラウザコンテキストを終了しました")

            if self.browser:
                await self.browser.close()
                self.browser = None
                self.logger.info("ブラウザを終了しました")

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                self.logger.info("Playwrightを終了しました")

            # 一時プロファイルディレクトリのクリーンアップ
            import shutil
            import os
            temp_profile = '/tmp/playwright_chrome_profile'
            if os.path.exists(temp_profile):
                try:
                    shutil.rmtree(temp_profile)
                    self.logger.info("一時プロファイルディレクトリを削除しました")
                except:
                    pass

        except Exception as e:
            self.logger.error("ブラウザの終了中にエラーが発生しました", exception=e)

    def is_browser_running(self) -> bool:
        """
        ブラウザの実行状態を確認

        Returns:
            bool: ブラウザが実行中かどうか
        """
        return self.browser is not None and self.context is not None

    async def get_new_page(self):
        """
        新しいページを取得

        Returns:
            Page: 新しいページインスタンス
        """
        if not self.context:
            raise RuntimeError("ブラウザコンテキストが作成されていません")

        page = await self.context.new_page()
        self.logger.info("新しいページを作成しました")
        return page

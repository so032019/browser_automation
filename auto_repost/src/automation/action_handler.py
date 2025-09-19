"""
アクション処理クラス
個別ポストでのフォロー、リポスト、いいね処理
"""

import asyncio
import random
from typing import Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from src.utils.logger import Logger
from src.utils.selectors import SelectorManager


class ActionHandler:
    """アクション処理クラス"""

    def __init__(self, page: Page):
        """
        アクション処理の初期化

        Args:
            page: Playwrightページインスタンス
        """
        self.page = page
        self.logger = Logger()
        self.selector_manager = SelectorManager()
        self.post_action_selectors = self.selector_manager.get_post_action_selectors()

    async def navigate_to_post(self, url: str) -> bool:
        """
        個別ポストページに移動

        Args:
            url: ポストURL

        Returns:
            bool: ナビゲーション成功/失敗
        """
        try:
            # URLをクリーンアップ（analytics等の不要な部分を削除）
            clean_url = self._clean_post_url(url)
            self.logger.info(f"ポストページに移動中: {clean_url}")

            # ページに移動（タイムアウトを延長し、domcontentloadedで待機）
            await self.page.goto(clean_url, wait_until='domcontentloaded', timeout=60000)
            self.logger.info("ページの基本読み込み完了、追加読み込みを待機中...")
            await asyncio.sleep(3)

            # ネットワーク活動の安定化を待機（タイムアウト短縮）
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
                self.logger.info("ネットワーク活動が安定しました")
            except Exception:
                self.logger.info("ネットワーク活動のタイムアウト（続行します）")

            # ページ読み込み完了を確認
            if await self._wait_for_page_load():
                self.logger.info("ポストページの読み込みが完了しました")
                return True
            else:
                self.logger.error("ポストページの読み込みに失敗しました")
                return False

        except Exception as e:
            self.logger.error(f"ポストページへの移動中にエラーが発生しました: {url}", exception=e)
            return False

    async def _wait_for_page_load(self) -> bool:
        """
        ページ読み込み完了を待機

        Returns:
            bool: 読み込み完了/失敗
        """
        try:
            # ポストページを示す要素を待機
            page_indicators = [
                "[data-testid='tweet']",
                "article",
                "[role='article']",
                "[data-testid='cellInnerDiv']"
            ]

            for indicator in page_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=10000)
                    return True
                except PlaywrightTimeoutError:
                    continue

            return False

        except Exception as e:
            self.logger.error("ページ読み込み待機中にエラーが発生しました", exception=e)
            return False

    async def follow_user(self) -> bool:
        """
        ユーザーをフォロー

        Returns:
            bool: フォロー成功/失敗
        """
        try:
            self.logger.info("フォロー処理を開始します")

            # フォローボタンを検索
            for selector in self.post_action_selectors['follow_button']:
                try:
                    # 要素の存在確認
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # ボタンのテキストを確認（既にフォロー済みかチェック）
                        button_text = await element.text_content()
                        if button_text and ('フォロー中' in button_text or 'Following' in button_text):
                            self.logger.info("既にフォロー済みです")
                            return True

                        # フォローボタンをクリック
                        await element.click()
                        self.logger.info(f"フォローボタンをクリックしました: {selector}")
                        await asyncio.sleep(2)

                        # フォロー完了を確認
                        if await self._verify_follow_success():
                            self.logger.info("フォローが完了しました")
                            return True

                except PlaywrightTimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"フォローボタンのクリック中にエラー: {selector}", exception=e)
                    continue

            # フォールバック: テキストベースの検索
            try:
                follow_button = await self.page.query_selector("button:has-text('フォロー')")
                if follow_button:
                    await follow_button.click()
                    self.logger.info("フォローボタンをクリックしました (テキストベース)")
                    await asyncio.sleep(2)
                    return True
            except:
                pass

            self.logger.warning("フォローボタンが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("フォロー処理中にエラーが発生しました", exception=e)
            return False

    async def _verify_follow_success(self) -> bool:
        """
        フォロー成功を確認

        Returns:
            bool: フォロー成功/失敗
        """
        try:
            # フォロー完了を示すテキストを確認
            success_texts = ['フォロー中', 'Following', 'フォロー済み']

            for text in success_texts:
                try:
                    await self.page.wait_for_selector(f"button:has-text('{text}')", timeout=3000)
                    return True
                except PlaywrightTimeoutError:
                    continue

            return False

        except Exception as e:
            self.logger.error("フォロー成功確認中にエラーが発生しました", exception=e)
            return False

    async def repost_content(self) -> bool:
        """
        コンテンツをリポスト

        Returns:
            bool: リポスト成功/失敗
        """
        try:
            self.logger.info("リポスト処理を開始します")

            # リポストボタンを検索
            for selector in self.post_action_selectors['repost_button']:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # リポストボタンをクリック
                        await element.click()
                        self.logger.info(f"リポストボタンをクリックしました: {selector}")
                        await asyncio.sleep(2)

                        # リポスト確認ダイアログの処理
                        if await self._handle_repost_confirmation():
                            self.logger.info("リポストが完了しました")
                            return True

                except PlaywrightTimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"リポストボタンのクリック中にエラー: {selector}", exception=e)
                    continue

            # フォールバック: テキストベースの検索
            try:
                repost_button = await self.page.query_selector("button:has-text('リポスト')")
                if repost_button:
                    await repost_button.click()
                    self.logger.info("リポストボタンをクリックしました (テキストベース)")
                    await asyncio.sleep(2)

                    if await self._handle_repost_confirmation():
                        return True
            except:
                pass

            self.logger.warning("リポストボタンが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("リポスト処理中にエラーが発生しました", exception=e)
            return False

    async def _handle_repost_confirmation(self) -> bool:
        """
        リポスト確認ダイアログの処理

        Returns:
            bool: 確認成功/失敗
        """
        try:
            # リポスト確認ボタンを検索
            for selector in self.post_action_selectors['repost_confirm']:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        await element.click()
                        self.logger.info(f"リポスト確認ボタンをクリックしました: {selector}")
                        await asyncio.sleep(2)
                        return True
                except PlaywrightTimeoutError:
                    continue

            # フォールバック: テキストベースの確認
            confirmation_texts = ['リポスト', 'Repost', '再投稿']
            for text in confirmation_texts:
                try:
                    confirm_button = await self.page.wait_for_selector(f"button:has-text('{text}')", timeout=3000)
                    if confirm_button:
                        await confirm_button.click()
                        self.logger.info(f"リポスト確認ボタンをクリックしました (テキスト: {text})")
                        await asyncio.sleep(2)
                        return True
                except PlaywrightTimeoutError:
                    continue

            # 確認ダイアログが表示されない場合（既にリポスト済みなど）
            self.logger.info("リポスト確認ダイアログが表示されませんでした（既にリポスト済みの可能性）")
            return True

        except Exception as e:
            self.logger.error("リポスト確認処理中にエラーが発生しました", exception=e)
            return False

    async def like_post(self) -> bool:
        """
        ポストにいいね

        Returns:
            bool: いいね成功/失敗
        """
        try:
            self.logger.info("いいね処理を開始します")

            # いいねボタンを検索
            for selector in self.post_action_selectors['like_button']:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # 既にいいね済みかチェック
                        is_liked = await self._is_already_liked(element)
                        if is_liked:
                            self.logger.info("既にいいね済みです")
                            return True

                        # いいねボタンをクリック
                        await element.click()
                        self.logger.info(f"いいねボタンをクリックしました: {selector}")
                        await asyncio.sleep(1)
                        return True

                except PlaywrightTimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"いいねボタンのクリック中にエラー: {selector}", exception=e)
                    continue

            # フォールバック: テキストベースの検索
            try:
                like_button = await self.page.query_selector("button:has-text('いいね')")
                if like_button:
                    await like_button.click()
                    self.logger.info("いいねボタンをクリックしました (テキストベース)")
                    await asyncio.sleep(1)
                    return True
            except:
                pass

            self.logger.warning("いいねボタンが見つかりませんでした")
            return False

        except Exception as e:
            self.logger.error("いいね処理中にエラーが発生しました", exception=e)
            return False

    async def _is_already_liked(self, element) -> bool:
        """
        既にいいね済みかチェック

        Args:
            element: いいねボタン要素

        Returns:
            bool: いいね済みかどうか
        """
        try:
            # ボタンの状態やクラスをチェック
            class_name = await element.get_attribute('class')
            aria_pressed = await element.get_attribute('aria-pressed')

            if aria_pressed == 'true':
                return True

            if class_name and ('liked' in class_name or 'active' in class_name):
                return True

            return False

        except Exception as e:
            self.logger.error("いいね状態の確認中にエラーが発生しました", exception=e)
            return False

    async def wait_for_element(self, selector: str, timeout: int = 10000):
        """
        要素の出現を待機

        Args:
            selector: セレクタ
            timeout: タイムアウト時間（ミリ秒）

        Returns:
            Element: 要素（見つからない場合はNone）
        """
        try:
            return await self.page.wait_for_selector(selector, timeout=timeout)
        except PlaywrightTimeoutError:
            self.logger.warning(f"要素が見つかりませんでした: {selector}")
            return None
        except Exception as e:
            self.logger.error(f"要素待機中にエラーが発生しました: {selector}", exception=e)
            return None

    async def random_delay(self, min_delay: int = 2, max_delay: int = 5):
        """
        ランダム遅延

        Args:
            min_delay: 最小遅延時間（秒）
            max_delay: 最大遅延時間（秒）
        """
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"ランダム遅延: {delay:.2f}秒")
        await asyncio.sleep(delay)

    async def perform_all_actions(self, url: str) -> dict:
        """
        指定されたポストで全てのアクションを実行

        Args:
            url: ポストURL

        Returns:
            dict: 実行結果
        """
        results = {
            'url': url,
            'navigation': False,
            'follow': False,
            'repost': False,
            'like': False
        }

        try:
            # ポストページに移動
            results['navigation'] = await self.navigate_to_post(url)
            if not results['navigation']:
                return results

            # ランダム遅延
            await self.random_delay(1, 3)

            # フォロー実行
            results['follow'] = await self.follow_user()
            await self.random_delay(2, 4)

            # リポスト実行
            results['repost'] = await self.repost_content()
            await self.random_delay(1, 3)

            # いいね実行
            results['like'] = await self.like_post()

            return results

        except Exception as e:
            self.logger.error(f"アクション実行中にエラーが発生しました: {url}", exception=e)
            return results
    def _clean_post_url(self, url: str) -> str:
        """
        ポストURLをクリーンアップ（不要なパラメータを削除）

        Args:
            url: 元のURL

        Returns:
            str: クリーンアップされたURL
        """
        try:
            # analytics等の不要な部分を削除
            if '/analytics' in url:
                url = url.replace('/analytics', '')
                self.logger.info(f"URLから/analyticsを削除しました")

            # その他の不要なパラメータも削除
            if '?' in url:
                base_url = url.split('?')[0]
                self.logger.info(f"URLからクエリパラメータを削除しました")
                return base_url

            return url

        except Exception as e:
            self.logger.error(f"URL クリーンアップ中にエラー: {e}")
            return url

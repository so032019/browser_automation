"""
検索処理クラス
検索クエリ生成、直接URL検索実行、スクロール機能とURL収集
"""

import asyncio
import re
import urllib.parse
from datetime import datetime
from typing import List, Set
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from src.utils.logger import Logger
from src.utils.selectors import SelectorManager


class SearchHandler:
    """検索処理クラス"""

    def __init__(self, page: Page):
        """
        検索処理の初期化

        Args:
            page: Playwrightページインスタンス
        """
        self.page = page
        self.logger = Logger()
        self.selector_manager = SelectorManager()
        self.search_selectors = self.selector_manager.get_search_selectors()
        self.timeline_selectors = self.selector_manager.get_timeline_selectors()

    def generate_search_query(self) -> str:
        """
        日付付きキーワードの検索クエリを生成

        Returns:
            str: 検索クエリ
        """
        current_date = datetime.now()
        date_str_1 = current_date.strftime("%m/%d")
        date_str_2 = current_date.strftime("%-m/%-d")
        query = f"リポスト フォロー キャンペーン プレゼント ({date_str_1} or {date_str_2})"

        self.logger.info(f"検索クエリを生成しました: {query}")
        return query

    def build_search_url(self, query: str) -> str:
        """
        検索URLを構築

        Args:
            query: 検索クエリ

        Returns:
            str: 検索URL
        """
        base_url = "https://x.com/search"
        params = {
            'q': query,
            'src': 'typed_query',
            'f': 'live'  # 最新ツイート表示
        }
        search_url = f"{base_url}?{urllib.parse.urlencode(params)}"

        self.logger.info(f"検索URLを構築しました: {search_url}")
        return search_url

    async def perform_search(self, query: str) -> bool:
        """
        直接URL方式で検索を実行

        Args:
            query: 検索クエリ

        Returns:
            bool: 検索成功/失敗
        """
        try:
            self.logger.info(f"直接URL方式で検索を実行中: {query}")

            # 検索URLを構築
            search_url = self.build_search_url(query)

            # 検索ページに直接ナビゲーション
            if not await self._navigate_to_search_url(search_url):
                return False

            # 検索結果の読み込み待機
            if not await self._wait_for_search_results():
                return False

            self.logger.info("検索が完了しました")
            return True

        except Exception as e:
            self.logger.error("検索実行中にエラーが発生しました", exception=e)
            return False

    async def _navigate_to_search_url(self, search_url: str) -> bool:
        """
        検索URLに直接ナビゲーション

        Args:
            search_url: 検索URL

        Returns:
            bool: 成功/失敗
        """
        try:
            self.logger.info(f"検索URLにナビゲーション中: {search_url}")

            # より柔軟な読み込み方式で検索ページに移動
            try:
                # まず基本的な読み込みを試行
                await self.page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                self.logger.info("DOMContentLoaded完了")
            except PlaywrightTimeoutError:
                self.logger.warning("DOMContentLoaded待機がタイムアウト、load待機に切り替え")
                try:
                    # DOMContentLoadedがタイムアウトした場合、load待機に切り替え
                    await self.page.goto(search_url, wait_until='load', timeout=20000)
                    self.logger.info("Load完了")
                except PlaywrightTimeoutError:
                    self.logger.warning("Load待機もタイムアウト、基本的なナビゲーションのみ実行")
                    # 最後の手段として、待機なしでナビゲーション
                    await self.page.goto(search_url, timeout=10000)
                    self.logger.info("基本ナビゲーション完了")

            # 追加の読み込み待機
            await asyncio.sleep(3)

            # 現在のURLを確認
            current_url = self.page.url
            self.logger.info(f"ナビゲーション後のURL: {current_url}")

            # ログインページにリダイレクトされていないかチェック
            login_page_indicators = [
                '/i/flow/login',
                '/login',
                '/oauth/authenticate'
            ]

            for indicator in login_page_indicators:
                if indicator in current_url:
                    self.logger.error(f"ログインページにリダイレクトされました: {current_url}")
                    self.logger.error("検索を実行するにはログインが必要です")
                    return False

            # 検索ページに正常に移動できたかチェック
            if 'search' in current_url.lower():
                self.logger.info("検索ページへのナビゲーションが成功しました")

                # 基本的な要素が読み込まれているかチェック
                basic_elements = [
                    "main",
                    "[role='main']",
                    "body"
                ]

                for element_selector in basic_elements:
                    try:
                        await self.page.wait_for_selector(element_selector, timeout=5000)
                        self.logger.info(f"基本要素を確認: {element_selector}")
                        break
                    except PlaywrightTimeoutError:
                        continue

                return True
            else:
                self.logger.error(f"検索ページへのナビゲーションに失敗しました。現在のURL: {current_url}")
                return False

        except PlaywrightTimeoutError:
            self.logger.error("検索ページの読み込みがタイムアウトしました")
            # タイムアウトしても現在のURLをチェック
            try:
                current_url = self.page.url
                self.logger.info(f"タイムアウト時のURL: {current_url}")
                if 'search' in current_url.lower():
                    self.logger.info("タイムアウトしましたが、検索ページには到達しています")
                    return True
            except:
                pass
            return False
        except Exception as e:
            self.logger.error("検索URLナビゲーション中にエラーが発生しました", exception=e)
            return False

    async def _wait_for_search_results(self) -> bool:
        """
        検索結果の読み込みを待機

        Returns:
            bool: 成功/失敗
        """
        try:
            # 現在のURLを確認
            current_url = self.page.url
            self.logger.info(f"検索結果ページのURL: {current_url}")

            # 検索結果ページかどうかを確認
            if 'search' not in current_url.lower():
                self.logger.warning("検索結果ページに遷移していない可能性があります")
                return False

            # 検索結果を示す要素を待機
            result_indicators = [
                "[data-testid='tweet']",
                "article",
                "[data-testid='cellInnerDiv']",
                "[role='article']"
            ]

            for indicator in result_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=15000)
                    self.logger.info(f"検索結果を確認しました: {indicator}")

                    # 検索結果の数を確認
                    elements = await self.page.query_selector_all(indicator)
                    self.logger.info(f"検索結果の要素数: {len(elements)}個")

                    # 検索結果が存在することを確認
                    if len(elements) > 0:
                        await asyncio.sleep(2)
                        return True
                    else:
                        self.logger.warning(f"要素は見つかりましたが、検索結果が0件です: {indicator}")
                        continue

                except PlaywrightTimeoutError:
                    self.logger.debug(f"要素が見つかりませんでした: {indicator}")
                    continue

            # 「結果が見つかりません」などのメッセージをチェック
            no_results_indicators = [
                "text=結果が見つかりません",
                "text=No results",
                "[data-testid='emptyState']"
            ]

            for indicator in no_results_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=3000)
                    if element:
                        self.logger.warning("検索結果が0件でした")
                        return False
                except PlaywrightTimeoutError:
                    continue

            self.logger.error("検索結果が表示されませんでした")
            return False

        except Exception as e:
            self.logger.error("検索結果の待機中にエラーが発生しました", exception=e)
            return False

    async def extract_post_urls_with_scroll(self, max_posts: int = 20) -> List[str]:
        """
        スクロール付きでポストURLを抽出

        Args:
            max_posts: 最大取得ポスト数

        Returns:
            List[str]: ポストURLリスト
        """
        try:
            self.logger.info(f"ポストURL収集開始 (目標: {max_posts}個)")
            return await self.scroll_and_collect_urls(max_posts)

        except Exception as e:
            self.logger.error("ポストURL収集中にエラーが発生しました", exception=e)
            return []

    async def scroll_and_collect_urls(self, target_count: int) -> List[str]:
        """
        スクロールしながらURLを収集

        Args:
            target_count: 目標収集数

        Returns:
            List[str]: 収集されたURLリスト
        """
        collected_urls: Set[str] = set()
        scroll_attempts = 0
        max_scrolls = 15
        no_new_urls_count = 0

        while len(collected_urls) < target_count and scroll_attempts < max_scrolls:
            # 現在のURL収集
            previous_count = len(collected_urls)
            current_urls = await self.extract_current_urls()
            collected_urls.update(current_urls)

            new_urls_found = len(collected_urls) - previous_count
            self.logger.info(f"スクロール {scroll_attempts + 1}: {new_urls_found}個の新しいURL発見 (合計: {len(collected_urls)}個)")

            # 新しいURLが見つからない場合のカウント
            if new_urls_found == 0:
                no_new_urls_count += 1
                if no_new_urls_count >= 3:
                    self.logger.info("新しいURLが見つからないため、収集を終了します")
                    break
            else:
                no_new_urls_count = 0

            # 目標数に達した場合は終了
            if len(collected_urls) >= target_count:
                break

            # スクロール実行
            await self.scroll_to_load_more()
            scroll_attempts += 1

        result_urls = list(collected_urls)[:target_count]
        self.logger.info(f"URL収集完了: {len(result_urls)}個のURLを収集しました")
        return result_urls

    async def extract_current_urls(self) -> List[str]:
        """
        現在表示されているポストURLを抽出

        Returns:
            List[str]: ポストURLリスト
        """
        try:
            urls = []

            # 複数のセレクタでリンクを検索
            for selector in self.timeline_selectors['post_links']:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href and self._is_valid_post_url(href):
                            # 相対URLを絶対URLに変換
                            if href.startswith('/'):
                                href = f"https://x.com{href}"
                            urls.append(href)
                except:
                    continue

            # 重複除去
            unique_urls = list(set(urls))
            return unique_urls

        except Exception as e:
            self.logger.error("現在のURL抽出中にエラーが発生しました", exception=e)
            return []

    def _is_valid_post_url(self, url: str) -> bool:
        """
        有効なポストURLかどうかを判定

        Args:
            url: 判定するURL

        Returns:
            bool: 有効なポストURLかどうか
        """
        if not url:
            return False

        # ポストURLのパターン
        post_pattern = r'https://x\.com/[^/]+/status/\d+'
        relative_pattern = r'/[^/]+/status/\d+'

        return bool(re.match(post_pattern, url) or re.match(relative_pattern, url))

    async def scroll_to_load_more(self) -> bool:
        """
        追加コンテンツを読み込むためのスクロール

        Returns:
            bool: スクロール成功/失敗
        """
        try:
            # 現在のスクロール位置を取得
            previous_height = await self.page.evaluate("document.body.scrollHeight")

            # ページ下部にスクロール
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # 読み込み待機
            await asyncio.sleep(3)

            # 新しいコンテンツが読み込まれたかチェック
            new_height = await self.page.evaluate("document.body.scrollHeight")

            if new_height > previous_height:
                self.logger.debug(f"スクロール成功: {previous_height} -> {new_height}")
                return True
            else:
                self.logger.debug("新しいコンテンツが読み込まれませんでした")
                return False

        except Exception as e:
            self.logger.error("スクロール中にエラーが発生しました", exception=e)
            return False

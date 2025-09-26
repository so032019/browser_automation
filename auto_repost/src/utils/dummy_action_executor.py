"""
ダミー行動実行器
人間らしい行動をシミュレートしてBAN対策を行う
"""

import asyncio
import random
from enum import Enum
from typing import Optional
from playwright.async_api import Page
from src.utils.logger import Logger


class DummyActionType(Enum):
    """ダミー行動の種類"""
    HOME_BROWSING = "home_browsing"
    POST_READING = "post_reading"
    REPLY_CHECKING = "reply_checking"
    PRE_ACTION_WAIT = "pre_action_wait"
    POST_ACTION_WAIT = "post_action_wait"


class DummyActionResult:
    """ダミー行動実行結果"""
    def __init__(self, action_type: DummyActionType, executed: bool,
                 duration: float, success: bool, error_message: Optional[str] = None):
        self.action_type = action_type
        self.executed = executed
        self.duration = duration
        self.success = success
        self.error_message = error_message


class DummyActionExecutor:
    """ダミー行動実行器"""

    def __init__(self, page: Page):
        """
        初期化

        Args:
            page: Playwrightページインスタンス
        """
        self.page = page
        self.logger = Logger()

    async def execute_home_browsing(self) -> DummyActionResult:
        """
        ホームタイムライン閲覧ダミー行動

        Returns:
            DummyActionResult: 実行結果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info("ホーム閲覧ダミー行動を開始")

            # ホームページにアクセス
            await self.page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # ランダムスクロール（2-4回）
            scroll_count = random.randint(2, 4)
            for i in range(scroll_count):
                scroll_distance = random.randint(300, 800)
                await self.page.mouse.wheel(0, scroll_distance)
                await asyncio.sleep(random.uniform(0.8, 1.5))

            # 1-2個のポストを軽く確認
            post_check_count = random.randint(1, 2)
            try:
                # ポスト要素を探す
                posts = await self.page.query_selector_all('[data-testid="tweet"]')
                if posts and len(posts) >= post_check_count:
                    for i in range(min(post_check_count, len(posts))):
                        post = posts[i]
                        # ポストにスクロール
                        await post.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                self.logger.warning(f"ポスト確認中にエラー: {e}")

            duration = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"ホーム閲覧ダミー行動完了 ({duration:.2f}秒)")

            return DummyActionResult(DummyActionType.HOME_BROWSING, True, duration, True)

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"ホーム閲覧ダミー行動エラー: {e}")
            return DummyActionResult(DummyActionType.HOME_BROWSING, True, duration, False, str(e))

    async def execute_post_reading(self) -> DummyActionResult:
        """
        ポスト内容読み込みダミー行動

        Returns:
            DummyActionResult: 実行結果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info("ポスト読み込みダミー行動を開始")

            # 読み込み時間（2-5秒）
            reading_duration = random.uniform(2.0, 5.0)

            # 自然なスクロール動作
            scroll_count = random.randint(1, 3)
            for i in range(scroll_count):
                scroll_distance = random.randint(100, 300)
                direction = random.choice([1, -1])
                await self.page.mouse.wheel(0, direction * scroll_distance)
                await asyncio.sleep(random.uniform(0.5, 1.0))

            # 画像確認（画像がある場合）
            try:
                images = await self.page.query_selector_all('img[src*="pbs.twimg.com"]')
                if images:
                    # ランダムに1つの画像を確認
                    image = random.choice(images)
                    await image.scroll_into_view_if_needed()
                    await asyncio.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                self.logger.debug(f"画像確認中にエラー: {e}")

            # 残り時間を待機
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = max(0, reading_duration - elapsed)
            if remaining > 0:
                await asyncio.sleep(remaining)

            duration = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"ポスト読み込みダミー行動完了 ({duration:.2f}秒)")

            return DummyActionResult(DummyActionType.POST_READING, True, duration, True)

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"ポスト読み込みダミー行動エラー: {e}")
            return DummyActionResult(DummyActionType.POST_READING, True, duration, False, str(e))

    async def execute_reply_checking(self) -> DummyActionResult:
        """
        返信確認ダミー行動

        Returns:
            DummyActionResult: 実行結果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info("返信確認ダミー行動を開始")

            # 返信セクションにスクロール
            try:
                # 返信セクションを探す
                reply_selectors = [
                    '[data-testid="reply"]',
                    '[role="article"]',
                    '[data-testid="tweet"]'
                ]

                replies_found = False
                for selector in reply_selectors:
                    replies = await self.page.query_selector_all(selector)
                    if len(replies) > 1:  # 元ポスト以外の返信がある
                        # 1-2個の返信を確認
                        check_count = min(random.randint(1, 2), len(replies) - 1)
                        for i in range(1, check_count + 1):  # 0番目は元ポストなのでスキップ
                            if i < len(replies):
                                reply = replies[i]
                                await reply.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(1.0, 2.0))
                        replies_found = True
                        break

                if not replies_found:
                    # 返信がない場合は軽くスクロール
                    await self.page.mouse.wheel(0, random.randint(200, 400))
                    await asyncio.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                self.logger.debug(f"返信確認中にエラー: {e}")
                # エラーの場合も軽くスクロール
                await self.page.mouse.wheel(0, random.randint(200, 400))
                await asyncio.sleep(random.uniform(1.0, 2.0))

            duration = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"返信確認ダミー行動完了 ({duration:.2f}秒)")

            return DummyActionResult(DummyActionType.REPLY_CHECKING, True, duration, True)

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"返信確認ダミー行動エラー: {e}")
            return DummyActionResult(DummyActionType.REPLY_CHECKING, True, duration, False, str(e))

    async def execute_pre_action_wait(self) -> DummyActionResult:
        """
        アクション前待機ダミー行動

        Returns:
            DummyActionResult: 実行結果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info("アクション前待機ダミー行動を開始")

            # 1-3秒の自然な待機
            wait_duration = random.uniform(1.0, 3.0)
            await asyncio.sleep(wait_duration)

            duration = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"アクション前待機ダミー行動完了 ({duration:.2f}秒)")

            return DummyActionResult(DummyActionType.PRE_ACTION_WAIT, True, duration, True)

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"アクション前待機ダミー行動エラー: {e}")
            return DummyActionResult(DummyActionType.PRE_ACTION_WAIT, True, duration, False, str(e))

    async def execute_post_action_wait(self) -> DummyActionResult:
        """
        アクション後待機ダミー行動

        Returns:
            DummyActionResult: 実行結果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info("アクション後待機ダミー行動を開始")

            # 1-2秒の結果確認待機
            wait_duration = random.uniform(1.0, 2.0)
            await asyncio.sleep(wait_duration)

            duration = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"アクション後待機ダミー行動完了 ({duration:.2f}秒)")

            return DummyActionResult(DummyActionType.POST_ACTION_WAIT, True, duration, True)

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"アクション後待機ダミー行動エラー: {e}")
            return DummyActionResult(DummyActionType.POST_ACTION_WAIT, True, duration, False, str(e))

    async def safe_execute_dummy_action(self, action_type: DummyActionType) -> DummyActionResult:
        """
        安全なダミー行動実行（エラーハンドリング付き）

        Args:
            action_type: 実行するダミー行動の種類

        Returns:
            DummyActionResult: 実行結果
        """
        try:
            if action_type == DummyActionType.HOME_BROWSING:
                return await self.execute_home_browsing()
            elif action_type == DummyActionType.POST_READING:
                return await self.execute_post_reading()
            elif action_type == DummyActionType.REPLY_CHECKING:
                return await self.execute_reply_checking()
            elif action_type == DummyActionType.PRE_ACTION_WAIT:
                return await self.execute_pre_action_wait()
            elif action_type == DummyActionType.POST_ACTION_WAIT:
                return await self.execute_post_action_wait()
            else:
                raise ValueError(f"未知のダミー行動タイプ: {action_type}")

        except asyncio.TimeoutError:
            self.logger.warning(f"ダミー行動タイムアウト: {action_type.value}")
            return DummyActionResult(action_type, False, 0.0, False, "Timeout")
        except Exception as e:
            self.logger.error(f"ダミー行動エラー: {action_type.value}", exception=e)
            return DummyActionResult(action_type, False, 0.0, False, str(e))

"""
アクション処理クラス
個別ポストでのフォロー、リポスト、いいね処理
"""

import asyncio
import random
import math
from typing import Tuple, Dict, List
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

        # 人間らしい動作のための設定
        self.human_behavior = {
            'mouse_speed_min': 100,  # マウス移動速度（ミリ秒）
            'mouse_speed_max': 300,
            'click_delay_min': 50,   # クリック前の遅延
            'click_delay_max': 200,
            'scroll_delay_min': 800, # スクロール間隔
            'scroll_delay_max': 2000,
            'reading_time_min': 2000, # 読み込み時間
            'reading_time_max': 5000,
            'hesitation_chance': 0.15, # 迷う確率
            'double_check_chance': 0.1, # 再確認する確率
        }

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
                        # 既にフォロー済みかチェック
                        is_following = await self._is_already_following(element)
                        if is_following:
                            self.logger.info("既にフォロー済みです")
                            return True

                        # 人間らしいフォローボタンクリック
                        await self.human_like_click(element)
                        self.logger.info(f"フォローボタンをクリックしました: {selector}")
                        await self.random_delay(2, 4, "interaction")

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
                    # 既にフォロー済みかチェック
                    is_following = await self._is_already_following(follow_button)
                    if is_following:
                        self.logger.info("既にフォロー済みです (テキストベース)")
                        return True

                    await self.human_like_click(follow_button)
                    self.logger.info("フォローボタンをクリックしました (テキストベース)")
                    await self.random_delay(2, 4, "interaction")
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
                        # 既にリポスト済みかチェック
                        is_reposted = await self._is_already_reposted(element)
                        if is_reposted:
                            self.logger.info("既にリポスト済みです")
                            return True

                        # 人間らしいリポストボタンクリック
                        await self.human_like_click(element)
                        self.logger.info(f"リポストボタンをクリックしました: {selector}")
                        await self.random_delay(1, 3, "interaction")

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
                    # 既にリポスト済みかチェック
                    is_reposted = await self._is_already_reposted(repost_button)
                    if is_reposted:
                        self.logger.info("既にリポスト済みです (テキストベース)")
                        return True

                    await self.human_like_click(repost_button)
                    self.logger.info("リポストボタンをクリックしました (テキストベース)")
                    await self.random_delay(1, 3, "interaction")

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
                        await self.human_like_click(element)
                        self.logger.info(f"リポスト確認ボタンをクリックしました: {selector}")
                        await self.random_delay(1, 2, "interaction")
                        return True
                except PlaywrightTimeoutError:
                    continue

            # フォールバック: テキストベースの確認
            confirmation_texts = ['リポスト', 'Repost', '再投稿']
            for text in confirmation_texts:
                try:
                    confirm_button = await self.page.wait_for_selector(f"button:has-text('{text}')", timeout=3000)
                    if confirm_button:
                        await self.human_like_click(confirm_button)
                        self.logger.info(f"リポスト確認ボタンをクリックしました (テキスト: {text})")
                        await self.random_delay(1, 2, "interaction")
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

                        # 人間らしいいいねボタンクリック
                        await self.human_like_click(element)
                        self.logger.info(f"いいねボタンをクリックしました: {selector}")
                        await self.random_delay(0.5, 2, "interaction")
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
                    await self.human_like_click(like_button)
                    self.logger.info("いいねボタンをクリックしました (テキストベース)")
                    await self.random_delay(0.5, 2, "interaction")
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
        既にいいね済みかチェック（data-testidベースの判定）

        Args:
            element: いいねボタン要素

        Returns:
            bool: いいね済みかどうか
        """
        try:
            # data-testidで判定（最も確実）
            test_id = await element.get_attribute('data-testid')
            if test_id == 'unlike':
                self.logger.debug("data-testid='unlike' - 既にいいね済み")
                return True
            elif test_id == 'like':
                self.logger.debug("data-testid='like' - 未いいね")
                return False

            # aria-labelでの判定（フォールバック）
            aria_label = await element.get_attribute('aria-label')
            if aria_label:
                if 'いいねしました' in aria_label or 'いいねを取り消す' in aria_label:
                    self.logger.debug(f"aria-label判定 - 既にいいね済み: {aria_label}")
                    return True
                elif 'いいねする' in aria_label:
                    self.logger.debug(f"aria-label判定 - 未いいね: {aria_label}")
                    return False

            # その他の属性での判定
            aria_pressed = await element.get_attribute('aria-pressed')
            if aria_pressed == 'true':
                self.logger.debug("aria-pressed='true' - 既にいいね済み")
                return True

            # デフォルトは未いいね
            return False

        except Exception as e:
            self.logger.error("いいね状態の確認中にエラーが発生しました", exception=e)
            return False

    async def _is_already_reposted(self, element) -> bool:
        """
        既にリポスト済みかチェック（data-testidベースの判定）

        Args:
            element: リポストボタン要素

        Returns:
            bool: リポスト済みかどうか
        """
        try:
            # data-testidで判定（最も確実）
            test_id = await element.get_attribute('data-testid')
            if test_id == 'unretweet':
                self.logger.debug("data-testid='unretweet' - 既にリポスト済み")
                return True
            elif test_id == 'retweet':
                self.logger.debug("data-testid='retweet' - 未リポスト")
                return False

            # aria-labelでの判定（フォールバック）
            aria_label = await element.get_attribute('aria-label')
            if aria_label:
                if 'リポストしました' in aria_label or 'リポストを取り消す' in aria_label or 'Retweeted' in aria_label:
                    self.logger.debug(f"aria-label判定 - 既にリポスト済み: {aria_label}")
                    return True
                elif 'リポスト' in aria_label and 'リポストしました' not in aria_label:
                    self.logger.debug(f"aria-label判定 - 未リポスト: {aria_label}")
                    return False

            # ボタンテキストでの判定（フォールバック）
            button_text = await element.text_content()
            if button_text:
                if 'リポスト済み' in button_text or 'Retweeted' in button_text:
                    self.logger.debug(f"テキスト判定 - 既にリポスト済み: {button_text}")
                    return True

            # デフォルトは未リポスト
            return False

        except Exception as e:
            self.logger.error("リポスト状態の確認中にエラーが発生しました", exception=e)
            return False

    async def _is_already_following(self, element) -> bool:
        """
        既にフォロー済みかチェック（テキストベースの判定）

        Args:
            element: フォローボタン要素

        Returns:
            bool: フォロー済みかどうか
        """
        try:
            # aria-labelでの判定
            aria_label = await element.get_attribute('aria-label')
            if aria_label:
                if 'フォロー中' in aria_label or 'Following' in aria_label or 'フォロー済み' in aria_label:
                    self.logger.debug(f"aria-label判定 - 既にフォロー済み: {aria_label}")
                    return True
                elif 'フォローする' in aria_label or 'Follow' in aria_label:
                    self.logger.debug(f"aria-label判定 - 未フォロー: {aria_label}")
                    return False

            # ボタンテキストでの判定
            button_text = await element.text_content()
            if button_text:
                button_text = button_text.strip()
                if button_text in ['フォロー中', 'Following', 'フォロー済み']:
                    self.logger.debug(f"テキスト判定 - 既にフォロー済み: {button_text}")
                    return True
                elif button_text in ['フォロー', 'Follow']:
                    self.logger.debug(f"テキスト判定 - 未フォロー: {button_text}")
                    return False

            # data-testidでの判定（フォールバック）
            test_id = await element.get_attribute('data-testid')
            if test_id:
                # フォロー中の場合は異なるtest-idになることがある
                if 'unfollow' in test_id.lower():
                    self.logger.debug(f"data-testid判定 - 既にフォロー済み: {test_id}")
                    return True
                elif 'follow' in test_id.lower():
                    self.logger.debug(f"data-testid判定 - 未フォロー: {test_id}")
                    return False

            # デフォルトは未フォロー
            return False

        except Exception as e:
            self.logger.error("フォロー状態の確認中にエラーが発生しました", exception=e)
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

    async def human_like_mouse_move(self, element, duration: int = None):
        """
        人間らしいマウス移動

        Args:
            element: 移動先の要素
            duration: 移動時間（ミリ秒）
        """
        try:
            if duration is None:
                duration = random.randint(
                    self.human_behavior['mouse_speed_min'],
                    self.human_behavior['mouse_speed_max']
                )

            # 要素の位置を取得
            box = await element.bounding_box()
            if not box:
                return

            # 要素の中心座標を計算（少しランダムにずらす）
            target_x = box['x'] + box['width'] / 2 + random.randint(-10, 10)
            target_y = box['y'] + box['height'] / 2 + random.randint(-5, 5)

            # 現在のマウス位置から曲線的に移動
            await self._move_mouse_naturally(target_x, target_y, duration)

        except Exception as e:
            self.logger.error("人間らしいマウス移動中にエラー", exception=e)

    async def _move_mouse_naturally(self, target_x: float, target_y: float, duration: int):
        """
        自然なマウス移動（ベジェ曲線風）

        Args:
            target_x: 目標X座標
            target_y: 目標Y座標
            duration: 移動時間（ミリ秒）
        """
        try:
            # 複数のポイントを経由して移動
            steps = max(3, duration // 50)  # 50msごとに1ステップ

            for i in range(steps):
                progress = i / (steps - 1)

                # イージング関数（人間らしい加速・減速）
                eased_progress = self._ease_in_out_cubic(progress)

                # 少しランダムな揺れを追加
                noise_x = random.uniform(-2, 2) * (1 - progress)
                noise_y = random.uniform(-2, 2) * (1 - progress)

                current_x = target_x * eased_progress + noise_x
                current_y = target_y * eased_progress + noise_y

                await self.page.mouse.move(current_x, current_y)
                await asyncio.sleep(duration / steps / 1000)

        except Exception as e:
            self.logger.error("自然なマウス移動中にエラー", exception=e)

    def _ease_in_out_cubic(self, t: float) -> float:
        """
        イージング関数（3次関数）

        Args:
            t: 進行度（0-1）

        Returns:
            float: イージング適用後の値
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    async def human_like_click(self, element, button: str = 'left'):
        """
        人間らしいクリック動作

        Args:
            element: クリック対象の要素
            button: クリックボタン
        """
        try:
            # マウスを要素に移動
            await self.human_like_mouse_move(element)

            # クリック前の短い遅延（人間は少し考える）
            pre_click_delay = random.randint(
                self.human_behavior['click_delay_min'],
                self.human_behavior['click_delay_max']
            )
            await asyncio.sleep(pre_click_delay / 1000)

            # 迷いの動作（確率的に発生）
            if random.random() < self.human_behavior['hesitation_chance']:
                await self._simulate_hesitation(element)

            # 実際のクリック
            await element.click(button=button)

            # クリック後の短い遅延
            post_click_delay = random.randint(50, 150)
            await asyncio.sleep(post_click_delay / 1000)

            self.logger.debug(f"人間らしいクリックを実行しました")

        except Exception as e:
            self.logger.error("人間らしいクリック中にエラー", exception=e)
            # フォールバック: 通常のクリック
            await element.click()

    async def _simulate_hesitation(self, element):
        """
        迷いの動作をシミュレート

        Args:
            element: 対象要素
        """
        try:
            # 要素の近くで少しマウスを動かす
            box = await element.bounding_box()
            if box:
                for _ in range(random.randint(1, 3)):
                    offset_x = random.randint(-20, 20)
                    offset_y = random.randint(-10, 10)

                    await self.page.mouse.move(
                        box['x'] + box['width'] / 2 + offset_x,
                        box['y'] + box['height'] / 2 + offset_y
                    )
                    await asyncio.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            self.logger.error("迷い動作シミュレート中にエラー", exception=e)

    async def human_like_scroll(self, direction: str = 'down', distance: int = None):
        """
        人間らしいスクロール動作

        Args:
            direction: スクロール方向（'up' or 'down'）
            distance: スクロール距離（ピクセル）
        """
        try:
            if distance is None:
                distance = random.randint(300, 800)

            # スクロールを複数回に分けて実行
            scroll_steps = random.randint(2, 5)
            step_distance = distance // scroll_steps

            for i in range(scroll_steps):
                # 各ステップでランダムな距離
                current_distance = step_distance + random.randint(-50, 50)

                if direction == 'down':
                    await self.page.mouse.wheel(0, current_distance)
                else:
                    await self.page.mouse.wheel(0, -current_distance)

                # ステップ間の遅延
                step_delay = random.randint(100, 400)
                await asyncio.sleep(step_delay / 1000)

            # スクロール後の読み込み待機
            reading_delay = random.randint(
                self.human_behavior['reading_time_min'],
                self.human_behavior['reading_time_max']
            )
            await asyncio.sleep(reading_delay / 1000)

            self.logger.debug(f"人間らしいスクロールを実行: {direction}, {distance}px")

        except Exception as e:
            self.logger.error("人間らしいスクロール中にエラー", exception=e)

    async def random_delay(self, min_delay: int = 2, max_delay: int = 5, action_type: str = "general"):
        """
        動的ランダム遅延（アクションタイプに応じて調整）

        Args:
            min_delay: 最小遅延時間（秒）
            max_delay: 最大遅延時間（秒）
            action_type: アクションタイプ（general, navigation, interaction, reading）
        """
        # アクションタイプに応じた遅延調整
        multipliers = {
            'navigation': 1.5,    # ページ移動は長め
            'interaction': 1.2,   # インタラクションは少し長め
            'reading': 2.0,       # 読み込みは長め
            'general': 1.0        # 通常
        }

        multiplier = multipliers.get(action_type, 1.0)
        adjusted_min = min_delay * multiplier
        adjusted_max = max_delay * multiplier

        # ガンマ分布を使用してより自然な遅延を生成
        # 人間の反応時間は正規分布ではなくガンマ分布に近い
        shape = 2.0  # 形状パラメータ
        scale = (adjusted_max - adjusted_min) / 4  # スケールパラメータ

        gamma_delay = random.gammavariate(shape, scale)
        delay = max(adjusted_min, min(adjusted_max, adjusted_min + gamma_delay))

        # 稀に長い遅延（人間が他のことをしている状況）
        if random.random() < 0.05:  # 5%の確率
            delay *= random.uniform(2.0, 4.0)
            self.logger.debug(f"長時間遅延を適用: {delay:.2f}秒")

        self.logger.debug(f"動的遅延 ({action_type}): {delay:.2f}秒")
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

            # ページ読み込み後の自然な遅延
            await self.random_delay(2, 5, "reading")

            # 事前に全ての状態をチェック
            pre_check_results = await self._check_all_action_status()
            self.logger.info("=" * 40)
            self.logger.info("📋 事前状態チェック結果")
            self.logger.info(f"  👤 フォロー済み: {pre_check_results['already_following']}")
            self.logger.info(f"  🔄 リポスト済み: {pre_check_results['already_reposted']}")
            self.logger.info(f"  ❤️  いいね済み: {pre_check_results['already_liked']}")
            self.logger.info("=" * 40)

            # 全て処理済みの場合はスキップ
            if (pre_check_results['already_following'] and
                pre_check_results['already_reposted'] and
                pre_check_results['already_liked']):
                self.logger.info("✅ 全てのアクションが既に実行済みです。このポストをスキップします。")
                results['follow'] = True
                results['repost'] = True
                results['like'] = True
                return results

            # 実行予定のアクションをログ出力
            pending_actions = []
            if not pre_check_results['already_following']:
                pending_actions.append("👤フォロー")
            if not pre_check_results['already_reposted']:
                pending_actions.append("🔄リポスト")
            if not pre_check_results['already_liked']:
                pending_actions.append("❤️いいね")

            if pending_actions:
                self.logger.info(f"🎯 実行予定のアクション: {', '.join(pending_actions)}")
            else:
                self.logger.info("ℹ️  実行するアクションはありません")

            # 人間らしい順序でアクション実行（時々順序を変える）
            actions = []
            if not pre_check_results['already_following']:
                actions.append('follow')
            if not pre_check_results['already_reposted']:
                actions.append('repost')
            if not pre_check_results['already_liked']:
                actions.append('like')

            if random.random() < 0.3:  # 30%の確率で順序を変更
                random.shuffle(actions)
                self.logger.debug(f"アクション順序を変更: {actions}")

            # 既に処理済みのアクションは成功として記録
            if pre_check_results['already_following']:
                results['follow'] = True
            if pre_check_results['already_reposted']:
                results['repost'] = True
            if pre_check_results['already_liked']:
                results['like'] = True

            for action in actions:
                if action == 'follow':
                    results['follow'] = await self.follow_user()
                    await self.random_delay(3, 8, "interaction")
                elif action == 'repost':
                    results['repost'] = await self.repost_content()
                    await self.random_delay(2, 6, "interaction")
                elif action == 'like':
                    results['like'] = await self.like_post()
                    await self.random_delay(1, 4, "interaction")

                # 再確認動作（稀に発生）
                if random.random() < self.human_behavior['double_check_chance']:
                    await self._simulate_double_check()
                    await self.random_delay(1, 3, "reading")

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

    async def _simulate_double_check(self):
        """
        再確認動作をシミュレート（人間が結果を確認する動作）
        """
        try:
            self.logger.debug("再確認動作を実行中...")

            # 少しスクロールして結果を確認
            await self.human_like_scroll('up', distance=100)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.human_like_scroll('down', distance=100)

        except Exception as e:
            self.logger.error("再確認動作中にエラー", exception=e)

    async def _check_all_action_status(self) -> Dict[str, bool]:
        """
        全てのアクションの事前状態をチェック

        Returns:
            Dict[str, bool]: 各アクションの実行済み状態
        """
        status = {
            'already_following': False,
            'already_reposted': False,
            'already_liked': False
        }

        try:
            # フォロー状態をチェック（フォロー中ボタンの存在確認）
            unfollow_selectors = self.post_action_selectors.get('unfollow_button', [])
            for selector in unfollow_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        status['already_following'] = True
                        self.logger.debug(f"フォロー済み状態を検出: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            # フォロー状態をチェック（通常のフォローボタンでの判定）
            if not status['already_following']:
                for selector in self.post_action_selectors['follow_button']:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            status['already_following'] = await self._is_already_following(element)
                            break
                    except PlaywrightTimeoutError:
                        continue

            # リポスト状態をチェック（リポスト取り消しボタンの存在確認）
            unretweet_selectors = self.post_action_selectors.get('unretweet_button', [])
            for selector in unretweet_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        status['already_reposted'] = True
                        self.logger.debug(f"リポスト済み状態を検出: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            # リポスト状態をチェック（通常のリポストボタンでの判定）
            if not status['already_reposted']:
                for selector in self.post_action_selectors['repost_button']:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            status['already_reposted'] = await self._is_already_reposted(element)
                            break
                    except PlaywrightTimeoutError:
                        continue

            # いいね状態をチェック（いいね取り消しボタンの存在確認）
            unlike_selectors = self.post_action_selectors.get('unlike_button', [])
            for selector in unlike_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        status['already_liked'] = True
                        self.logger.debug(f"いいね済み状態を検出: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            # いいね状態をチェック（通常のいいねボタンでの判定）
            if not status['already_liked']:
                for selector in self.post_action_selectors['like_button']:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            status['already_liked'] = await self._is_already_liked(element)
                            break
                    except PlaywrightTimeoutError:
                        continue

        except Exception as e:
            self.logger.error("事前状態チェック中にエラーが発生しました", exception=e)

        return status

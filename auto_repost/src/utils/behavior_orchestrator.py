"""
行動統制器
ダミー行動の実行タイミング決定とフロー制御を行う
"""

import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import Page
from src.utils.dummy_action_executor import DummyActionExecutor, DummyActionType, DummyActionResult
from src.utils.enhanced_delay_manager import EnhancedDelayManager
from src.utils.logger import Logger


class ActionExecutionRecord:
    """アクション実行記録"""
    def __init__(self, timestamp: datetime, post_url: str,
                 dummy_actions_executed: List[DummyActionType],
                 total_duration: float, action_results: Dict[str, bool]):
        self.timestamp = timestamp
        self.post_url = post_url
        self.dummy_actions_executed = dummy_actions_executed
        self.total_duration = total_duration
        self.action_results = action_results


class BehaviorOrchestrator:
    """行動統制器"""

    def __init__(self, page: Page):
        """
        初期化

        Args:
            page: Playwrightページインスタンス
        """
        self.page = page
        self.dummy_executor = DummyActionExecutor(page)
        self.delay_manager = EnhancedDelayManager()
        self.logger = Logger()

        # 実行状態管理
        self.post_count = 0
        self.execution_records: List[ActionExecutionRecord] = []
        self.session_start_time = datetime.now()

    async def execute_enhanced_post_action(self, url: str,
                                         action_handler_method) -> bool:
        """
        拡張されたポストアクション実行（BAN対策付き）

        Args:
            url: ポストURL
            action_handler_method: 既存のアクション実行メソッド

        Returns:
            bool: 実行成功/失敗
        """
        start_time = datetime.now()
        dummy_actions_executed = []
        action_results = {}

        try:
            self.logger.info(f"拡張ポストアクション開始: {url}")

            # 2回目以降はホーム経由でアクセス
            if self.post_count > 0:
                if await self.should_execute_dummy_action(DummyActionType.HOME_BROWSING):
                    result = await self.dummy_executor.safe_execute_dummy_action(
                        DummyActionType.HOME_BROWSING
                    )
                    if result.executed:
                        dummy_actions_executed.append(result.action_type)

                    # ホーム閲覧後の遅延
                    delay = self.delay_manager.get_page_transition_delay()
                    await asyncio.sleep(delay)

            # 目標ポストURLにアクセス
            await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)

            # ページ読み込み後の遅延
            page_delay = self.delay_manager.get_page_transition_delay()
            await asyncio.sleep(page_delay)

            # ダミー行動1: ポスト内容読み込み
            if await self.should_execute_dummy_action(DummyActionType.POST_READING):
                result = await self.dummy_executor.safe_execute_dummy_action(
                    DummyActionType.POST_READING
                )
                if result.executed:
                    dummy_actions_executed.append(result.action_type)

            # ダミー行動2: 返信確認
            if await self.should_execute_dummy_action(DummyActionType.REPLY_CHECKING):
                result = await self.dummy_executor.safe_execute_dummy_action(
                    DummyActionType.REPLY_CHECKING
                )
                if result.executed:
                    dummy_actions_executed.append(result.action_type)

            # ダミー行動3: アクション前待機
            if await self.should_execute_dummy_action(DummyActionType.PRE_ACTION_WAIT):
                result = await self.dummy_executor.safe_execute_dummy_action(
                    DummyActionType.PRE_ACTION_WAIT
                )
                if result.executed:
                    dummy_actions_executed.append(result.action_type)

            # メインアクション実行
            main_action_success = await action_handler_method(url)
            action_results['main_action'] = main_action_success

            # ダミー行動4: アクション後待機
            if await self.should_execute_dummy_action(DummyActionType.POST_ACTION_WAIT):
                result = await self.dummy_executor.safe_execute_dummy_action(
                    DummyActionType.POST_ACTION_WAIT
                )
                if result.executed:
                    dummy_actions_executed.append(result.action_type)

            # 実行記録を保存
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            record = ActionExecutionRecord(
                timestamp=start_time,
                post_url=url,
                dummy_actions_executed=dummy_actions_executed,
                total_duration=total_duration,
                action_results=action_results
            )
            self.execution_records.append(record)

            self.post_count += 1

            self.logger.info(f"拡張ポストアクション完了: {url} "
                           f"(時間: {total_duration:.2f}秒, "
                           f"ダミー行動: {len(dummy_actions_executed)}個)")

            return main_action_success

        except Exception as e:
            self.logger.error(f"拡張ポストアクション実行エラー: {e}", exception=e)
            return False

    async def should_execute_dummy_action(self, action_type: DummyActionType) -> bool:
        """
        ダミー行動を実行すべきかを判定

        Args:
            action_type: ダミー行動の種類

        Returns:
            bool: 実行すべきかどうか
        """
        try:
            # 基本実行確率
            base_probabilities = {
                DummyActionType.HOME_BROWSING: 0.9,  # ホーム閲覧は高確率
                DummyActionType.POST_READING: 0.95,  # ポスト読み込みはほぼ必須
                DummyActionType.REPLY_CHECKING: 0.7, # 返信確認は中確率
                DummyActionType.PRE_ACTION_WAIT: 0.8, # アクション前待機は高確率
                DummyActionType.POST_ACTION_WAIT: 0.9 # アクション後待機は高確率
            }

            base_prob = base_probabilities.get(action_type, 0.5)

            # 連続実行による調整
            if self.post_count > 5:
                # 多くのポストを処理している場合は確率を上げる
                base_prob = min(1.0, base_prob + 0.1)

            # 時間帯による調整
            current_hour = datetime.now().hour
            if 22 <= current_hour or current_hour <= 6:
                # 深夜は少し確率を下げる（人間は疲れている）
                base_prob *= 0.9

            # ランダム判定
            should_execute = random.random() < base_prob

            self.logger.debug(f"ダミー行動判定 {action_type.value}: "
                            f"{should_execute} (確率: {base_prob:.2f})")

            return should_execute

        except Exception as e:
            self.logger.error(f"ダミー行動判定エラー: {e}")
            return True  # エラー時はデフォルトで実行

    async def coordinate_action_flow(self, urls: List[str],
                                   action_handler_method) -> List[bool]:
        """
        複数ポストのアクションフローを統制

        Args:
            urls: ポストURLのリスト
            action_handler_method: アクション実行メソッド

        Returns:
            List[bool]: 各ポストの実行結果
        """
        results = []

        try:
            self.logger.info(f"アクションフロー統制開始: {len(urls)}個のポスト")

            for i, url in enumerate(urls):
                self.logger.info(f"ポスト {i+1}/{len(urls)} を処理中")

                # ポスト間の遅延
                if i > 0:
                    inter_post_delay = self.delay_manager.get_enhanced_delay(
                        base_delay=random.uniform(5.0, 15.0),
                        variation_factor=0.6
                    )
                    self.logger.info(f"ポスト間遅延: {inter_post_delay:.2f}秒")
                    await asyncio.sleep(inter_post_delay)

                # 拡張ポストアクション実行
                result = await self.execute_enhanced_post_action(url, action_handler_method)
                results.append(result)

                # 進捗ログ
                success_count = sum(results)
                self.logger.info(f"進捗: {i+1}/{len(urls)} "
                               f"(成功: {success_count}, 失敗: {i+1-success_count})")

            self.logger.info(f"アクションフロー統制完了: "
                           f"成功 {sum(results)}/{len(urls)}")

            return results

        except Exception as e:
            self.logger.error(f"アクションフロー統制エラー: {e}", exception=e)
            return results

    def get_execution_statistics(self) -> Dict:
        """
        実行統計情報を取得

        Returns:
            Dict: 統計情報
        """
        try:
            if not self.execution_records:
                return {}

            # 基本統計
            total_posts = len(self.execution_records)
            total_duration = sum(record.total_duration for record in self.execution_records)
            avg_duration = total_duration / total_posts if total_posts > 0 else 0

            # ダミー行動統計
            dummy_action_counts = {}
            for record in self.execution_records:
                for action_type in record.dummy_actions_executed:
                    dummy_action_counts[action_type.value] = \
                        dummy_action_counts.get(action_type.value, 0) + 1

            # 成功率統計
            main_action_successes = sum(
                1 for record in self.execution_records
                if record.action_results.get('main_action', False)
            )
            success_rate = main_action_successes / total_posts if total_posts > 0 else 0

            # セッション時間
            session_duration = (datetime.now() - self.session_start_time).total_seconds()

            return {
                'total_posts_processed': total_posts,
                'total_duration_seconds': total_duration,
                'average_duration_per_post': avg_duration,
                'main_action_success_rate': success_rate,
                'dummy_action_counts': dummy_action_counts,
                'session_duration_seconds': session_duration,
                'posts_per_minute': (total_posts / (session_duration / 60)) if session_duration > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {}

    def reset_session(self):
        """
        セッション情報をリセット
        """
        try:
            self.post_count = 0
            self.execution_records.clear()
            self.session_start_time = datetime.now()
            self.delay_manager.reset_session()
            self.logger.info("行動統制セッションをリセット")

        except Exception as e:
            self.logger.error(f"セッションリセットエラー: {e}")

    def get_behavior_diversity_score(self) -> float:
        """
        行動多様性スコアを計算

        Returns:
            float: 多様性スコア（0.0-1.0）
        """
        try:
            if len(self.execution_records) < 2:
                return 0.0

            # 実行時間の多様性
            durations = [record.total_duration for record in self.execution_records]
            duration_variance = self._calculate_variance(durations)

            # ダミー行動パターンの多様性
            dummy_patterns = [
                len(record.dummy_actions_executed)
                for record in self.execution_records
            ]
            pattern_variance = self._calculate_variance(dummy_patterns)

            # 正規化して0-1の範囲にする
            diversity_score = min(1.0, (duration_variance + pattern_variance) / 2.0)

            return diversity_score

        except Exception as e:
            self.logger.error(f"多様性スコア計算エラー: {e}")
            return 0.0

    def _calculate_variance(self, values: List[float]) -> float:
        """
        分散を計算

        Args:
            values: 値のリスト

        Returns:
            float: 分散値
        """
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)

        # 正規化（平均値で割る）
        normalized_variance = variance / mean if mean > 0 else 0.0

        return min(1.0, normalized_variance)

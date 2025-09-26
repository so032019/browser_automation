"""
拡張遅延管理器
既存の遅延機能を拡張してより人間らしいタイミング制御を提供
"""

import random
import time
from typing import Optional
from src.utils.logger import Logger


class EnhancedDelayManager:
    """拡張遅延管理器"""

    def __init__(self):
        """初期化"""
        self.logger = Logger()
        self.last_action_time = 0.0
        self.consecutive_actions = 0

    def get_enhanced_delay(self, base_delay: float, variation_factor: float = 0.5) -> float:
        """
        拡張されたランダム遅延を取得

        Args:
            base_delay: 基本遅延時間（秒）
            variation_factor: 変動係数（0.0-1.0）

        Returns:
            float: 調整された遅延時間
        """
        try:
            # 基本変動（負の値を防ぐ）
            base_delay = max(0.1, base_delay)  # 最小値を保証
            variation = base_delay * variation_factor
            min_delay = max(0.1, base_delay - variation)
            max_delay = base_delay + variation

            # ランダム遅延
            delay = random.uniform(min_delay, max_delay)

            # 連続アクション調整
            if self.consecutive_actions > 3:
                # 連続アクションが多い場合は遅延を増加
                multiplier = 1.0 + (self.consecutive_actions - 3) * 0.2
                delay *= multiplier
                self.logger.debug(f"連続アクション調整: {multiplier:.2f}倍")

            # 前回アクションからの経過時間調整
            current_time = time.time()
            if self.last_action_time > 0:
                elapsed = current_time - self.last_action_time
                if elapsed < 2.0:  # 2秒以内の場合は追加遅延
                    additional_delay = random.uniform(1.0, 3.0)
                    delay += additional_delay
                    self.logger.debug(f"短間隔調整: +{additional_delay:.2f}秒")

            self.last_action_time = current_time
            self.consecutive_actions += 1

            self.logger.debug(f"拡張遅延: {delay:.2f}秒 (基本: {base_delay:.2f}秒)")
            return delay

        except Exception as e:
            self.logger.error(f"拡張遅延計算エラー: {e}")
            return base_delay

    def get_page_transition_delay(self) -> float:
        """
        ページ遷移時の遅延を取得

        Returns:
            float: ページ遷移遅延時間（秒）
        """
        try:
            # 基本遅延（1-3秒）
            base_delay = random.uniform(1.0, 3.0)

            # 時間帯による調整
            current_hour = time.localtime().tm_hour
            if 9 <= current_hour <= 17:  # 日中は少し短め
                multiplier = random.uniform(0.8, 1.0)
            elif 22 <= current_hour or current_hour <= 6:  # 深夜は少し長め
                multiplier = random.uniform(1.2, 1.5)
            else:  # その他の時間
                multiplier = random.uniform(0.9, 1.1)

            delay = base_delay * multiplier

            self.logger.debug(f"ページ遷移遅延: {delay:.2f}秒")
            return delay

        except Exception as e:
            self.logger.error(f"ページ遷移遅延計算エラー: {e}")
            return 2.0  # デフォルト値

    def get_reading_delay(self, content_length: Optional[int] = None) -> float:
        """
        コンテンツ読み込み時の遅延を取得

        Args:
            content_length: コンテンツの長さ（文字数）

        Returns:
            float: 読み込み遅延時間（秒）
        """
        try:
            if content_length is None:
                # 長さが不明の場合は標準的な読み込み時間
                base_delay = random.uniform(2.0, 5.0)
            else:
                # 文字数に基づく読み込み時間計算
                # 1文字あたり約0.05-0.1秒の読み込み時間
                reading_speed = random.uniform(0.05, 0.1)
                base_delay = content_length * reading_speed

                # 最小・最大値の制限
                base_delay = max(1.0, min(10.0, base_delay))

            # ランダム変動を追加
            variation = base_delay * 0.3
            delay = random.uniform(base_delay - variation, base_delay + variation)

            self.logger.debug(f"読み込み遅延: {delay:.2f}秒 (文字数: {content_length})")
            return delay

        except Exception as e:
            self.logger.error(f"読み込み遅延計算エラー: {e}")
            return 3.0  # デフォルト値

    def get_action_interval_delay(self, action_type: str) -> float:
        """
        アクション間隔の遅延を取得

        Args:
            action_type: アクションの種類（follow, repost, like等）

        Returns:
            float: アクション間隔遅延時間（秒）
        """
        try:
            # アクションタイプ別の基本遅延
            base_delays = {
                'follow': random.uniform(2.0, 4.0),
                'repost': random.uniform(1.5, 3.0),
                'like': random.uniform(1.0, 2.5),
                'general': random.uniform(1.5, 3.0)
            }

            base_delay = base_delays.get(action_type, base_delays['general'])

            # 拡張遅延を適用
            delay = self.get_enhanced_delay(base_delay, 0.4)

            self.logger.debug(f"アクション間隔遅延 ({action_type}): {delay:.2f}秒")
            return delay

        except Exception as e:
            self.logger.error(f"アクション間隔遅延計算エラー: {e}")
            return 2.0  # デフォルト値

    def get_scroll_delay(self) -> float:
        """
        スクロール動作の遅延を取得

        Returns:
            float: スクロール遅延時間（秒）
        """
        try:
            # スクロール間隔（0.5-1.5秒）
            delay = random.uniform(0.5, 1.5)

            self.logger.debug(f"スクロール遅延: {delay:.2f}秒")
            return delay

        except Exception as e:
            self.logger.error(f"スクロール遅延計算エラー: {e}")
            return 1.0  # デフォルト値

    def reset_session(self):
        """
        セッション情報をリセット
        新しい実行セッション開始時に呼び出す
        """
        try:
            self.last_action_time = 0.0
            self.consecutive_actions = 0
            self.logger.info("遅延管理セッションをリセット")

        except Exception as e:
            self.logger.error(f"セッションリセットエラー: {e}")

    def get_statistics(self) -> dict:
        """
        統計情報を取得

        Returns:
            dict: 統計情報
        """
        try:
            current_time = time.time()
            elapsed_since_last = current_time - self.last_action_time if self.last_action_time > 0 else 0

            return {
                'consecutive_actions': self.consecutive_actions,
                'last_action_time': self.last_action_time,
                'elapsed_since_last_action': elapsed_since_last,
                'current_time': current_time
            }

        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {}

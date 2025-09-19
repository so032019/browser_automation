"""
人間らしい動作をシミュレートするユーティリティクラス
"""

import asyncio
import random
import math
from typing import Dict, List, Tuple
from playwright.async_api import Page
from src.utils.logger import Logger


class HumanBehaviorSimulator:
    """人間らしい動作をシミュレートするクラス"""

    def __init__(self, page: Page):
        """
        初期化

        Args:
            page: Playwrightページインスタンス
        """
        self.page = page
        self.logger = Logger()

        # 人間らしい動作パラメータ
        self.behavior_config = {
            'typing_speed_min': 80,      # タイピング速度（文字/分）
            'typing_speed_max': 200,
            'mouse_jitter_range': 3,     # マウスの微細な動き（ピクセル）
            'scroll_variation': 0.3,     # スクロール距離の変動率
            'pause_probability': 0.15,   # 一時停止の確率
            'mistake_probability': 0.05, # タイプミスの確率
            'double_click_chance': 0.02, # 誤ダブルクリックの確率
        }

    async def human_like_typing(self, text: str, element=None) -> bool:
        """
        人間らしいタイピング

        Args:
            text: 入力するテキスト
            element: 入力要素（Noneの場合は現在のフォーカス要素）

        Returns:
            bool: 成功/失敗
        """
        try:
            if element:
                await element.click()
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # 文字ごとに人間らしい間隔でタイピング
            for i, char in enumerate(text):
                # タイピング速度の計算（文字/分 → 秒/文字）
                typing_speed = random.randint(
                    self.behavior_config['typing_speed_min'],
                    self.behavior_config['typing_speed_max']
                )
                char_delay = 60.0 / typing_speed

                # 文字の種類による遅延調整
                if char in ' \n\t':
                    char_delay *= random.uniform(1.5, 2.5)  # スペースや改行は長め
                elif char in '.,!?':
                    char_delay *= random.uniform(1.2, 1.8)  # 句読点は少し長め
                elif char.isupper():
                    char_delay *= random.uniform(1.1, 1.4)  # 大文字は少し長め

                # タイプミスのシミュレーション
                if random.random() < self.behavior_config['mistake_probability']:
                    await self._simulate_typo(char)
                    char_delay *= random.uniform(2.0, 3.0)  # ミス修正で時間がかかる

                # 実際の文字入力
                await self.page.keyboard.type(char)

                # 一時停止（人間が考えている状況）
                if random.random() < self.behavior_config['pause_probability']:
                    pause_time = random.uniform(0.5, 2.0)
                    await asyncio.sleep(pause_time)

                await asyncio.sleep(char_delay)

            return True

        except Exception as e:
            self.logger.error("人間らしいタイピング中にエラー", exception=e)
            return False

    async def _simulate_typo(self, correct_char: str):
        """
        タイプミスをシミュレート

        Args:
            correct_char: 正しい文字
        """
        try:
            # 近くのキーを間違って押す
            typo_chars = self._get_nearby_keys(correct_char)
            if typo_chars:
                typo_char = random.choice(typo_chars)
                await self.page.keyboard.type(typo_char)
                await asyncio.sleep(random.uniform(0.2, 0.5))

                # バックスペースで修正
                await self.page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            self.logger.error("タイプミスシミュレート中にエラー", exception=e)

    def _get_nearby_keys(self, char: str) -> List[str]:
        """
        指定した文字の近くのキーを取得

        Args:
            char: 基準となる文字

        Returns:
            List[str]: 近くのキーのリスト
        """
        # QWERTY配列での近接キーマップ
        nearby_keys = {
            'a': ['s', 'q', 'w', 'z'],
            's': ['a', 'd', 'w', 'e', 'x', 'z'],
            'd': ['s', 'f', 'e', 'r', 'c', 'x'],
            'f': ['d', 'g', 'r', 't', 'v', 'c'],
            'g': ['f', 'h', 't', 'y', 'b', 'v'],
            'h': ['g', 'j', 'y', 'u', 'n', 'b'],
            'j': ['h', 'k', 'u', 'i', 'm', 'n'],
            'k': ['j', 'l', 'i', 'o', 'm'],
            'l': ['k', 'o', 'p'],
            'q': ['w', 'a'],
            'w': ['q', 'e', 'a', 's'],
            'e': ['w', 'r', 's', 'd'],
            'r': ['e', 't', 'd', 'f'],
            't': ['r', 'y', 'f', 'g'],
            'y': ['t', 'u', 'g', 'h'],
            'u': ['y', 'i', 'h', 'j'],
            'i': ['u', 'o', 'j', 'k'],
            'o': ['i', 'p', 'k', 'l'],
            'p': ['o', 'l'],
            'z': ['x', 'a', 's'],
            'x': ['z', 'c', 's', 'd'],
            'c': ['x', 'v', 'd', 'f'],
            'v': ['c', 'b', 'f', 'g'],
            'b': ['v', 'n', 'g', 'h'],
            'n': ['b', 'm', 'h', 'j'],
            'm': ['n', 'j', 'k'],
        }

        return nearby_keys.get(char.lower(), [])

    async def natural_mouse_movement(self, start_x: float, start_y: float,
                                   end_x: float, end_y: float, duration: float = 1.0):
        """
        自然なマウス移動（ベジェ曲線を使用）

        Args:
            start_x: 開始X座標
            start_y: 開始Y座標
            end_x: 終了X座標
            end_y: 終了Y座標
            duration: 移動時間（秒）
        """
        try:
            # ベジェ曲線の制御点を計算
            control_points = self._calculate_bezier_control_points(
                start_x, start_y, end_x, end_y
            )

            steps = max(10, int(duration * 60))  # 60fps相当

            for i in range(steps + 1):
                t = i / steps

                # ベジェ曲線上の点を計算
                x, y = self._bezier_curve(t, control_points)

                # 微細な揺れを追加
                jitter_x = random.uniform(-self.behavior_config['mouse_jitter_range'],
                                        self.behavior_config['mouse_jitter_range'])
                jitter_y = random.uniform(-self.behavior_config['mouse_jitter_range'],
                                        self.behavior_config['mouse_jitter_range'])

                await self.page.mouse.move(x + jitter_x, y + jitter_y)
                await asyncio.sleep(duration / steps)

        except Exception as e:
            self.logger.error("自然なマウス移動中にエラー", exception=e)

    def _calculate_bezier_control_points(self, start_x: float, start_y: float,
                                       end_x: float, end_y: float) -> List[Tuple[float, float]]:
        """
        ベジェ曲線の制御点を計算

        Args:
            start_x: 開始X座標
            start_y: 開始Y座標
            end_x: 終了X座標
            end_y: 終了Y座標

        Returns:
            List[Tuple[float, float]]: 制御点のリスト
        """
        # 距離を計算
        distance = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

        # 制御点の距離（全体距離の1/3程度）
        control_distance = distance / 3

        # ランダムな角度で制御点を配置
        angle1 = random.uniform(-math.pi/4, math.pi/4)
        angle2 = random.uniform(-math.pi/4, math.pi/4)

        # 制御点1
        control1_x = start_x + control_distance * math.cos(angle1)
        control1_y = start_y + control_distance * math.sin(angle1)

        # 制御点2
        control2_x = end_x - control_distance * math.cos(angle2)
        control2_y = end_y - control_distance * math.sin(angle2)

        return [
            (start_x, start_y),
            (control1_x, control1_y),
            (control2_x, control2_y),
            (end_x, end_y)
        ]

    def _bezier_curve(self, t: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        3次ベジェ曲線上の点を計算

        Args:
            t: パラメータ（0-1）
            points: 制御点のリスト

        Returns:
            Tuple[float, float]: 曲線上の点の座標
        """
        if len(points) != 4:
            raise ValueError("ベジェ曲線には4つの制御点が必要です")

        # 3次ベジェ曲線の公式
        x = (1-t)**3 * points[0][0] + 3*(1-t)**2*t * points[1][0] + \
            3*(1-t)*t**2 * points[2][0] + t**3 * points[3][0]

        y = (1-t)**3 * points[0][1] + 3*(1-t)**2*t * points[1][1] + \
            3*(1-t)*t**2 * points[2][1] + t**3 * points[3][1]

        return x, y

    async def simulate_reading_behavior(self, min_time: float = 2.0, max_time: float = 8.0):
        """
        読み込み行動をシミュレート

        Args:
            min_time: 最小読み込み時間（秒）
            max_time: 最大読み込み時間（秒）
        """
        try:
            reading_time = random.uniform(min_time, max_time)

            # 読み込み中にランダムなマウス移動
            for _ in range(random.randint(2, 5)):
                # 現在のビューポート内でランダムな位置に移動
                viewport = await self.page.viewport_size()
                if viewport:
                    random_x = random.randint(100, viewport['width'] - 100)
                    random_y = random.randint(100, viewport['height'] - 100)

                    await self.page.mouse.move(random_x, random_y)
                    await asyncio.sleep(random.uniform(0.5, 1.5))

            # 残りの時間を待機
            await asyncio.sleep(reading_time)

        except Exception as e:
            self.logger.error("読み込み行動シミュレート中にエラー", exception=e)

    async def simulate_hesitation_click(self, element):
        """
        迷いのあるクリック動作をシミュレート

        Args:
            element: クリック対象の要素
        """
        try:
            # 要素の位置を取得
            box = await element.bounding_box()
            if not box:
                return

            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2

            # 要素の近くでマウスを動かす（迷い）
            for _ in range(random.randint(1, 3)):
                offset_x = random.randint(-30, 30)
                offset_y = random.randint(-20, 20)

                await self.page.mouse.move(center_x + offset_x, center_y + offset_y)
                await asyncio.sleep(random.uniform(0.2, 0.8))

            # 最終的に要素をクリック
            await element.click()

            # 誤ダブルクリックのシミュレーション
            if random.random() < self.behavior_config['double_click_chance']:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await element.click()
                self.logger.debug("誤ダブルクリックをシミュレート")

        except Exception as e:
            self.logger.error("迷いクリックシミュレート中にエラー", exception=e)

    async def random_page_interaction(self):
        """
        ランダムなページインタラクション（人間らしい無意識の動作）
        """
        try:
            interactions = [
                self._random_scroll,
                self._random_mouse_move,
                self._random_key_press,
                self._random_pause
            ]

            # ランダムに1-3個のインタラクションを実行
            num_interactions = random.randint(1, 3)
            selected_interactions = random.sample(interactions, num_interactions)

            for interaction in selected_interactions:
                await interaction()
                await asyncio.sleep(random.uniform(0.5, 2.0))

        except Exception as e:
            self.logger.error("ランダムページインタラクション中にエラー", exception=e)

    async def _random_scroll(self):
        """ランダムスクロール"""
        direction = random.choice([1, -1])  # 上下
        distance = random.randint(50, 200)
        await self.page.mouse.wheel(0, direction * distance)

    async def _random_mouse_move(self):
        """ランダムマウス移動"""
        viewport = await self.page.viewport_size()
        if viewport:
            x = random.randint(0, viewport['width'])
            y = random.randint(0, viewport['height'])
            await self.page.mouse.move(x, y)

    async def _random_key_press(self):
        """ランダムキー押下（無害なキー）"""
        keys = ['Tab', 'Shift', 'Control']  # 無害なキー
        key = random.choice(keys)
        await self.page.keyboard.press(key)

    async def _random_pause(self):
        """ランダム一時停止"""
        pause_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(pause_time)

"""
セレクタ設定管理クラス
JSONファイルベースのセレクタ設定管理、複数のフォールバックセレクタ対応
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SelectorConfig:
    """セレクタ設定クラス"""
    login: Dict[str, str]
    search: Dict[str, str]
    post_actions: Dict[str, str]
    timeline: Dict[str, str]
    fallback: Dict[str, str]

    @classmethod
    def from_file(cls, config_path: str = "config/selectors.json") -> 'SelectorConfig':
        """
        JSONファイルからセレクタ設定を読み込み

        Args:
            config_path: 設定ファイルのパス

        Returns:
            SelectorConfig: セレクタ設定インスタンス
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"セレクタ設定ファイルが見つかりません: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        return cls(
            login=config_data.get('login', {}),
            search=config_data.get('search', {}),
            post_actions=config_data.get('post_actions', {}),
            timeline=config_data.get('timeline', {}),
            fallback=config_data.get('fallback', {})
        )

    def get_selector(self, category: str, key: str) -> Optional[str]:
        """
        指定されたカテゴリとキーのセレクタを取得

        Args:
            category: セレクタカテゴリ
            key: セレクタキー

        Returns:
            str: セレクタ文字列
        """
        category_data = getattr(self, category, {})
        return category_data.get(key)

    def get_selectors_with_fallback(self, category: str, key: str) -> List[str]:
        """
        フォールバック付きセレクタリストを取得

        Args:
            category: セレクタカテゴリ
            key: セレクタキー

        Returns:
            List[str]: セレクタリスト（メイン + フォールバック）
        """
        selectors = []

        # メインセレクタ
        main_selector = self.get_selector(category, key)
        if main_selector:
            selectors.append(main_selector)

        # フォールバックセレクタ
        fallback_key = f"{key}_alt"
        fallback_selector = self.get_selector('fallback', fallback_key)
        if fallback_selector:
            selectors.append(fallback_selector)

        return selectors


class SelectorManager:
    """セレクタ管理クラス"""

    def __init__(self, config_path: str = "config/selectors.json"):
        """
        セレクタ管理の初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config = SelectorConfig.from_file(config_path)

    def reload_config(self):
        """設定ファイルの再読み込み"""
        self.config = SelectorConfig.from_file(self.config_path)

    def get_login_selectors(self) -> Dict[str, List[str]]:
        """
        ログイン関連セレクタを取得

        Returns:
            Dict[str, List[str]]: ログインセレクタ辞書
        """
        return {
            'login_button': self.config.get_selectors_with_fallback('login', 'login_button'),
            'username_input': self.config.get_selectors_with_fallback('login', 'username_input'),
            'password_input': self.config.get_selectors_with_fallback('login', 'password_input'),
            'next_button': self.config.get_selectors_with_fallback('login', 'next_button'),
            'login_form': self.config.get_selectors_with_fallback('login', 'login_form')
        }

    def get_search_selectors(self) -> Dict[str, List[str]]:
        """
        検索関連セレクタを取得

        Returns:
            Dict[str, List[str]]: 検索セレクタ辞書
        """
        return {
            'search_input': self.config.get_selectors_with_fallback('search', 'search_input'),
            'search_button': self.config.get_selectors_with_fallback('search', 'search_button')
        }

    def get_post_action_selectors(self) -> Dict[str, List[str]]:
        """
        ポストアクション関連セレクタを取得

        Returns:
            Dict[str, List[str]]: ポストアクションセレクタ辞書
        """
        return {
            'follow_button': self.config.get_selectors_with_fallback('post_actions', 'follow_button'),
            'repost_button': self.config.get_selectors_with_fallback('post_actions', 'repost_button'),
            'repost_confirm': self.config.get_selectors_with_fallback('post_actions', 'repost_confirm'),
            'like_button': self.config.get_selectors_with_fallback('post_actions', 'like_button'),
            'unlike_button': self.config.get_selectors_with_fallback('post_actions', 'unlike_button'),
            'unretweet_button': self.config.get_selectors_with_fallback('post_actions', 'unretweet_button'),
            'unfollow_button': self.config.get_selectors_with_fallback('post_actions', 'unfollow_button')
        }

    def get_timeline_selectors(self) -> Dict[str, List[str]]:
        """
        タイムライン関連セレクタを取得

        Returns:
            Dict[str, List[str]]: タイムラインセレクタ辞書
        """
        return {
            'post_links': self.config.get_selectors_with_fallback('timeline', 'post_links'),
            'article_container': self.config.get_selectors_with_fallback('timeline', 'article_container')
        }

    def update_selector(self, category: str, key: str, selector: str):
        """
        セレクタの動的更新

        Args:
            category: セレクタカテゴリ
            key: セレクタキー
            selector: 新しいセレクタ
        """
        category_data = getattr(self.config, category, {})
        category_data[key] = selector

        # ファイルに保存
        self._save_config()

    def _save_config(self):
        """設定ファイルの保存"""
        config_data = {
            'login': self.config.login,
            'search': self.config.search,
            'post_actions': self.config.post_actions,
            'timeline': self.config.timeline,
            'fallback': self.config.fallback
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def validate_selectors(self) -> Dict[str, bool]:
        """
        セレクタの有効性チェック

        Returns:
            Dict[str, bool]: 検証結果
        """
        validation_results = {}

        # 必須セレクタの存在チェック
        required_selectors = [
            ('login', 'login_button'),
            ('login', 'username_input'),
            ('login', 'password_input'),
            ('search', 'search_input'),
            ('post_actions', 'follow_button'),
            ('post_actions', 'repost_button'),
            ('timeline', 'post_links')
        ]

        for category, key in required_selectors:
            selector = self.config.get_selector(category, key)
            validation_results[f"{category}.{key}"] = selector is not None and len(selector.strip()) > 0

        return validation_results

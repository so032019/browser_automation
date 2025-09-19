"""
Slack通知モジュール
実行結果をSlackに送信する機能を提供
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.utils.logger import Logger


class SlackNotifier:
    """Slack通知クラス"""

    def __init__(self, api_url: str, api_key: str, workspace: str = "default"):
        """
        Slack通知の初期化

        Args:
            api_url: Slack API URL
            api_key: API認証キー
            workspace: ワークスペース識別子
        """
        self.api_url = api_url
        self.api_key = api_key
        self.workspace = workspace
        self.logger = Logger()

    def send_execution_summary(self, summary_data: Dict[str, Any], is_success: bool = True) -> bool:
        """
        実行サマリーをSlackに送信

        Args:
            summary_data: 実行サマリーデータ
            is_success: 実行成功フラグ

        Returns:
            bool: 送信成功/失敗
        """
        try:
            # メッセージタイプを決定
            message_type = "success" if is_success else "error"

            # タイトルを生成
            title = "🎉 X自動化ツール実行完了" if is_success else "❌ X自動化ツール実行失敗"

            # メッセージ本文を生成
            message = self._format_summary_message(summary_data, is_success)

            # フィールド情報を生成
            fields = self._create_summary_fields(summary_data, is_success)

            return self.send_notification(
                message=message,
                title=title,
                message_type=message_type,
                fields=fields
            )

        except Exception as e:
            self.logger.error("Slack通知の送信中にエラーが発生しました", exception=e)
            return False

    def send_notification(
        self,
        message: str,
        title: Optional[str] = None,
        message_type: str = "info",
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Slackに通知を送信

        Args:
            message: メッセージ本文
            title: メッセージタイトル
            message_type: メッセージタイプ
            fields: フィールド情報

        Returns:
            bool: 送信成功/失敗
        """
        try:
            self.logger.info("Slack通知を送信中...")

            # リクエストパラメータを構築
            params = {
                'api_key': self.api_key,
                'message': message,
                'workspace': self.workspace,
                'type': message_type
            }

            if title:
                params['title'] = title

            if fields:
                params['fields'] = json.dumps(fields)

            # POSTリクエストで送信
            response = requests.post(
                self.api_url,
                data=params,
                timeout=30
            )

            # レスポンスを確認
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'ok':
                        self.logger.info("Slack通知の送信が成功しました")
                        return True
                    else:
                        self.logger.error(f"Slack API エラー: {result.get('detail', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    # JSONでない場合、レスポンステキストをチェック
                    response_text = response.text.strip()
                    if 'Notification sent' in response_text or 'sent' in response_text.lower():
                        self.logger.info("Slack通知の送信が成功しました")
                        return True
                    else:
                        self.logger.error(f"Slack API 応答が不正: {response_text}")
                        return False

            else:
                self.logger.error(f"Slack API リクエストが失敗しました (HTTP {response.status_code})")
                return False

        except requests.exceptions.Timeout:
            self.logger.error("Slack API リクエストがタイムアウトしました")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error("Slack API リクエスト中にネットワークエラーが発生しました", exception=e)
            return False
        except Exception as e:
            self.logger.error("Slack通知送信中に予期しないエラーが発生しました", exception=e)
            return False

    def _format_summary_message(self, summary_data: Dict[str, Any], is_success: bool) -> str:
        """
        サマリーメッセージをフォーマット

        Args:
            summary_data: サマリーデータ
            is_success: 成功フラグ

        Returns:
            str: フォーマット済みメッセージ
        """
        if is_success:
            success_rate = summary_data.get('success_rate', 0)
            total_posts = summary_data.get('total_posts', 0)
            successful_posts = summary_data.get('successful_posts', 0)

            message = f"X自動化ツールが正常に完了しました！\n"
            message += f"📊 成功率: {success_rate}%\n"
            message += f"📝 処理ポスト数: {successful_posts}/{total_posts}\n"

            if summary_data.get('follow_success', 0) > 0:
                message += f"👥 フォロー: {summary_data.get('follow_success', 0)}件\n"
            if summary_data.get('repost_success', 0) > 0:
                message += f"🔄 リポスト: {summary_data.get('repost_success', 0)}件\n"
            if summary_data.get('like_success', 0) > 0:
                message += f"❤️ いいね: {summary_data.get('like_success', 0)}件\n"
        else:
            message = f"X自動化ツールの実行中にエラーが発生しました。\n"
            error_message = summary_data.get('error_message', '詳細不明')
            message += f"エラー内容: {error_message}"

        return message

    def _create_summary_fields(self, summary_data: Dict[str, Any], is_success: bool) -> List[Dict[str, Any]]:
        """
        サマリーフィールドを作成

        Args:
            summary_data: サマリーデータ
            is_success: 成功フラグ

        Returns:
            List[Dict[str, Any]]: フィールドリスト
        """
        fields = []

        # 実行時刻を追加
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields.append({
            "title": "実行時刻",
            "value": current_time,
            "short": True
        })

        if is_success:
            # 成功時のフィールド
            fields.extend([
                {
                    "title": "総ポスト数",
                    "value": str(summary_data.get('total_posts', 0)),
                    "short": True
                },
                {
                    "title": "成功ポスト数",
                    "value": str(summary_data.get('successful_posts', 0)),
                    "short": True
                },
                {
                    "title": "失敗ポスト数",
                    "value": str(summary_data.get('failed_posts', 0)),
                    "short": True
                },
                {
                    "title": "成功率",
                    "value": f"{summary_data.get('success_rate', 0)}%",
                    "short": True
                }
            ])

            # アクション別成功数
            if summary_data.get('follow_success', 0) > 0:
                fields.append({
                    "title": "フォロー成功",
                    "value": str(summary_data.get('follow_success', 0)),
                    "short": True
                })

            if summary_data.get('repost_success', 0) > 0:
                fields.append({
                    "title": "リポスト成功",
                    "value": str(summary_data.get('repost_success', 0)),
                    "short": True
                })

            if summary_data.get('like_success', 0) > 0:
                fields.append({
                    "title": "いいね成功",
                    "value": str(summary_data.get('like_success', 0)),
                    "short": True
                })

        else:
            # 失敗時のフィールド
            fields.append({
                "title": "エラー詳細",
                "value": summary_data.get('error_message', '詳細不明'),
                "short": False
            })

        return fields

    def send_simple_message(self, message: str, message_type: str = "info") -> bool:
        """
        シンプルなメッセージを送信

        Args:
            message: メッセージ
            message_type: メッセージタイプ

        Returns:
            bool: 送信成功/失敗
        """
        return self.send_notification(message=message, message_type=message_type)

    def test_connection(self) -> bool:
        """
        Slack API接続テスト

        Returns:
            bool: 接続成功/失敗
        """
        test_message = "X自動化ツール - Slack通知テスト"
        return self.send_simple_message(test_message, "info")

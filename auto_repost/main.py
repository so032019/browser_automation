#!/usr/bin/env python3
"""
X自動化ツール - メインエントリーポイント
PlaywrightベースのX自動化ツール
"""

import asyncio
import argparse
import sys
import random
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.automation.browser_manager import BrowserManager
from src.automation.login_handler import LoginHandler
from src.automation.search_handler import SearchHandler
from src.automation.action_handler import ActionHandler
from src.utils.config import Config
from src.utils.logger import Logger
from src.utils.slack_notifier import SlackNotifier


def _log_execution_summary(logger: Logger, summary: dict):
    """実行サマリーをログ出力"""
    logger.info("=" * 50)
    logger.info("実行サマリー")
    logger.info("=" * 50)
    logger.info(f"総ポスト数: {summary['total_posts']}")
    logger.info(f"処理成功ポスト数: {summary['processed_posts']}")
    logger.info(f"フォロー成功数: {summary['successful_follows']}")
    logger.info(f"リポスト成功数: {summary['successful_reposts']}")
    logger.info(f"いいね成功数: {summary['successful_likes']}")
    logger.info(f"処理失敗ポスト数: {summary['failed_posts']}")

    if summary['errors']:
        logger.info("エラー詳細:")
        for error in summary['errors'][:5]:  # 最初の5件のみ表示
            logger.info(f"  - {error}")
        if len(summary['errors']) > 5:
            logger.info(f"  ... 他 {len(summary['errors']) - 5} 件のエラー")

    success_rate = (summary['processed_posts'] / summary['total_posts'] * 100) if summary['total_posts'] > 0 else 0
    logger.info(f"成功率: {success_rate:.1f}%")
    logger.info("=" * 50)


async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='X自動化ツール')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')
    parser.add_argument('--max-posts', type=int, default=10, help='最大処理ポスト数')
    parser.add_argument('--debug', action='store_true', help='デバッグモード')
    parser.add_argument('--skip-slack', action='store_true', help='Slack通知をスキップ')

    args = parser.parse_args()

    # 設定とログの初期化
    config = Config.from_env()
    config.headless = args.headless
    config.max_posts_per_session = args.max_posts

    logger = Logger(debug=args.debug, log_dir=config.log_dir)
    logger.info("X自動化ツール開始")
    logger.info(f"ログ出力先: {config.log_dir}")

    # Slack通知の初期化
    slack_notifier = None
    if not args.skip_slack:
        try:
            slack_notifier = SlackNotifier(
                api_url=config.slack_api_url,
                api_key=config.slack_api_key,
                workspace=config.slack_workspace
            )
            logger.info("Slack通知が有効です")
        except Exception as e:
            logger.warning(f"Slack通知の初期化に失敗しました: {e}")
            slack_notifier = None
    else:
        logger.info("Slack通知はスキップされます")

    browser_manager = None
    try:
        # ブラウザ管理の初期化
        browser_manager = BrowserManager(
            headless=config.headless,
            stealth=config.stealth_mode,
            browser_path=config.browser_path
        )
        browser = await browser_manager.launch_browser()
        context = await browser_manager.create_context()
        page = await context.new_page()

        # 各ハンドラーの初期化
        login_handler = LoginHandler(page, config)
        search_handler = SearchHandler(page)
        action_handler = ActionHandler(page, config)  # configを渡してBAN対策機能を有効化

        # 1. ログイン処理
        logger.info("ログイン処理開始")
        login_success = await login_handler.login(config.username, config.password)
        if not login_success:
            logger.error("ログインに失敗しました")
            return False

        # 2. 検索処理
        logger.info("検索処理開始")
        search_query = search_handler.generate_search_query()
        search_success = await search_handler.perform_search(search_query)
        if not search_success:
            logger.error("検索に失敗しました")
            return False

        # 3. URL収集（スクロール付き）
        logger.info("ポストURL収集開始")
        post_urls = await search_handler.extract_post_urls_with_scroll(config.max_posts_per_session)
        logger.info(f"{len(post_urls)}個のポストURLを収集しました")

        # 4. 各ポストでアクション実行
        results_summary = {
            'total_posts': len(post_urls),
            'processed_posts': 0,
            'successful_follows': 0,
            'successful_reposts': 0,
            'successful_likes': 0,
            'failed_posts': 0,
            'errors': []
        }

        for i, url in enumerate(post_urls, 1):
            logger.info(f"ポスト {i}/{len(post_urls)} 処理中: {url}")

            try:
                # ポスト間遅延（30秒以内）
                if i > 1:  # 最初のポスト以外
                    inter_post_delay = random.uniform(10.0, 30.0)  # 10-30秒の遅延
                    logger.info(f"ポスト間遅延: {inter_post_delay:.1f}秒")
                    await asyncio.sleep(inter_post_delay)

                # 全アクションを実行
                action_results = await action_handler.perform_all_actions(url)

                # 結果を集計
                if action_results['navigation']:
                    results_summary['processed_posts'] += 1

                    if action_results['follow']:
                        results_summary['successful_follows'] += 1

                    if action_results['repost']:
                        results_summary['successful_reposts'] += 1

                    if action_results['like']:
                        results_summary['successful_likes'] += 1
                else:
                    results_summary['failed_posts'] += 1
                    results_summary['errors'].append(f"Navigation failed: {url}")

                # 遅延
                await action_handler.random_delay()

            except Exception as e:
                results_summary['failed_posts'] += 1
                results_summary['errors'].append(f"Error processing {url}: {str(e)}")
                logger.error(f"ポスト処理中にエラー: {url}", exception=e)

        # 実行サマリーを出力
        _log_execution_summary(logger, results_summary)

        # Slack通知を送信（成功時）
        if slack_notifier:
            success_rate = (results_summary['processed_posts'] / results_summary['total_posts'] * 100) if results_summary['total_posts'] > 0 else 0
            slack_summary = {
                'total_posts': results_summary['total_posts'],
                'successful_posts': results_summary['processed_posts'],
                'failed_posts': results_summary['failed_posts'],
                'follow_success': results_summary['successful_follows'],
                'repost_success': results_summary['successful_reposts'],
                'like_success': results_summary['successful_likes'],
                'success_rate': round(success_rate, 1)
            }
            slack_notifier.send_execution_summary(slack_summary, is_success=True)

        return True

    except Exception as e:
        logger.error(f"実行中にエラーが発生しました: {e}")

        # Slack通知を送信（失敗時）
        if slack_notifier:
            error_summary = {
                'error_message': str(e)
            }
            slack_notifier.send_execution_summary(error_summary, is_success=False)

        return False
    finally:
        if browser_manager:
            await browser_manager.close()
        logger.info("X自動化ツール終了")


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

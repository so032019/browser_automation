#!/usr/bin/env python3
"""
カスタムブラウザ使用例 🚀
Braveブラウザやその他のChromiumベースブラウザを使用する方法
"""

import asyncio
import os
import sys

# パスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.automation.browser_manager import BrowserManager
from src.utils.logger import Logger


async def test_brave_browser():
    """Braveブラウザを使用したテスト"""
    logger = Logger()

    # Braveブラウザのパスを確認
    brave_paths = [
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
        "/opt/brave.com/brave/brave-browser",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"  # macOS
    ]

    brave_path = None
    for path in brave_paths:
        if os.path.exists(path):
            brave_path = path
            break

    if not brave_path:
        logger.error("Braveブラウザが見つかりません 😢")
        logger.info("利用可能なパス:")
        for path in brave_paths:
            logger.info(f"  - {path}")
        return

    logger.info(f"Braveブラウザを使用します: {brave_path} ✨")

    # カスタムブラウザでBrowserManagerを初期化
    browser_manager = BrowserManager(
        headless=False,  # ヘッドレスモードを無効にして動作確認
        stealth=True,
        browser_path=brave_path
    )

    try:
        # ブラウザ起動
        await browser_manager.launch_browser()
        await browser_manager.create_context()

        # 新しいページを作成
        page = await browser_manager.get_new_page()

        # テストページに移動
        await page.goto("https://whatismybrowser.com/")
        await page.wait_for_load_state("networkidle")

        # ブラウザ情報を取得
        browser_info = await page.evaluate("""
            () => {
                return {
                    userAgent: navigator.userAgent,
                    vendor: navigator.vendor,
                    platform: navigator.platform,
                    cookieEnabled: navigator.cookieEnabled,
                    language: navigator.language,
                    onLine: navigator.onLine
                };
            }
        """)

        logger.info("ブラウザ情報:")
        for key, value in browser_info.items():
            logger.info(f"  {key}: {value}")

        # スクリーンショットを撮影
        await page.screenshot(path="brave_browser_test.png")
        logger.info("スクリーンショットを保存しました: brave_browser_test.png 📸")

        # 少し待機
        await asyncio.sleep(3)

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")

    finally:
        await browser_manager.close()


async def test_custom_features():
    """カスタム機能のテスト（JavaScript注入など）"""
    logger = Logger()

    browser_manager = BrowserManager(headless=False, stealth=True)

    try:
        await browser_manager.launch_browser()
        context = await browser_manager.create_context()

        # カスタム機能を注入
        await context.add_init_script("""
            // カスタム広告ブロック機能
            const blockAds = () => {
                console.log('🚫 広告ブロック機能が動作中...');

                // 広告関連の要素を非表示
                const adSelectors = [
                    '[data-testid="placementTracking"]',
                    '.promoted-tweet',
                    '[aria-label*="広告"]',
                    '[aria-label*="Promoted"]'
                ];

                let blockedCount = 0;
                adSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        el.style.display = 'none';
                        blockedCount++;
                    });
                });

                if (blockedCount > 0) {
                    console.log(`✅ ${blockedCount}個の広告要素をブロックしました`);
                }
            };

            // ページ読み込み時に実行
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', blockAds);
            } else {
                blockAds();
            }

            // DOM変更を監視
            const observer = new MutationObserver(blockAds);
            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true
            });

            // カスタムコンソールメッセージ
            console.log('🎉 カスタム機能が読み込まれました！');
        """)

        page = await context.new_page()

        # コンソールログを監視
        page.on("console", lambda msg: logger.info(f"Console: {msg.text}"))

        # テストページに移動
        await page.goto("https://twitter.com")
        await page.wait_for_load_state("networkidle")

        logger.info("カスタム機能のテストが完了しました ✨")

        # 少し待機してコンソールログを確認
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")

    finally:
        await browser_manager.close()


async def main():
    """メイン関数"""
    print("🚀 カスタムブラウザテストを開始します！")
    print()

    print("1. Braveブラウザのテスト...")
    await test_brave_browser()
    print()

    print("2. カスタム機能のテスト...")
    await test_custom_features()
    print()

    print("✅ すべてのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
